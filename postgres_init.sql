-- PostgreSQL Finance Database Schema
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- Insert sample data
DELETE FROM payments;
INSERT INTO payments (order_id, user_id, amount, status, created_at) VALUES
(1, 979, 396000, 'COMPLETED', NOW()),
(2, 691, 258000, 'COMPLETED', NOW()),
(3, 587, 308000, 'PENDING', NOW()),
(4, 580, 196000, 'COMPLETED', NOW()),
(5, 325, 746000, 'FAILED', NOW()),
(6, 100, 500000, 'COMPLETED', NOW()),
(7, 200, 750000, 'COMPLETED', NOW()),
(8, 300, 1000000, 'COMPLETED', NOW()),
(9, 400, 450000, 'PENDING', NOW()),
(10, 500, 600000, 'COMPLETED', NOW());
