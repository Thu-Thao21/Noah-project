import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  ShoppingBag,
  Users,
  Settings,
  LogOut,
  Search,
  Bell,
  TrendingUp,
  TrendingDown,
  Store,
  MonitorSmartphone,
  ChevronRight,
  Package,
  ChevronLeft,
  ChevronRightIcon
} from 'lucide-react';
import './App.css';

function App() {
  // === PAGINATION STATE ===
  const [orders, setOrders] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);

  // === FETCH ORDERS FROM API ===
  useEffect(() => {
    const fetchOrders = async () => {
      try {
        setLoading(true);
        const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
        const response = await fetch(
          `${apiUrl}/orders?page=${currentPage}&limit=${limit}`
        );
        const data = await response.json();
        
        if (data.success) {
          setOrders(data.data || []);
          setTotal(data.pagination?.total || 0);
          setTotalPages(data.pagination?.pages || 0);
        }
      } catch (error) {
        console.error('Failed to fetch orders:', error);
        setOrders([]);
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, [currentPage, limit]);

  // === PAGINATION HANDLERS ===
  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const handleLimitChange = (e) => {
    setLimit(parseInt(e.target.value));
    setCurrentPage(1); // Reset to first page when limit changes
  };

  const handlePageJump = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">
            <Store size={24} color="#F48FB1" />
          </div>
          <div className="logo-text text-gradient">NOAH Retail</div>
        </div>

        <nav className="nav-menu">
          <a href="#" className="nav-item active">
            <LayoutDashboard className="nav-icon" />
            <span>Dashboard</span>
          </a>
          <a href="#" className="nav-item">
            <ShoppingBag className="nav-icon" />
            <span>Orders</span>
          </a>
          <a href="#" className="nav-item">
            <Users className="nav-icon" />
            <span>Customers</span>
          </a>
          <a href="#" className="nav-item">
            <Package className="nav-icon" />
            <span>Inventory</span>
          </a>

          <div style={{ flex: 1 }}></div>

          <a href="#" className="nav-item">
            <Settings className="nav-icon" />
            <span>Settings</span>
          </a>
          <a href="#" className="nav-item">
            <LogOut className="nav-icon" color="#EF4444" />
            <span style={{ color: '#EF4444' }}>Logout</span>
          </a>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="header">
          <div className="header-title">
            <h1>Welcome back, Admin!!!</h1>
            <p>Dưới đây là những sự kiện diễ ra tại NOAH hôm nay.</p>
          </div>

          <div className="header-actions">
            <div className="search-bar">
              <Search size={18} color="#94A3B8" />
              <input type="text" placeholder="Search orders, clients..." />
            </div>

            <button className="icon-btn">
              <Bell size={20} />
              <span className="notification-badge"></span>
            </button>

            <div className="profile-avatar">
              N
            </div>
          </div>
        </header>

        {/* Top KPIs */}
        <div className="dashboard-grid">
          <div className="stat-card glass">
            <div className="stat-header">
              <div className="stat-icon revenue">
                <TrendingUp size={24} />
              </div>
            </div>
            <div>
              <div className="stat-value">₫245.5M</div>
              <div className="stat-label">Tổng doanh thu (Today)</div>
            </div>
            <div className="stat-footer">
              <span className="trend-up"><TrendingUp size={16} /> 12.5%</span>
              <span style={{ color: 'var(--text-muted)' }}>so với hôm qua</span>
            </div>
          </div>

          <div className="stat-card glass">
            <div className="stat-header">
              <div className="stat-icon orders">
                <ShoppingBag size={24} />
              </div>
            </div>
            <div>
              <div className="stat-value">1,248</div>
              <div className="stat-label">Đơn hàng đang hoạt động</div>
            </div>
            <div className="stat-footer">
              <span className="trend-up"><TrendingUp size={16} /> 4.2%</span>
              <span style={{ color: 'var(--text-muted)' }}>so với hôm qua</span>
            </div>
          </div>

          <div className="stat-card glass">
            <div className="stat-header">
              <div className="stat-icon customers">
                <Users size={24} />
              </div>
            </div>
            <div>
              <div className="stat-value">842</div>
              <div className="stat-label">Khách hàng mới</div>
            </div>
            <div className="stat-footer">
              <span className="trend-down"><TrendingDown size={16} /> 1.8%</span>
              <span style={{ color: 'var(--text-muted)' }}>so với hôm qua</span>
            </div>
          </div>

          <div className="stat-card glass">
            <div className="stat-header">
              <div className="stat-icon growth">
                <MonitorSmartphone size={24} />
              </div>
            </div>
            <div>
              <div className="stat-value">68%</div>
              <div className="stat-label">Chia sẻ trực tuyến</div>
            </div>
            <div className="stat-footer">
              <span className="trend-up"><TrendingUp size={16} /> 5.0%</span>
              <span style={{ color: 'var(--text-muted)' }}>so với tháng trước</span>
            </div>
          </div>
        </div>

        {/* Bento Grid layout for complex components */}
        <div className="bento-grid">
          {/* Recent Orders */}
          <div className="panel glass">
            <div className="panel-header">
              <h2 className="panel-title">Giao dịch gần đây</h2>
              <button className="btn-secondary">View All</button>
            </div>

            {loading ? (
              <div className="loading-spinner">Đang tải đơn hàng...</div>
            ) : (
              <>
                <table className="order-table">
                  <thead>
                    <tr>
                      <th>Order ID</th>
                      <th>Khách hàng</th>
                      <th>Sản phẩm</th>
                      <th>Số lượng</th>
                      <th>Tổng tiền</th>
                      <th>Trạng thái</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.length > 0 ? (
                      orders.map((order) => (
                        <tr key={order.id}>
                          <td>#{order.id}</td>
                          <td>User {order.user_id}</td>
                          <td>
                            <div className="product-cell">
                              <div className="product-img"><Package size={20} color="#6ee7b7" /></div>
                              <div className="product-info">
                                <p>Product {order.product_id}</p>
                                <span>From API</span>
                              </div>
                            </div>
                          </td>
                          <td>{order.quantity}</td>
                          <td>₫{order.total_price?.toLocaleString('vi-VN')}</td>
                          <td>
                            <span className={`status-badge status-${order.status?.toLowerCase()}`}>
                              {order.status || 'PENDING'}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="6" className="empty-state">Không có đơn hàng</td>
                      </tr>
                    )}
                  </tbody>
                </table>

                {/* Pagination Controls */}
                <div className="pagination-container">
                  <div className="pagination-info">
                    <span>Trang {currentPage} của {totalPages} ({total} đơn hàng)</span>
                  </div>

                  <div className="pagination-controls">
                    {/* Previous Button */}
                    <button 
                      className="pagination-btn"
                      onClick={handlePrevPage}
                      disabled={currentPage === 1}
                    >
                      <ChevronLeft size={18} /> Trước
                    </button>

                    {/* Page Numbers */}
                    <div className="page-numbers">
                      {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                        let pageNum;
                        if (totalPages <= 5) {
                          pageNum = i + 1;
                        } else if (currentPage <= 3) {
                          pageNum = i + 1;
                        } else if (currentPage >= totalPages - 2) {
                          pageNum = totalPages - 4 + i;
                        } else {
                          pageNum = currentPage - 2 + i;
                        }
                        
                        return (
                          <button
                            key={pageNum}
                            className={`page-btn ${currentPage === pageNum ? 'active' : ''}`}
                            onClick={() => handlePageJump(pageNum)}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                    </div>

                    {/* Next Button */}
                    <button 
                      className="pagination-btn"
                      onClick={handleNextPage}
                      disabled={currentPage >= totalPages}
                    >
                      Tiếp <ChevronRightIcon size={18} />
                    </button>
                  </div>

                  {/* Limit Selector */}
                  <div className="limit-selector">
                    <label htmlFor="limit">Hiển thị:</label>
                    <select 
                      id="limit" 
                      value={limit} 
                      onChange={handleLimitChange}
                      className="limit-select"
                    >
                      <option value={5}>5 rows</option>
                      <option value={10}>10 rows</option>
                      <option value={20}>20 rows</option>
                      <option value={50}>50 rows</option>
                    </select>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Store Performance */}
          <div className="panel glass">
            <div className="panel-header">
              <h2 className="panel-title">Hiệu suất kênh</h2>
            </div>

            <div className="store-list">
              <div className="store-item">
                <div className="store-info">
                  <span>Online (Web & App)</span>
                  <span style={{ fontWeight: 600 }}>68%</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill online-fill" style={{ width: '68%' }}></div>
                </div>
              </div>

              <div className="store-item">
                <div className="store-info">
                  <span>Store #1 (Hue)</span>
                  <span style={{ fontWeight: 600 }}>12%</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: '12%' }}></div>
                </div>
              </div>

              <div className="store-item">
                <div className="store-info">
                  <span>Store #2 (Da Nang)</span>
                  <span style={{ fontWeight: 600 }}>8%</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: '8%' }}></div>
                </div>
              </div>

              <div className="store-item">
                <div className="store-info">
                  <span>Store #3 (Da Nang)</span>
                  <span style={{ fontWeight: 600 }}>5%</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: '5%' }}></div>
                </div>
              </div>

              <div className="store-item">
                <div className="store-info">
                  <span>Store #4 & #5</span>
                  <span style={{ fontWeight: 600 }}>7%</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: '7%' }}></div>
                </div>
              </div>

            </div>
          </div>
        </div>

      </main>
    </div>
  );
}

export default App;
