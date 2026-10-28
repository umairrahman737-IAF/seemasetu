-- =====================================================================
-- SeemaSetu Database Schema
-- Border Infrastructure Monitoring and Maintenance System
-- Compatible with MySQL 8.0+, SQLite (via translation layer), and cloud-hosted MySQL
-- =====================================================================

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer', -- 'admin', 'engineer', 'maintenance', 'viewer'
    department VARCHAR(100) DEFAULT 'Border Roads & Civil Infrastructure',
    badge_number VARCHAR(50) DEFAULT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS issues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(30) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'Roads & Bridges', 'Water Supply', 'Power & Lighting', 'Communications', 'Public Facilities'
    sector VARCHAR(100) NOT NULL,  -- Fictional Border Sector
    location_name VARCHAR(200) NOT NULL,
    coordinates VARCHAR(100) DEFAULT NULL, -- Fictional demonstration coordinates
    severity VARCHAR(20) NOT NULL, -- 'Critical', 'High', 'Medium', 'Low'
    urgency VARCHAR(20) NOT NULL,  -- 'Immediate', 'High', 'Moderate', 'Routine'
    weather_vulnerability VARCHAR(30) DEFAULT 'Moderate Risk', -- 'Severe/Imminent', 'Moderate Risk', 'Normal/Stable'
    priority_score INT NOT NULL DEFAULT 50, -- Rule-based calculated score (0-100)
    priority_level VARCHAR(20) NOT NULL DEFAULT 'Medium', -- 'Critical', 'High', 'Medium', 'Low'
    status VARCHAR(30) NOT NULL DEFAULT 'Reported', -- 'Reported', 'Under Review', 'Work Order Assigned', 'In Progress', 'Resolved', 'Closed'
    image_path VARCHAR(255) DEFAULT NULL,
    reported_by INT NOT NULL,
    assigned_to INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (reported_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS issue_timeline (
    id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT NOT NULL,
    user_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    previous_status VARCHAR(30) DEFAULT NULL,
    new_status VARCHAR(30) DEFAULT NULL,
    remarks TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS work_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    work_order_no VARCHAR(30) NOT NULL UNIQUE,
    issue_id INT NOT NULL,
    contractor_or_unit VARCHAR(150) NOT NULL,
    lead_engineer VARCHAR(100) NOT NULL,
    estimated_cost DECIMAL(12,2) DEFAULT 0.00,
    actual_cost DECIMAL(12,2) DEFAULT 0.00,
    start_date DATE NOT NULL,
    target_date DATE NOT NULL,
    completion_date DATE DEFAULT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Assigned', -- 'Assigned', 'In Progress', 'Under Inspection', 'Completed', 'Delayed'
    scope_of_work TEXT NOT NULL,
    progress_percentage INT DEFAULT 0,
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resource_code VARCHAR(30) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'Civil & Road Material', 'Electrical & Solar', 'Water Supply & Piping', 'Heavy Machinery', 'Structural Steel'
    quantity DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    unit VARCHAR(30) NOT NULL, -- 'Tons', 'Units', 'Meters', 'Drums', 'Kits'
    min_threshold DECIMAL(10,2) NOT NULL DEFAULT 10.00,
    depot_location VARCHAR(150) NOT NULL,
    unit_cost DECIMAL(10,2) DEFAULT 0.00,
    last_restocked DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS resource_allocations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    work_order_id INT NOT NULL,
    resource_id INT NOT NULL,
    quantity_allocated DECIMAL(10,2) NOT NULL,
    allocated_by INT NOT NULL,
    allocated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE RESTRICT,
    FOREIGN KEY (allocated_by) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL,
    username VARCHAR(50) DEFAULT 'System',
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) DEFAULT NULL,
    details TEXT DEFAULT NULL,
    ip_address VARCHAR(50) DEFAULT '127.0.0.1',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
