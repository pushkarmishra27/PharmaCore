CREATE DATABASE IF NOT EXISTS meditrack_db;
USE meditrack_db;

CREATE TABLE IF NOT EXISTS owners (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS medicines (
    batch_no VARCHAR(40) PRIMARY KEY,
    medicine_name VARCHAR(120) NOT NULL,
    category VARCHAR(80) NOT NULL,
    manufacturer VARCHAR(120) NOT NULL,
    purchase_price DECIMAL(10,2) NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    expiry_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(120),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NULL,
    customer_name VARCHAR(120) NOT NULL,
    customer_phone VARCHAR(20),
    sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) NOT NULL DEFAULT 0,
    grand_total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sale_items (
    sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    batch_no VARCHAR(40) NOT NULL,
    medicine_name VARCHAR(120) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
    FOREIGN KEY (batch_no) REFERENCES medicines(batch_no)
);

INSERT INTO owners (username, email, password)
VALUES ('pushkar', 'pushkar@example.com', '1234')
ON DUPLICATE KEY UPDATE username = username;

INSERT INTO medicines
(batch_no, medicine_name, category, manufacturer, purchase_price, selling_price, quantity, expiry_date)
VALUES
('MT001', 'Paracetamol 500mg', 'Pain Relief', 'Demo Pharma', 12.00, 20.00, 50, '2027-12-31'),
('MT002', 'ORS Sachet', 'Rehydration', 'Demo Pharma', 8.00, 15.00, 40, '2027-06-30'),
('MT003', 'Antacid Tablets', 'Digestive', 'Demo Pharma', 18.00, 30.00, 30, '2027-03-31')
ON DUPLICATE KEY UPDATE batch_no = batch_no;
