import os
import json
import mysql.connector
import psycopg2
import pika
import redis
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import time
from datetime import datetime
from decimal import Decimal

# === CUSTOM JSON ENCODER ===
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# === REDIS CONNECTION ===
def get_redis_connection():
    """Kết nối Redis"""
    try:
        return redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
    except Exception as e:
        print(f"[WARN] Redis connection failed: {e}")
        return None

# === DATABASE CONNECTION WITH RETRY ===
def get_db_connection(max_retries=5):
    """Kết nối MySQL với retry logic exponential backoff"""
    for attempt in range(max_retries):
        try:
            return mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "mysql"),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", "root"),
                database=os.getenv("MYSQL_DATABASE", "noah_sales")
            )
        except mysql.connector.Error as e:
            wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
            print(f"[WARN] MySQL connection failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"[INFO] Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise Exception("Failed to connect to MySQL after 5 attempts")

# === POSTGRESQL CONNECTION ===
def get_postgres_connection():
    """Kết nối PostgreSQL"""
    try:
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "root"),
            database=os.getenv("POSTGRES_DATABASE", "noah_finance")
        )
    except Exception as e:
        print(f"[WARN] PostgreSQL connection failed: {e}")
        return None

# === RABBITMQ CONNECTION ===
def get_rabbitmq_channel():
    """Kết nối RabbitMQ và tạo queue"""
    try:
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='order_queue', durable=True)
        return channel
    except Exception as e:
        print(f"[ERROR] RabbitMQ connection failed: {e}")
        return None

# === HTTP REQUEST HANDLER ===
class OrderAPIHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """GET /orders hoặc GET /report"""
        parsed_path = urlparse(self.path)
        
        # GET /orders?page=1&limit=50
        if parsed_path.path == '/orders':
            self._handle_get_orders()
        # GET /report
        elif parsed_path.path == '/report':
            self._handle_get_report()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _handle_get_orders(self):
        """GET /orders - Lấy danh sách đơn hàng có pagination"""
        try:
            # Parse query parameters
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            page = int(query_params.get('page', ['1'])[0])
            limit = int(query_params.get('limit', ['50'])[0])
            
            # Validate pagination
            page = max(1, page)
            limit = min(100, max(1, limit))
            offset = (page - 1) * limit
            
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM orders")
            total = cursor.fetchone()['total']
            
            # Get paginated data
            cursor.execute(f"SELECT * FROM orders LIMIT {limit} OFFSET {offset}")
            orders = cursor.fetchall()
            
            # Convert datetime to string and Decimal to float
            for order in orders:
                if hasattr(order.get('created_at'), 'isoformat'):
                    order['created_at'] = order['created_at'].isoformat()
                for key, value in order.items():
                    if isinstance(value, Decimal):
                        order[key] = float(value)
            
            total_pages = (total + limit - 1) // limit
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "data": orders,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": total_pages
                }
            }, cls=DecimalEncoder).encode())
            
            cursor.close()
            db.close()
        except Exception as e:
            print(f"[ERROR] GET /orders failed: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}, cls=DecimalEncoder).encode())
    
    def _handle_get_report(self):
        """GET /report - Data Stitching (MySQL + PostgreSQL)"""
        try:
            # MySQL: Get orders
            mysql_db = get_db_connection()
            mysql_cursor = mysql_db.cursor(dictionary=True)
            mysql_cursor.execute("SELECT id, user_id, product_id, quantity, total_price, status FROM orders")
            orders = mysql_cursor.fetchall()
            mysql_cursor.close()
            mysql_db.close()
            
            # PostgreSQL: Get payments
            postgres_db = get_postgres_connection()
            if postgres_db:
                postgres_cursor = postgres_db.cursor()
                postgres_cursor.execute("SELECT order_id, user_id, amount, status FROM payments LIMIT 1000")
                payments = postgres_cursor.fetchall()
                postgres_cursor.close()
                postgres_db.close()
            else:
                payments = []
            
            # Data Stitching: Calculate metrics
            total_revenue = 0
            completed_orders = 0
            failed_orders = 0
            
            # Build order_id -> status mapping
            order_status_map = {o['id']: o['status'] for o in orders}
            
            # Calculate from payments
            for payment in payments:
                if payment[3] == 'COMPLETED':  # payment status
                    total_revenue += payment[2]  # amount
            
            # Calculate from orders
            completed_orders = len([o for o in orders if o['status'] == 'COMPLETED'])
            failed_orders = len([o for o in orders if o['status'] == 'FAILED'])
            
            error_rate = (failed_orders / len(orders) * 100) if orders else 0
            
            # Top products
            top_products = {}
            for order in orders:
                if order['status'] == 'COMPLETED':
                    product_id = order['product_id']
                    qty = order['quantity']
                    top_products[product_id] = top_products.get(product_id, 0) + qty
            
            top_products_list = sorted(
                [{"product_id": k, "quantity": v} for k, v in top_products.items()],
                key=lambda x: x['quantity'],
                reverse=True
            )[:5]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "total_revenue": float(total_revenue) if isinstance(total_revenue, Decimal) else total_revenue,
                "orders_completed": completed_orders,
                "orders_failed": failed_orders,
                "error_rate": f"{error_rate:.2f}%",
                "top_products": top_products_list,
                "data_sources": ["MySQL (orders)", "PostgreSQL (payments)"],
                "timestamp": datetime.now().isoformat()
            }, cls=DecimalEncoder).encode())
            
        except Exception as e:
            print(f"[ERROR] GET /report failed: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}, cls=DecimalEncoder).encode())

    def do_POST(self):
        """POST /orders - Tạo đơn hàng mới với Redis anti-overselling"""
        if self.path == '/orders':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                order_data = json.loads(body.decode())

                # Validate data
                if not all(k in order_data for k in ['user_id', 'product_id', 'quantity']):
                    raise ValueError("Missing required fields: user_id, product_id, quantity")
                
                quantity = int(order_data['quantity'])
                if quantity <= 0:
                    raise ValueError("Quantity must be greater than 0")
                
                product_id = order_data['product_id']
                user_id = order_data['user_id']

                # === ANTI-OVERSELLING CHECK (REDIS) ===
                redis_conn = get_redis_connection()
                if redis_conn:
                    stock_key = f"product:{product_id}:stock"
                    remaining = redis_conn.decrby(stock_key, quantity)
                    
                    if remaining < 0:
                        # Revert the decrement
                        redis_conn.incrby(stock_key, quantity)
                        print(f"[INFO] Out of stock for product {product_id}")
                        self.send_response(400)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": False,
                            "error": "Out of stock"
                        }, cls=DecimalEncoder).encode())
                        return
                    
                    print(f"[INFO] Stock check passed. Remaining: {remaining}")

                # Insert vào MySQL database
                db = get_db_connection()
                cursor = db.cursor()
                
                # Get product price
                cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Product {product_id} not found")
                
                price = result[0]
                total_price = price * quantity
                
                cursor.execute(
                    "INSERT INTO orders (user_id, product_id, quantity, total_price, status) VALUES (%s, %s, %s, %s, 'PENDING')",
                    (user_id, product_id, quantity, total_price)
                )
                db.commit()
                order_id = cursor.lastrowid

                print(f"[INFO] Order #{order_id} created: user={user_id}, product={product_id}, qty={quantity}")

                # Publish to RabbitMQ
                channel = get_rabbitmq_channel()
                if channel:
                    message = json.dumps({
                        "order_id": order_id,
                        "user_id": user_id,
                        "product_id": product_id,
                        "quantity": quantity,
                        "total_price": float(total_price) if isinstance(total_price, Decimal) else total_price
                    }, cls=DecimalEncoder)
                    channel.basic_publish(
                        exchange='',
                        routing_key='order_queue',
                        body=message,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    channel.connection.close()
                    print(f"[INFO] Message published to RabbitMQ for order #{order_id}")

                self.send_response(201)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "order_id": order_id,
                    "total_price": float(total_price) if isinstance(total_price, Decimal) else total_price
                }, cls=DecimalEncoder).encode())

                cursor.close()
                db.close()
            except Exception as e:
                print(f"[ERROR] POST /orders failed: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}, cls=DecimalEncoder).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()

    def log_message(self, format, *args):
        """Log messages"""
        print(f"[HTTP] {format % args}")

# === MAIN ===
if __name__ == "__main__":
    print("[INFO] Order API starting on port 8000...")
    server = HTTPServer(('0.0.0.0', 8000), OrderAPIHandler)
    print("[INFO] Server ready. Listening on http://0.0.0.0:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[INFO] Server stopped")
        server.server_close()
