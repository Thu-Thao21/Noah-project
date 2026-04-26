# HƯỚNG DẪN SETUP VÀ CHẠY HỆ THỐNG NOAH

## 1. YÊU CẦU HỆ THỐNG

- **Docker & Docker Compose**: Phải cài đặt Docker Desktop
- **Python 3.10+**: Để chạy local (không bắt buộc nếu dùng Docker)
- **Git**: Để clone repository

## 2. CẤU TRÚC PROJECT

```
Noah-project/
├── order_api/                 # REST API service
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── order_worker/              # RabbitMQ consumer service
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── legacy_adapter/            # CSV importer service
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/                 # React frontend
│   ├── package.json
│   └── src/
├── docker-compose.yml         # Orchestration file
├── init.sql                   # MySQL initialization
├── postgres_init.sql          # PostgreSQL initialization
├── kong.yml                   # Kong API Gateway config
├── requirements.txt           # Python dependencies
└── .gitignore                 # Git ignore file
```

## 3. SETUP BAN ĐẦU (Chỉ lần đầu)

### 3.1 Nếu bạn vừa clone từ Git

```bash
# Tạo virtual environment
python -m venv .venv

# Activate venv (Windows)
.venv\Scripts\activate

# Activate venv (Mac/Linux)
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Hoặc cài từng service
pip install -r order_api/requirements.txt
pip install -r order_worker/requirements.txt
pip install -r legacy_adapter/requirements.txt
```

### 3.2 Start tất cả các services bằng Docker

```bash
# Build và start containers
docker-compose up -d --build

# Kiểm tra status
docker-compose ps

# Xem logs
docker-compose logs -f

# Stop all
docker-compose down
```

## 4. CHẠY TỪNG SERVICE (Nếu không dùng Docker)

### 4.1 MySQL
```bash
# Docker
docker run -d \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=noah_sales \
  -v mysql_data:/var/lib/mysql \
  -p 3306:3306 \
  mysql:8.0
```

### 4.2 PostgreSQL
```bash
docker run -d \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=noah_finance \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15
```

### 4.3 Redis
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 4.4 RabbitMQ
```bash
docker run -d \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```

### 4.5 Legacy Adapter
```bash
cd legacy_adapter
python main.py
```

### 4.6 Order API
```bash
cd order_api
python main.py
```

### 4.7 Order Worker
```bash
cd order_worker
python main.py
```

### 4.8 Dashboard (React)
```bash
cd dashboard
npm install
npm run dev
```

## 5. API ENDPOINTS

### Pagination
```bash
GET http://localhost:8000/orders?page=1&limit=50
```

### Data Stitching (MySQL + PostgreSQL)
```bash
GET http://localhost:8000/report
```

### Create Order (Anti-overselling)
```bash
POST http://localhost:8000/orders
Content-Type: application/json

{
  "user_id": 101,
  "product_id": 1,
  "quantity": 5
}
```

### Dashboard
```
http://localhost:3000
```

## 6. KIỂM TRA DỮ LIỆU

### MySQL
```bash
docker exec -it noah_mysql mysql -u root -proot noah_sales
mysql> SELECT COUNT(*) FROM orders;
mysql> SELECT COUNT(*) FROM products;
```

### PostgreSQL
```bash
docker exec -it noah_postgres psql -U postgres -d noah_finance
postgres=# SELECT COUNT(*) FROM payments;
```

### Redis
```bash
docker exec -it noah_redis redis-cli
redis> GET product:1:stock
```

## 7. TROUBLESHOOTING

### Port bị chiếm
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -i :8000
kill -9 <PID>
```

### Containers không start
```bash
# Xóa containers cũ
docker-compose down -v

# Rebuild
docker-compose up -d --build
```

### Redis connection error
```bash
# Kiểm tra Redis running
docker ps | grep redis

# Restart
docker-compose restart redis
```

## 8. CÁCH NỘP BÀI

**KO NỘP:**
- `.venv/` folder (virtual environment)
- `__pycache__/` folders
- `node_modules/` folder
- `.env` file (nếu có sensitive data)
- `*.pyc` files
- `*.docx`, `*.pdf` files (nếu không yêu cầu)

**CÓ NỘP:**
- `requirements.txt` (để teacher cài dependencies)
- `package.json` (cho dashboard)
- `docker-compose.yml`
- `Dockerfile` (cho từng service)
- `.gitignore`
- Tất cả source code (*.py, *.js)
- Database init files (`init.sql`, `postgres_init.sql`)

### Cách loại trừ .venv khi nộp
```bash
# Nếu dùng Git
git status  # Kiểm tra .venv không được track (phải có trong .gitignore)

# Nếu nộp folder trực tiếp
# Xóa .venv folder trước khi ZIP
rm -r .venv

# Hoặc dùng command để tạo archive mà không gồm .venv
tar --exclude='.venv' --exclude='__pycache__' --exclude='node_modules' \
    -czf Noah-project.tar.gz Noah-project/

# Windows (PowerShell)
Compress-Archive -Path Noah-project -DestinationPath Noah-project.zip `
  -Exclude '.venv', '__pycache__', 'node_modules', '*.pyc'
```

## 9. TÓMLẠI - BƯỚC NỘP NHANH

1. **Xóa .venv**
   ```bash
   rm -r .venv
   ```

2. **Kiểm tra .gitignore**
   - `.venv/` ✓
   - `__pycache__/` ✓
   - `node_modules/` ✓

3. **Giữ lại**
   - `requirements.txt` ✓
   - `docker-compose.yml` ✓
   - Tất cả `*.py` files ✓
   - Tất cả `Dockerfile` ✓

4. **Nộp (3 cách)**
   - Push lên Git (teacher clone)
   - Upload ZIP folder
   - Gửi tar.gz file

## 10. LIÊN HỆ & HỖ TỢ

Nếu có vấn đề, hãy:
1. Kiểm tra Docker running: `docker ps`
2. Xem logs: `docker-compose logs service_name`
3. Kiểm tra ports: `netstat -an | grep :XXXX`

---

**Generated: April 26, 2026**
