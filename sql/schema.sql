CREATE DATABASE IF NOT EXISTS seemasetu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE seemasetu;
CREATE TABLE users (
 id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL,
 email VARCHAR(160) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL,
 role ENUM('admin','engineer','maintenance','viewer') NOT NULL DEFAULT 'viewer',
 active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE issues (
 id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(150) NOT NULL, description TEXT NOT NULL,
 asset_type ENUM('Road','Bridge','Pothole','Streetlight','Water Supply','Public Facility','Slope','Tunnel','Other') NOT NULL,
 simulated_location VARCHAR(120) NOT NULL,
 severity ENUM('Low','Medium','High','Critical') NOT NULL DEFAULT 'Medium',
 urgency ENUM('Routine','Soon','Urgent','Immediate') NOT NULL DEFAULT 'Soon',
 priority_score TINYINT NOT NULL DEFAULT 2,
 status ENUM('Reported','Under Review','Approved','In Progress','Resolved','Rejected') NOT NULL DEFAULT 'Reported',
 photo_filename VARCHAR(255), reporter_id INT NULL, assigned_to VARCHAR(100),
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE SET NULL,
 INDEX idx_issue_status_severity(status,severity), INDEX idx_issue_created(created_at)
);
CREATE TABLE work_orders (
 id INT AUTO_INCREMENT PRIMARY KEY, issue_id INT NOT NULL,
 team_name VARCHAR(100) NOT NULL, task_description TEXT NOT NULL,
 status ENUM('Planned','Assigned','In Progress','Completed','Cancelled') NOT NULL DEFAULT 'Planned',
 estimated_cost DECIMAL(12,2) NOT NULL DEFAULT 0, actual_cost DECIMAL(12,2) NOT NULL DEFAULT 0,
 target_date DATE NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE,
 CHECK(estimated_cost>=0), CHECK(actual_cost>=0), INDEX idx_workorder_status(status)
);
CREATE TABLE resources (
 id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE,
 category VARCHAR(60) NOT NULL, quantity INT NOT NULL DEFAULT 0,
 unit VARCHAR(30) NOT NULL DEFAULT 'units', minimum_quantity INT NOT NULL DEFAULT 0,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CHECK(quantity>=0), CHECK(minimum_quantity>=0)
);
CREATE TABLE audit_logs (
 id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NULL, action VARCHAR(100) NOT NULL,
 details VARCHAR(255) NOT NULL DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL, INDEX idx_audit_created(created_at)
);
CREATE OR REPLACE VIEW v_work_order_cost_summary AS
SELECT status, COUNT(*) order_count, SUM(estimated_cost) estimated_total, SUM(actual_cost) actual_total
FROM work_orders GROUP BY status;

-- Join example
SELECT i.id, i.title, w.team_name, w.status, w.estimated_cost
FROM issues i LEFT JOIN work_orders w ON w.issue_id=i.id;
