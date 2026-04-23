# 🧪 HƯỚNG DẪN CHẠY TEST ĐỒ ÁN - NOAH PROJECT

**Dự án:** NOAH - Microservices E-commerce Platform  
**Ngày:** April 23, 2026  
**Loại:** Group Project - Full Stack Testing  

---

## ✅ BƯỚC 1: Kiểm Tra Docker Containers

### Lệnh chạy:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Kết quả mong muốn:
```
NAMES                 STATUS
dashboard_ui          Up 52 minutes
legacy_adapter        Up 52 minutes
order_worker_server   Up 52 minutes
order_api_server      Up 52 minutes (healthy)
redis_cache           Up About an hour
rabbitmq_server       Up About an hour
postgres_db           Up About an hour
mysql_db              Up About an hour
kong_gateway          Up 52 minutes (healthy)
```

### Nếu DOWN, rebuild:
```powershell
cd d:\Noah-project
docker-compose down -v
docker-compose up --build
```

⏳ **Chờ ~30 giây** cho tất cả containers khởi động

---

## ✅ BƯỚC 2: TEST Dashboard Pagination UI

### Cách làm:
1. Mở trình duyệt
2. Truy cập: **http://localhost:3000**
3. Nhìn thấy bảng Orders

### Các yếu tố kiểm tra:
- ✅ Có nút "Trước" (Previous)
- ✅ Có nút "Tiếp" (Next)
- ✅ Có số trang (1, 2, 3, ...)
- ✅ Có dropdown "Hiển thị: 5 rows / 10 rows / 20 rows / 50 rows"

### Thử tương tác:
```
Bước 1: Click "Tiếp" → Bảng hiển thị trang 2
Bước 2: Click số "3" → Jump đến trang 3
Bước 3: Chọn "20 rows" → Bảng hiển thị 20 dòng/trang
Bước 4: Reload page (F5) → Data load lại từ API
```

### Kết quả mong muốn:
✅ **Data load real-time từ API, pagination hoạt động mượt mà**

---

## ✅ BƯỚC 3: TEST API Pagination - Trang 1

### Mở PowerShell mới

```powershell
# Copy-paste lệnh này:
$resp = Invoke-WebRequest -Uri "http://localhost:8001/orders?page=1&limit=10" -UseBasicParsing
$data = $resp.Content | ConvertFrom-Json

Write-Host "=== PAGINATION INFO ===" -ForegroundColor Green
$data.pagination | Format-Table page, limit, total, pages

Write-Host "`n=== ORDER DATA ===" -ForegroundColor Cyan
$data.data | Select-Object id, user_id, product_id, quantity, status | Format-Table
```

### Kết quả mong muốn:
```
page limit total pages
---- ----- ----- -----
   1    10 20000  2000

id user_id product_id quantity status
-- ------- ---------- -------- ------
 1     979        195        3 PENDING
 2     691        143        2 PENDING
 3     587        252        4 PENDING
 4     580        137        2 PENDING
 5     325        276        2 PENDING
 6     ...        ...        ...  ...
10     ...        ...        ...  ...
```

### Giải thích:
- **page:** 1 (trang đầu tiên)
- **limit:** 10 (hiển thị 10 đơn hàng)
- **total:** 20000 (tổng 20,000 đơn hàng)
- **pages:** 2000 (chia thành 2,000 trang)

✅ **PASS** = Pagination API hoạt động!

---

## ✅ BƯỚC 4: TEST API Pagination - Trang 2

### Copy-paste lệnh này:

```powershell
# Test trang 2, 5 dòng
$resp = Invoke-WebRequest -Uri "http://localhost:8001/orders?page=2&limit=5" -UseBasicParsing
$data = $resp.Content | ConvertFrom-Json

Write-Host "=== PAGE 2, LIMIT 5 ===" -ForegroundColor Yellow
$data.pagination | Format-Table page, limit, total, pages

Write-Host "`n=== ORDER DATA ===" -ForegroundColor Green
$data.data | Select-Object id, user_id, product_id, quantity, status | Format-Table
```

### Kết quả mong muốn:
```
page limit total pages
---- ----- ----- -----
   2     5 20000  4000

id user_id product_id quantity status
-- ------- ---------- -------- ------
 6     325        276        2 PENDING
 7     ...        ...        ...  ...
10     ...        ...        ...  ...
```

### Giải thích:
- Order 1-5 ở trang 1
- Order 6-10 ở trang 2 ✅
- 5000 trang khi limit=5 ✅

---

## ✅ BƯỚC 5: TEST Redis Anti-Overselling - Check Stock

### Copy-paste lệnh này:

```powershell
# Kiểm tra stock của product 10
docker exec redis_cache redis-cli GET "product:10:stock"
```

### Kết quả mong muốn:
```
0
hoặc
(nil)
```

**Nếu kết quả là (nil) hoặc 0:** Chuyển sang BƯỚC 6

---

## ✅ BƯỚC 6: TEST Redis Anti-Overselling - Initialize Stock

### Copy-paste lệnh này:

```powershell
# Khởi tạo stock = 100 units
docker exec redis_cache redis-cli SET "product:10:stock" 100

# Verify
docker exec redis_cache redis-cli GET "product:10:stock"
```

### Kết quả mong muốn:
```
100
```

✅ **Stock: 100 units**

---

## ✅ BƯỚC 7: TEST Redis Anti-Overselling - DECR Operation

### Copy-paste lệnh này:

```powershell
# Giảm stock 5 units (simulate khách hàng mua 5 cái)
docker exec redis_cache redis-cli DECRBY "product:10:stock" 5

# Verify stock sau khi DECR
docker exec redis_cache redis-cli GET "product:10:stock"
```

### Kết quả mong muốn:
```
95
```

### Giải thích:
- Stock trước: 100
- Giảm: -5
- Stock sau: **95** ✅

✅ **Atomic DECR operation hoạt động!**

---

## ✅ BƯỚC 8: TEST Legacy Adapter - Xem Logs

### Mở PowerShell mới

```powershell
# Xem logs của Legacy Adapter
docker logs -f legacy_adapter
```

### Kết quả mong muốn:
```
[INFO] Legacy Adapter starting... Polling /app/input/ every 10s
[WARN] Skipped row: {product_id: 128, quantity: 999999999} - Reason: Quantity too large (OUTLIER)
[WARN] Skipped row: {product_id: 188, quantity: 999999999} - Reason: Quantity too large (OUTLIER)
[WARN] Skipped row: {product_id: 236, quantity: 999999999} - Reason: Quantity too large (OUTLIER)
...
[INFO] File processed. Processed: 4585, Skipped: 415
```

### Giải thích:
- **Total CSV rows:** 5000
- **Processed (import):** 4585 rows
- **Skipped (OUTLIERS):** 415 rows (quantity = 999999999)
- **Error rate:** 8.3% (415/5000)

✅ **Dirty Data Handling PASS!**

### Nhấn Ctrl+C để thoát logs

---

## ✅ BƯỚC 9: TEST Order API Logs

### Mở PowerShell mới

```powershell
# Xem logs của Order API
docker logs -f order_api_server
```

### Kết quả mong muốn:
```
[INFO] MySQL connection established
[INFO] RabbitMQ connection established
[INFO] PostgreSQL connection established
[INFO] Server listening on port 8000
[INFO] GET /orders request received (page=1, limit=10)
[INFO] Returning 10 orders from MySQL
```

### Nhấn Ctrl+C để thoát logs

---

## ✅ BƯỚC 10: TEST Order Worker Logs

### Mở PowerShell mới

```powershell
# Xem logs của Order Worker
docker logs -f order_worker_server
```

### Kết quả mong muốn:
```
[INFO] Worker started, consuming from order_queue...
[INFO] Waiting for messages...
[INFO] Message received: {order_id: 20001, ...}
[INFO] Processing order #20001...
[INFO] Updating inventory in MySQL
[INFO] Inserting payment record to PostgreSQL
[INFO] ACK message
```

### Nhấn Ctrl+C để thoát logs

---

## ✅ BƯỚC 11: TEST Dashboard Real-time Update (Final)

### Quay lại Browser

**URL:** http://localhost:3000

### Thử tương tác:
```
Bước 1: Click "Tiếp" (Next button)
        → Bảng update ngay
        → Data load từ API
        
Bước 2: Change "5 rows" → "20 rows"
        → Bảng hiển thị 20 dòng
        → No delay
        
Bước 3: Click page number "5"
        → Jump đến trang 5 ngay
        
Bước 4: Reload page (F5)
        → Data load lại
        → Pagination reset về trang 1
```

### Kết quả mong muốn:
✅ **Dashboard hoạt động smooth, real-time update từ API**

---

## 📊 SUMMARY - Những gì bạn đã test:

```
✅ INFRASTRUCTURE (9 containers)
   - MySQL, PostgreSQL, RabbitMQ, Redis, Kong running
   - All services healthy

✅ PAGINATION SYSTEM
   Frontend:
   - Dashboard UI: Click buttons, jump pages, change limit
   Backend:
   - API: GET /orders?page=X&limit=Y returns paginated data
   - Total: 20,000 orders, 2,000-4,000 pages (depending on limit)

✅ REDIS ANTI-OVERSELLING
   - SET stock = 100
   - DECRBY stock = 95
   - Atomic operation prevents race condition

✅ DIRTY DATA HANDLING (OUTLIERS)
   - CSV file: 5000 rows
   - OUTLIERS detected: 415 rows (quantity = 999999999)
   - Processed: 4585 rows (imported to MySQL + Redis)
   - Skipped: 415 rows (with error logging)
   - Error rate: 8.3% (< 10% acceptable)

✅ ASYNC MESSAGE PROCESSING
   - Order API receives request
   - Publishes message to RabbitMQ
   - Order Worker consumes and processes async
   - Status updates in real-time

✅ REAL-TIME DASHBOARD
   - Fetch data from API on page load
   - Update when pagination changes
   - No hard refresh needed
```

---

## 🎤 SCRIPT TRÌNH BÀY

### Khi trình bày với thầy:

> "Chúng em xây dựng hệ thống bán lẻ điện tử với kiến trúc microservices, gồm 5 module chính:
>
> **MODULE 1 - Legacy Adapter (Xử lý dữ liệu cũ):**
> - Đọc CSV file với 5000 dòng tồn kho
> - Tự động phát hiện và bỏ qua OUTLIERS (415 rows với quantity = 999999999)
> - Kết quả: 4585 processed, 415 skipped (error rate 8.3%)
> - Sử dụng try-except để xử lý lỗi dữ liệu bẩn
>
> **MODULE 2 - Order API (REST API):**
> - Hỗ trợ pagination cho 20,000 đơn hàng
> - Chia thành 2,000 trang (limit=10) hoặc 4,000 trang (limit=5)
> - Endpoint: GET /orders?page=X&limit=Y
>
> **MODULE 3 - Redis (Anti-Overselling):**
> - Dùng atomic DECR operation để chống tình trạng bán quá số lượng
> - Khi khách mua 5 cái, stock giảm từ 100 → 95 ngay lập tức
>
> **MODULE 4 - Order Worker (Async Processing):**
> - Consume message từ RabbitMQ queue
> - Xử lý async (payment simulation, inventory update)
> - Decoupling: API không chờ worker
>
> **MODULE 5 - Dashboard (React UI):**
> - Real-time pagination UI
> - Click Next/Previous/Jump page
> - Change limit (5/10/20/50 rows)
> - Data auto-reload từ API"

---

## 🚀 QUICK COMMANDS

### Rebuild toàn bộ:
```powershell
cd d:\Noah-project
docker-compose down -v
docker-compose up --build
```

### Test API nhanh:
```powershell
(Invoke-WebRequest -Uri "http://localhost:8001/orders?page=1&limit=5" -UseBasicParsing).Content | ConvertFrom-Json | ConvertTo-Json -Depth 2
```

### Check Redis:
```powershell
docker exec redis_cache redis-cli GET "product:10:stock"
```

### View logs:
```powershell
docker logs -f legacy_adapter      # Legacy Adapter
docker logs -f order_api_server    # Order API
docker logs -f order_worker_server # Order Worker
docker logs -f dashboard_ui        # Dashboard
```

### Stop all:
```powershell
docker-compose down
```

---

## ❓ TROUBLESHOOTING

### Q: Dashboard không load
**A:** 
```powershell
docker logs dashboard_ui
docker-compose up --build dashboard
```

### Q: API trả về 500 error
**A:**
```powershell
docker logs order_api_server
# Check MySQL/PostgreSQL/RabbitMQ connection
```

### Q: Redis key không tồn tại
**A:**
```powershell
docker exec redis_cache redis-cli SET "product:10:stock" 100
```

### Q: Legacy Adapter không process CSV
**A:**
```powershell
# Verify file exists
docker exec legacy_adapter ls -la /app/input/

# Check logs
docker logs -f legacy_adapter
```

---

## 📝 NOTES

- **File inventory.csv:** 5000 rows, 415 OUTLIERS
- **Database:** 20,000 sample orders in MySQL
- **Containers:** 9 total (MySQL, PostgreSQL, RabbitMQ, Redis, Kong, API, Worker, Adapter, Dashboard)
- **API Port:** 8001
- **Dashboard Port:** 3000
- **Kong Gateway Port:** 8000

---

## ✅ CHECKLIST TRƯỚC TRÌNH BÀY

- [ ] Docker containers all running
- [ ] Dashboard loads (http://localhost:3000)
- [ ] API responds (GET /orders)
- [ ] Redis has stock data
- [ ] Logs are clean (no critical errors)
- [ ] CSV file in /shared_data/input/
- [ ] Legacy adapter processed file (check logs)
- [ ] Pagination UI buttons work
- [ ] Database has 20,000 orders
- [ ] All screenshots/commands tested

---

**Good luck! 🚀**

Hãy chạy từ BƯỚC 1 và thực hiện tất cả các steps!
