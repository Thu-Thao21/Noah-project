import os, time, shutil, csv, mysql.connector, redis
from datetime import datetime

# Redis Connection for Stock Sync
def get_redis_connection():
    """Kết nối Redis"""
    try:
        return redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
    except Exception as e:
        print(f"[WARN] Redis connection failed: {e}")
        return None

# Thử thách Retry Connection [cite: 215]
def get_db_connection(max_retries=5):
    """MySQL connection với exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "mysql"), # Tên service trong docker-compose
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
                raise Exception("Failed to connect after 5 attempts")

def process_csv():
    input_file = "/app/input/inventory.csv"
    if not os.path.exists(input_file): 
        return

    db = get_db_connection()
    cursor = db.cursor()
    redis_conn = get_redis_connection()
    
    with open(input_file, mode='r') as f:
        reader = csv.DictReader(f)
        processed, skipped = 0, 0
        for row in reader:
            try:
                p_id, qty = int(row['product_id']), int(row['quantity'])
                
                # === OUTLIER DETECTION (Group 5: OUTLIERS Strategy) ===
                # Bỏ qua nếu quantity < 0 (Negative outlier)
                if qty < 0: 
                    print(f"[WARN] Skipped row: {row} - Reason: Negative stock (OUTLIER)")
                    skipped += 1
                    continue
                
                # Bỏ qua nếu quantity > 1,000,000 (Extreme outlier)
                if qty > 1000000:
                    print(f"[WARN] Skipped row: {row} - Reason: Quantity too large (OUTLIER)")
                    skipped += 1
                    continue
                
                # UPDATE MySQL
                cursor.execute("UPDATE products SET stock = %s WHERE id = %s", (qty, p_id))
                
                # SYNC to Redis (Anti-overselling cache)
                if redis_conn:
                    stock_key = f"product:{p_id}:stock"
                    redis_conn.set(stock_key, qty)
                    print(f"[INFO] Synced to Redis: {stock_key} = {qty}")
                
                processed += 1
            except (ValueError, KeyError) as e:
                print(f"[WARN] Skipped row: {row} - Reason: {e}")
                skipped += 1
            except Exception as e:
                print(f"[ERROR] Processing error: {e}")
                skipped += 1
    
    db.commit()
    db.close()

    # Dọn dẹp: Di chuyển file kèm timestamp [cite: 39, 42]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        shutil.move(input_file, f"/app/processed/inventory_{timestamp}.csv")
        print(f"[INFO] File processed. Processed: {processed}, Skipped: {skipped}")
    except Exception as e:
        print(f"[ERROR] Failed to move file: {e}")

if __name__ == "__main__":
    print("[INFO] Legacy Adapter starting... Polling /app/input/ every 10s")
    while True:
        try:
            process_csv()
        except Exception as e:
            print(f"[ERROR] process_csv failed: {e}")
            time.sleep(5)
        time.sleep(10) # Polling 10 giây/lần [cite: 33]