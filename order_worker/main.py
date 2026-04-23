import os
import json
import mysql.connector
import psycopg2
import pika
import time
from datetime import datetime

# === MYSQL CONNECTION ===
def get_mysql_connection(max_retries=5):
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
            wait_time = 2 ** attempt
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
def get_rabbitmq_connection():
    """Kết nối RabbitMQ"""
    while True:
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
            return connection
        except Exception as e:
            print(f"[WARN] RabbitMQ chưa sẵn sàng: {e}. Thử lại sau 5s...")
            time.sleep(5)

# === MESSAGE PROCESSOR ===
def process_order(order_data):
    """Xử lý order: update inventory & sync to PostgreSQL"""
    try:
        order_id = order_data['order_id']
        product_id = order_data['product_id']
        quantity = order_data['quantity']
        user_id = order_data['user_id']
        total_price = order_data.get('total_price', 0)
        
        # Simulate payment processing
        time.sleep(1)
        
        mysql_db = get_mysql_connection()
        mysql_cursor = mysql_db.cursor(dictionary=True)

        # Check inventory (already done in Order API, but double-check)
        mysql_cursor.execute("SELECT stock FROM products WHERE id = %s", (product_id,))
        product = mysql_cursor.fetchone()

        if not product or product['stock'] < quantity:
            # Inventory không đủ
            mysql_cursor.execute(
                "UPDATE orders SET status = 'FAILED' WHERE id = %s",
                (order_id,)
            )
            mysql_db.commit()
            print(f"[FAIL] Order {order_id}: Insufficient stock")
            mysql_cursor.close()
            mysql_db.close()
            return False

        # Update inventory in MySQL
        mysql_cursor.execute(
            "UPDATE products SET stock = stock - %s WHERE id = %s",
            (quantity, product_id)
        )
        
        # Update order status to SYNCED in MySQL
        mysql_cursor.execute(
            "UPDATE orders SET status = 'SYNCED' WHERE id = %s",
            (order_id,)
        )
        mysql_db.commit()
        print(f"[SUCCESS] Order {order_id}: MySQL updated")

        # Insert to PostgreSQL Finance system
        postgres_db = get_postgres_connection()
        if postgres_db:
            postgres_cursor = postgres_db.cursor()
            try:
                postgres_cursor.execute(
                    "INSERT INTO payments (order_id, user_id, amount, status) VALUES (%s, %s, %s, 'COMPLETED')",
                    (order_id, user_id, total_price)
                )
                postgres_db.commit()
                print(f"[SUCCESS] Order {order_id}: Payment recorded in PostgreSQL")
            except Exception as e:
                print(f"[WARN] PostgreSQL insert failed: {e}")
            finally:
                postgres_cursor.close()
                postgres_db.close()

        mysql_cursor.close()
        mysql_db.close()
        return True

    except Exception as e:
        print(f"[ERROR] Processing order failed: {e}")
        return False

# === CONSUMER ===
def consume_messages():
    """Lắng nghe RabbitMQ queue"""
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue='order_queue', durable=True)
    
    print("[INFO] Order Worker started. Waiting for messages...")

    def callback(ch, method, properties, body):
        try:
            order_data = json.loads(body.decode())
            print(f"[RECEIVED] Order #{order_data['order_id']}: user={order_data['user_id']}, product={order_data['product_id']}, qty={order_data['quantity']}")
            
            if process_order(order_data):
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"[ACK] Order #{order_data['order_id']} processed successfully")
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                print(f"[NACK] Order #{order_data['order_id']} requeued")
        except Exception as e:
            print(f"[ERROR] Callback error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='order_queue', on_message_callback=callback)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()
        print("[INFO] Worker stopped")

# === MAIN ===
if __name__ == "__main__":
    print("[INFO] Initializing Order Worker...")
    consume_messages()

