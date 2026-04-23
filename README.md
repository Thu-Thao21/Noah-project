# 🚀 NOAH - Microservices E-commerce Platform

Hệ thống bán lẻ điện tử với kiến trúc microservices sử dụng Docker.

## 📋 Kiến Trúc Hệ Thống

### 📊 Tầng Dữ Liệu (Data Layer)
- **MySQL** (port 3306) - `noah_sales` database cho kho hàng & đơn hàng
- **PostgreSQL** (port 5432) - `noah_finance` database cho tài chính

### 🔧 Trung Gian (Middleware)
- **RabbitMQ** (port 5672, Dashboard: 15672) - Message queue xử lý async
- **Kong Gateway** (port 8000) - API Gateway bảo vệ & route request

### 🎯 Microservices
| Service | Port | Chức năng |
|---------|------|----------|
| **legacy-adapter** | - | Xử lý CSV inventory, cập nhật MySQL |
| **order-api** | 8001 | REST API tạo & lấy đơn hàng |
| **order-worker** | - | Worker xử lý queue đơn hàng |
| **dashboard** | 3000 | React UI quản lý |

## 📁 Cấu Trúc Folder

```
d:\Noah-project\
├── docker-compose.yml        # Orchestration
├── init.sql                   # SQL init script
├── kong.yml                   # Kong Gateway config
├── shared_data/
│   ├── input/                 # Upload CSV inventory
│   └── processed/             # Processed CSV backup
├── legacy_adapter/            # CSV processor
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── order_api/                 # REST API
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── order_worker/              # Message processor
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
└── dashboard/                 # React frontend
    ├── package.json
    ├── Dockerfile
    ├── vite.config.js
    └── src/
```

## 🚀 Hướng Dẫn Chạy

### 1. Build & Start tất cả services
```bash
cd d:\Noah-project
docker-compose up --build
```

### 2. Kiểm tra các service

**Frontend Dashboard:**
```
http://localhost:3000
```

**Order API:**
```bash
# Lấy danh sách đơn hàng
curl http://localhost:8001/orders

# Tạo đơn hàng mới
curl -X POST http://localhost:8001/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 100, "quantity": 5}'
```

**RabbitMQ Dashboard:**
```
http://localhost:15672
# Username: guest
# Password: guest
```

**MySQL:**
```bash
mysql -h localhost -u root -p
# Password: root
# Database: noah_sales
```

## 🔄 Quy Trình Hoạt Động

1. **Frontend (Dashboard)** gửi request tạo order
2. **Order API** nhận, validate, insert vào MySQL
3. **Order API** publish message to RabbitMQ queue
4. **Order Worker** consume message từ queue
5. **Order Worker** check inventory, update stock, update order status
6. **Frontend** hiển thị danh sách orders

## 📝 API Endpoints

| Method | Endpoint | Mô Tả |
|--------|----------|-------|
| GET | `/orders` | Lấy danh sách 50 đơn hàng gần nhất |
| POST | `/orders` | Tạo đơn hàng mới |

**Request Body (POST /orders):**
```json
{
  "user_id": 1,
  "product_id": 100,
  "quantity": 5
}
```

**Response:**
```json
{
  "success": true,
  "order_id": 1
}
```

## 🔧 Troubleshooting

### Lỗi MySQL connection refused
```bash
# Check MySQL container
docker logs mysql_db

# Chờ ~30s MySQL khởi động
```

### RabbitMQ connection failed
```bash
# Check RabbitMQ logs
docker logs rabbitmq_server

# Verify credentials: guest/guest
```

### Frontend không kết nối API
- Check `VITE_API_BASE_URL` environment variable
- Verify order-api container đang chạy: `docker ps`

## 📊 Database Schema

### products table
```sql
CREATE TABLE products (
  id INT PRIMARY KEY,
  name VARCHAR(255),
  price DECIMAL(10,2),
  stock INT DEFAULT 0
);
```

### orders table
```sql
CREATE TABLE orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  product_id INT,
  quantity INT,
  total_price DECIMAL(10,2),
  status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, COMPLETED, FAILED
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 💡 Tips

- **Thêm sản phẩm:** Thêm vào init.sql
- **Dọn dẹp:** `docker-compose down -v` (xóa volumes)
- **Rebuild:** `docker-compose up --build --force-recreate`
- **Logs:** `docker-compose logs -f [service_name]`

---

**Created:** April 19, 2026  
**Status:** Ready for development ✅
