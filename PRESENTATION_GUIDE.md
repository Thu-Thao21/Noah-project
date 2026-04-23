# 🎯 NOAH Retail Project - HƯỚNG DẪN TRÌNH BÀY

**Dự án:** NOAH - Microservices E-commerce Platform  
**Loại:** Group Project - Microservices Architecture  
**Thời gian trình bày:** 15-20 phút  
**Ngôn ngữ:** Tiếng Việt  
**Ngày trình bày:** April 23, 2026

---

## 📋 OUTLINE TRÌNH BÀY (Slide Structure)

### **PHẦN 1: GIỚI THIỆU (2 phút)**

**Slide 1: Title Slide**
```
NOAH RETAIL UNIFIED COMMERCE
Microservices E-commerce Platform

Team: [Tên thành viên]
Date: April 23, 2026
```

**Talking Points:**
- Đây là dự án thực tế một hệ thống bán lẻ điện tử hiện đại
- Sử dụng microservices architecture - kiến trúc mà các công ty lớn như Amazon, Netflix, Uber đang dùng
- Giải quyết các bài toán thực tế: Xử lý đơn hàng, quản lý kho, bảo mật, performance

---

### **PHẦN 2: VẤN ĐỀ & GIẢI PHÁP (3 phút)**

**Slide 2: Các Thách Thức**
```
❌ Thách Thức:
1. Xử lý 20,000+ đơn hàng → Cần pagination
2. Tránh tình trạng overselling (bán quá số lượng hàng)
3. Hệ thống phải xử lý async (không block)
4. Dữ liệu từ nhiều database (MySQL + PostgreSQL)
5. Bảo mật API (Authentication & Rate Limiting)
6. Xử lý dữ liệu từ legacy system (CSV files)
```

**Talking Points:**
- Khi có 20,000 đơn hàng, tải toàn bộ memory sẽ crash → Cần pagination
- Overselling: Khách hàng 1 mua 10 cái hàng, khách hàng 2 mua 5 cái, nhưng chỉ có 10 cái → Redis cache giải quyết
- Xử lý đơn hàng mất thời gian (payment, inventory update) → RabbitMQ queue giải quyết
- Data stitching: Đơn hàng ở MySQL, thanh toán ở PostgreSQL → Cần JOIN 2 DB

---

### **PHẦN 3: KIẾN TRÚC HỆ THỐNG (4 phút)**

**Slide 3: Architecture Diagram**
```
┌─────────────────────────────────────┐
│   Frontend: React Dashboard         │ (Port 3000)
│   - Real-time pagination UI         │
│   - KPI display                     │
└────────────┬────────────────────────┘
             │
        ┌────▼───────────────┐
        │   KONG Gateway     │ (Port 8000)
        │ - Auth (X-API-Key) │
        │ - Rate Limiting    │
        └────┬───────────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
┌────────┐ ┌────────┐
│Order   │ │Report  │ (REST APIs)
│API:5000│ │API:5000│
└───┬────┘ └───┬────┘
    │          │
    └─────┬────┘
          │
    ┌─────▼──────────────┐
    │   RabbitMQ Queue   │ (Message Bus)
    │   - order_queue    │
    └──────┬─────────────┘
           │
      ┌────▼────────────────┐
      │   Order Worker      │ (Consumer)
      │   - Process async   │
      └─────────────────────┘
           │
    ┌──────┼──────┬──────────┐
    ▼      ▼      ▼          ▼
  MySQL  PostgreSQL Redis  CSV Files
  Sales  Finance   Cache  Legacy Data
```

**Talking Points (Module by Module):**

1. **Frontend (React + Vite)**
   - Dashboard hiển thị real-time orders
   - Pagination UI để duyệt 20,000 đơn hàng
   - KPI display (revenue, orders, customers)
   
2. **Kong Gateway (API Security)**
   - Tất cả request phải qua gateway
   - Authentication: X-API-Key header
   - Rate Limiting: 10 req/min cho /orders, 20 req/min cho /report
   - Chặn request không authorize
   
3. **Order API (REST Service)**
   - GET /orders: Lấy danh sách đơn hàng (pagination)
   - POST /orders: Tạo đơn hàng mới
   - GET /report: Data stitching (MySQL + PostgreSQL)
   
4. **Order Worker (Async Processing)**
   - Consume message từ RabbitMQ
   - Xử lý async (payment simulation: sleep 1s)
   - Update inventory trong MySQL
   - Insert payment record vào PostgreSQL
   
5. **Message Queue (RabbitMQ)**
   - Decoupling: API không cần chờ worker xử lý
   - Nếu worker down, message sẽ retry
   - Fault tolerance

6. **Data Layer**
   - MySQL: Orders, Products (Sales DB)
   - PostgreSQL: Payments (Finance DB)
   - Redis: Product stock cache (anti-overselling)

---

### **PHẦN 4: CORE FEATURES (5 phút)**

**Slide 4: Feature 1 - Pagination (DEMO)**

**Talking Points:**
- Problem: 20,000 đơn hàng không thể tải một lần
- Solution: LIMIT/OFFSET pagination + Frontend UI
- Backend API: `GET /orders?page=1&limit=10`
- Frontend: Next/Previous buttons, page numbers, limit selector

**LIVE DEMO #1:**
```
1. Truy cập http://localhost:3000
2. Show dashboard với bảng Orders
3. Click Next button → Trang tiếp theo
4. Click page 5 → Jump to page 5
5. Change limit 5→10 rows
→ Show: đơn hàng load từ API real-time ✅
```

---

**Slide 5: Feature 2 - Anti-Overselling with Redis**

**Talking Points:**
- Problem: Khách hàng 1 đặt 100 cái, khách hàng 2 đặt 50 cái, nhưng chỉ có 100 cái
- Atomic operation: Redis DECR command
- Race condition prevention

**LIVE DEMO #2 (Command Line):**
```powershell
# 1. Check current stock
docker exec redis_cache redis-cli GET "product:10:stock"
# Output: 100

# 2. Try create order (quantity=5)
# → API atomically DECR stock
# → Stock becomes 95

# 3. Verify
docker exec redis_cache redis-cli GET "product:10:stock"
# Output: 95 ✅
```

---

**Slide 6: Feature 3 - Async Order Processing (RabbitMQ)**

**Talking Points:**
- Problem: Order API không nên chờ payment processing
- Solution: Publish message → RabbitMQ → Worker consume
- Benefits:
  - API instant response (201 Created)
  - Worker xử lý async (payment, inventory update)
  - Retry logic nếu worker fail
  - Message persistence

**Flow Diagram:**
```
1. POST /orders
   ↓
2. API: Redis DECR stock ✓
   ↓
3. API: Insert to MySQL (PENDING) ✓
   ↓
4. API: Publish to RabbitMQ ✓
   ↓
5. Return 201 immediately ✓
   ↓
6. [Async] Worker: Sleep 1s (payment sim)
   ↓
7. [Async] Worker: Update stock in MySQL
   ↓
8. [Async] Worker: Insert to PostgreSQL payments
   ↓
9. [Async] Worker: ACK message
```

---

**Slide 7: Feature 4 - Data Stitching (Multi-DB Join)**

**Talking Points:**
- Problem: Orders ở MySQL, Payments ở PostgreSQL, cần join
- Solution: Application-level join (fetch from both, merge in code)
- Returns: Unified report KPIs

**Report Data (GET /report):**
```json
{
  "total_revenue": 245500000,      // sum(amount) from PostgreSQL
  "orders_completed": 18500,        // count from MySQL orders
  "orders_failed": 1500,            // count from MySQL orders
  "error_rate": 7.5,                // (failed/total) %
  "top_products": [                 // rank by quantity
    {product_id: 100, total_qty: 1500},
    {product_id: 101, total_qty: 1200},
    ...
  ]
}
```

**LIVE DEMO #3:**
```powershell
# Fetch report with data stitching
$resp = Invoke-WebRequest `
  -Uri "http://localhost:8001/report" `
  -UseBasicParsing

$resp.Content | ConvertFrom-Json | Format-List
# → Show total_revenue, orders_completed, error_rate
```

---

**Slide 8: Feature 5 - Legacy Data Integration (CSV Adapter)**

**Talking Points:**
- Problem: Old system có data trong CSV files
- Solution: Legacy Adapter microservice
- Workflow:
  1. CSV files → /app/input folder
  2. Adapter polls mỗi 10 giây
  3. Parse CSV, validate data
  4. Update MySQL products table
  5. Sync to Redis stock cache
  6. Move file → /app/processed folder

**Process Flow:**
```
CSV File (inventory.csv)
    ↓
Legacy Adapter (10s polling)
    ↓
Validate (qty > 0)
    ↓
✓ Update MySQL products table
    ↓
✓ Sync to Redis (anti-overselling)
    ↓
✓ Move → /app/processed folder
    ↓
Logging: [INFO] Processed 50, Skipped 2
```

---

### **PHẦN 5: CHALLENGES & SOLUTIONS (2 phút)**

**Slide 9: Technical Challenges**

| Challenge | Solution | Tech |
|-----------|----------|------|
| Connection retry | Exponential backoff (1s, 2s, 4s, 8s, 16s) | Python loop |
| Race condition (overselling) | Atomic Redis DECR | Redis atomic ops |
| Async processing | Message queue | RabbitMQ |
| Data from 2 DBs | Application-level join | Python fetch |
| Dirty data (CSV) | Validate + skip invalid rows | CSV parsing |
| API rate limit | Kong Gateway rate limiter | Kong plugin |
| Authentication | API Key in X-API-Key header | Kong auth |

---

### **PHẦN 6: RESULTS & METRICS (2 phút)**

**Slide 10: Project Status**

```
✅ INFRASTRUCTURE (7/7)        100%
   - Docker Compose: 9 containers
   - MySQL 8.0: noah_sales
   - PostgreSQL 15: noah_finance
   - RabbitMQ 3: order_queue
   - Redis 7: stock cache
   - Kong Gateway: API security
   - Network: noah_network

✅ LEGACY ADAPTER (7/7)         100%
   - CSV polling ✓
   - Data validation ✓
   - MySQL sync ✓
   - Redis sync ✓
   - File processing ✓
   - Retry logic ✓
   - Logging ✓

✅ ORDER API (8/8)              100%
   - GET /orders (pagination) ✓
   - GET /report (data stitching) ✓
   - POST /orders ✓
   - Redis anti-overselling ✓
   - Input validation ✓
   - RabbitMQ publish ✓
   - Retry logic ✓
   - Error handling ✓

✅ ORDER WORKER (7/7)           100%
   - RabbitMQ consume ✓
   - Payment simulation ✓
   - MySQL inventory update ✓
   - PostgreSQL insert ✓
   - ACK/NACK logic ✓
   - Error resilience ✓
   - Logging ✓

✅ DASHBOARD (7/7)              100%
   - React frontend ✓
   - Real-time pagination ✓
   - KPI display ✓
   - Data stitching integration ✓
   - Loading state ✓
   - Empty state ✓
   - Responsive design ✓

✅ SECURITY (4/4)               100%
   - Kong Gateway ✓
   - API Key Auth ✓
   - Rate Limiting ✓
   - Routes mapping ✓

📊 TOTAL: 39/39 = 100% ✅
```

---

**Slide 11: Key Metrics**

- **Data Volume**: 20,000 orders in database
- **API Response Time**: < 100ms (pagination)
- **Queue Processing**: 1 message per second (payment sim)
- **Database Support**: MySQL + PostgreSQL
- **Security**: 3-layer (Kong + Auth + Rate Limit)
- **Uptime**: Auto-restart on crash (docker restart: always)
- **Code Quality**: Error handling + retry logic on all critical paths

---

### **PHẦN 7: LEARNING OUTCOMES (1 phút)**

**Slide 12: What We Learned**

1. **Microservices Architecture**
   - API Gateway pattern (Kong)
   - Service decoupling (RabbitMQ)
   - Data ownership (separate databases)

2. **Concurrency & Performance**
   - Redis atomic operations (race condition prevention)
   - Connection pooling (retry logic)
   - Pagination (memory efficiency)

3. **Data Integration**
   - Multi-database joins (data stitching)
   - Legacy system migration (CSV adapter)
   - Event-driven processing (async workers)

4. **DevOps & Infrastructure**
   - Docker containerization
   - Container orchestration (docker-compose)
   - Network isolation (virtual networks)

5. **Full-Stack Development**
   - Backend: Python (Flask/HTTP Server)
   - Frontend: React (Vite)
   - Databases: MySQL, PostgreSQL
   - Message Queue: RabbitMQ

---

### **PHẦN 8: CONCLUSION (1 phút)**

**Slide 13: Summary & Q&A**

```
📌 Key Takeaways:
1. Microservices = independent, scalable services
2. Message queues = async processing + reliability
3. Caching = performance boost (Redis)
4. Monitoring = know what's happening (logs)
5. Testing = demo real features

🚀 Future Enhancements:
- WebSocket real-time updates
- Notification system (email/SMS)
- Advanced analytics & ML
- Mobile app
- Kubernetes orchestration
```

**Closing Statement:**
> "NOAH Retail demonstrates how modern e-commerce platforms are built: scalable, resilient, and user-friendly. Phân tách mối quan tâm, async processing, và data integration là những nền tảng của hệ thống thực tế."

**Questions?**

---

## 🎬 LIVE DEMO SEQUENCE

### **Setup (Before Presentation)**
```bash
# Terminal 1: Start all services
cd d:\Noah-project
docker-compose up --build

# Wait for all services to be healthy (10-15 seconds)
# Check: docker ps (all containers should show "Up")
```

### **Demo Flow (During Presentation)**

**Demo 1: Dashboard Real-time Pagination**
```
1. Open http://localhost:3000 in browser
2. Show Orders table loading from API
3. Click "Tiếp" (Next) button → Table refreshes
4. Click page number "3" → Jump to page 3
5. Change limit "10 rows" → Shows 5 rows
→ Show: Real-time API integration ✅
```

**Demo 2: Redis Anti-Overselling**
```powershell
# Terminal 2
1. Check product stock
   docker exec redis_cache redis-cli GET "product:10:stock"
   
2. Show: 100 units available
```

**Demo 3: Create Order (POST /orders)**
```powershell
# Terminal 2
$body = @{user_id=999; product_id=10; quantity=5} | ConvertTo-Json
$resp = Invoke-WebRequest `
  -Uri "http://localhost:8001/orders" `
  -Method POST -Body $body -ContentType "application/json" `
  -UseBasicParsing

$resp.Content | ConvertFrom-Json

# Show: order_id = 20001, status = PENDING
```

**Demo 4: Verify Stock Decremented**
```powershell
# Terminal 2
docker exec redis_cache redis-cli GET "product:10:stock"
# Show: 95 (was 100, now 100-5)
```

**Demo 5: Check Message Queue Processing**
```powershell
# Terminal 2
docker logs -f order_worker_server

# Show: Worker processing order, updating inventory, ACKing message
```

**Demo 6: Data Stitching Report**
```powershell
# Terminal 2
$resp = Invoke-WebRequest `
  -Uri "http://localhost:8001/report" -UseBasicParsing

$resp.Content | ConvertFrom-Json | Format-List total_revenue, orders_completed, error_rate

# Show: Unified report from MySQL + PostgreSQL
```

---

## 📝 TALKING POINTS (By Slide)

### Khi nói về Pagination:
> "Tưởng tượng bạn có 20,000 đơn hàng, bạn không thể hiển thị hết trên 1 trang. Nó sẽ chậm và tốn RAM. Vì vậy chúng ta chia thành các trang: trang 1 có 10 đơn hàng, trang 2 có 10 đơn hàng khác. Backend API trả về ?page=1&limit=10, frontend hiển thị các nút Next/Previous."

### Khi nói về Anti-Overselling:
> "Redis là in-memory cache rất nhanh. Khi khách hàng tạo đơn hàng, chúng ta dùng Redis DECR command để giảm stock một cách atomic. Điều này ngăn tình trạng 2 request cùng lúc cùng giảm stock từ 10 xuống 9 → hết hàng chỉ bán được 1 cái."

### Khi nói về RabbitMQ:
> "RabbitMQ là message broker. Khi API nhận đơn hàng, nó không chờ payment processing xong. Nó publish message vào queue, return ngay 201 Created cho client. Worker sẽ consume message từ queue và xử lý async. Nếu worker crash, message vẫn trong queue, worker khi restart sẽ tiếp tục xử lý."

### Khi nói về Data Stitching:
> "Orders ở MySQL, Payments ở PostgreSQL. Khi client yêu cầu report, API fetch orders từ MySQL, fetch payments từ PostgreSQL, merge in code, calculate KPIs. Đây là application-level join - chúng ta join ở backend code thay vì SQL query."

---

## ⏱️ TIMING GUIDE

| Phần | Phút | Nội Dung |
|------|------|---------|
| Giới thiệu | 2 | Title + Problem |
| Vấn đề & Giải pháp | 3 | Challenges |
| Kiến trúc | 4 | Architecture + Components |
| Core Features | 5 | Pagination, Anti-overselling, Async, Data Stitching, Legacy Adapter |
| Challenges & Solutions | 2 | Technical solutions table |
| Results & Metrics | 2 | Project status (100%) |
| Learning Outcomes | 1 | What we learned |
| Conclusion | 1 | Summary + Q&A |
| **TOTAL** | **20** | |

---

## ✅ CHECKLIST TRƯỚC TRÌNH BÀY

- [ ] Docker containers all running (`docker ps`)
- [ ] API responding (`curl http://localhost:8001/orders`)
- [ ] Dashboard loading (`http://localhost:3000`)
- [ ] Redis has stock data (`docker exec redis_cache redis-cli GET "product:10:stock"`)
- [ ] Prepare PowerPoint slides (optional, can use markdown)
- [ ] Test all demo commands in terminal
- [ ] Have backup terminal open for logs
- [ ] Have order ID ready for demo (or create one live)
- [ ] Know alternative demo if one fails

---

## 🎤 PRESENTATION TIPS

1. **Speak Clearly**: Dùng microphone nếu có
2. **Make Eye Contact**: Nhìn vào audience, không chỉ slide
3. **Live Demo**: Demo là phần quan trọng nhất - nó chứng minh công việc thực tế
4. **Be Prepared for Questions**: 
   - "Tại sao chọn RabbitMQ?" → Async processing, reliability
   - "Tại sao Redis?" → In-memory, atomic operations, performance
   - "Tại sao separation of databases?" → Microservices best practice
5. **Have Backup Plan**: Nếu demo fail, có thể show screenshots/videos
6. **Manage Time**: Nếu demo mất thời gian, có thể skip một demo
7. **Highlight Your Contribution**: Nói rõ bạn làm feature nào

---

## 📚 RESOURCES

- [README.md](README.md) - Project overview
- [DEMO_GUIDE.md](DEMO_GUIDE.md) - System architecture details
- [RUN_DEMO.md](RUN_DEMO.md) - Demo commands

---

**Good luck with your presentation! 🚀**
