-- =====================================================================
-- SeemaSetu Seed Data (Fictional Demonstration Data Only)
-- All locations, coordinates, and personnel names are completely fictional
-- and unclassified for education and demonstration purposes.
-- =====================================================================

-- Users
INSERT INTO users (id, username, email, password_hash, full_name, role, department, badge_number, is_active) VALUES
(1, 'admin', 'admin@seemasetu.gov.in', 'scrypt:32768:8:1$Jq1PRdhXr2y9Ct3e$002fad0d2acaf6ff87391d28bc5e0c8b585b9e9892c621938de4bf9b2cf8a4effb648ffd5a558f5e4e9949a31bede097ad691f0e30ae3b94dd8f1ce5ccd308aa', 'Vikramaditya Sharma', 'admin', 'Border Infrastructure Command', 'HQ-ADM-01', 1),
(2, 'officer_sharma', 'officer@seemasetu.gov.in', 'scrypt:32768:8:1$fOaOPOQCYzurFjlC$00737af1a853c83b1ab6ea3d44d84895f9c50afd06bb2175ec530287aae390d384b82406bab9c3c8ad8796f1bb6653d278d8aaa8925556bc427da0f4eec9a3d5', 'Major R. K. Nair (Retd.)', 'officer', 'Sector Road & Bridge Division', 'FO-SEC-09', 1),
(3, 'reporter_amit', 'amit@seemasetu.gov.in', 'scrypt:32768:8:1$gce4f8C6m0bdcP8E$0220a0acec9fdfbe4ea9328f6c48eb9f8df745b652022b05decbf24464b5701325661188b4978c1da4a1bdc13ae63db518bad1a48093673fe794631c1b6bed9e', 'Amitabh Negi', 'user', 'Field Patrol & Survey Unit', 'FP-SUR-44', 1);

-- Resources / Inventory
INSERT INTO resources (id, resource_code, name, category, quantity, unit, min_threshold, depot_location, unit_cost) VALUES
(1, 'MAT-ASP-01', 'Cold Mix Polymer Asphalt Bags', 'Civil & Road Material', 450.00, 'Bags', 100.00, 'Northern Logistics Base - Staging Depot Alpha', 1250.00),
(2, 'MAT-STEEL-02', 'Bailey Bridge Pre-fab Deck Panels (10ft)', 'Structural Steel', 24.00, 'Units', 10.00, 'Sector Central Depot - Yard 3', 85000.00),
(3, 'ELE-SOL-03', 'High-Mast 120W Hybrid Solar Streetlight Kits', 'Electrical & Solar', 18.00, 'Kits', 15.00, 'Eastern Foothills Hub - Warehouse B', 32000.00),
(4, 'WAT-PIPE-04', 'High-Density Polyethylene (HDPE) PN16 Water Pipes', 'Water Supply & Piping', 85.00, 'Meters', 120.00, 'Western Desert Outpost Supply Point', 650.00),
(5, 'MCH-EXC-05', 'Compact Tracked Hydraulic Excavator (4.5T)', 'Heavy Machinery', 3.00, 'Units', 2.00, 'Northern High Altitude Staging Depot', 3500000.00),
(6, 'ELE-GEN-06', 'All-Weather Diesel Backup Generator (25 kVA)', 'Electrical & Solar', 5.00, 'Units', 3.00, 'Central Logistics Hub - Power Section', 420000.00),
(7, 'MAT-CEM-07', 'Rapid Hardening Portland Slag Cement', 'Civil & Road Material', 620.00, 'Bags', 150.00, 'Sector Central Depot - Yard 1', 480.00);

-- Issues (Demonstration Fictional Border Incidents)
INSERT INTO issues (id, ticket_number, title, description, category, sector, location_name, coordinates, severity, urgency, weather_vulnerability, priority_score, priority_level, status, image_path, reported_by, assigned_to, created_at) VALUES
(1, 'SS-2026-0001', 'Landslide debris blocking Bridge Km 34 approach roadway', 'Heavy rainfall caused rockfall across 60 meters of the primary civil supply route leading to Himjyoti settlement. Roadway narrowed to single lane; risk of further slope failure.', 'Roads & Bridges', 'Sector North-A (Zanskar Valley Corridor)', 'Himjyoti Pass Link Road Km 34.2', '34.2180° N, 77.4120° E', 'Critical', 'Immediate', 'Severe/Imminent', 92, 'Critical', 'In Progress', 'sample_landslide.jpg', 3, 2, '2026-10-24 08:30:00'),
(2, 'SS-2026-0002', 'Solar deep borewell pump motor inverter failure', 'Borewell pump controller burnt due to lightning surge. Drinking water supply halted for Border Civil Transit Camp 4; currently relying on emergency water tanker reserve.', 'Water Supply', 'Sector West-D (Thar Border Staging)', 'Civil Transit Hub 4 Water Tank', '26.8920° N, 70.9230° E', 'High', 'Immediate', 'Moderate Risk', 82, 'Critical', 'Work Order Assigned', 'sample_waterpump.jpg', 3, 2, '2026-10-25 11:15:00'),
(3, 'SS-2026-0003', 'Perimeter solar security lighting battery bank depleted', 'Storm winds damaged solar mounting rack on poles 14 through 18 along boundary security track. Illumination failure creates blacked-out surveillance deadzone.', 'Power & Lighting', 'Sector East-C (Lohit River Foothills)', 'Perimeter Track Mile 8 to 9', '27.9120° N, 96.1540° E', 'High', 'High', 'Severe/Imminent', 74, 'High', 'Under Review', 'sample_streetlight.jpg', 3, NULL, '2026-10-26 14:00:00'),
(4, 'SS-2026-0004', 'Civil community shelter roof insulation insulation tear', 'Sub-zero mountain winds tore corrugated sheet and insulation layer on roof of emergency transit shelter. Infiltration of snow and ice inside common hall.', 'Public Facilities', 'Sector Central-B (Niti High Pass Access)', 'Niti Transit Shelter Block B', '30.8210° N, 79.8450° E', 'Medium', 'Moderate', 'Severe/Imminent', 58, 'High', 'Reported', 'sample_shelter.jpg', 3, NULL, '2026-10-27 09:40:00'),
(5, 'SS-2026-0005', 'Civil wireless telemetry repeater mast guy wire loose', 'Anchor tension bolt loosened by soil erosion after heavy cloudburst. Tower is vibrating under high velocity wind shear; risk of mast structural collapse.', 'Communications', 'Sector North-East (Siang Civil Transit)', 'Ridge Peak Repeater Station R-11', '28.4520° N, 94.9810° E', 'High', 'High', 'Moderate Risk', 68, 'High', 'Reported', 'sample_tower.jpg', 3, NULL, '2026-10-27 16:20:00'),
(6, 'SS-2026-0006', 'Culvert concrete apron eroded by mountain rivulet', 'Scouring of culvert footing foundation at stream crossing; road embankment subsidence observed. Pre-emptive foundation concrete rip-rap required.', 'Roads & Bridges', 'Sector North-A (Zanskar Valley Corridor)', 'Suru River tributary culvert C-19', '34.0950° N, 76.9840° E', 'Medium', 'Moderate', 'Moderate Risk', 45, 'Medium', 'Resolved', 'sample_culvert.jpg', 3, 2, '2026-10-20 10:00:00');

-- Issue Timeline
INSERT INTO issue_timeline (issue_id, user_id, action, previous_status, new_status, remarks, created_at) VALUES
(1, 3, 'ISSUE_REPORTED', NULL, 'Reported', 'Field patrol observed 60m rock slide blocking artery.', '2026-10-24 08:30:00'),
(1, 1, 'PRIORITY_UPDATED', 'Reported', 'Reported', 'Rule-based evaluation raised score to 92 (Critical artery & active slope vulnerability).', '2026-10-24 08:45:00'),
(1, 1, 'STATUS_CHANGE', 'Reported', 'In Progress', 'Assigned Work Order WO-2026-0001 to Northern Fast-Track Road Maintenance Unit.', '2026-10-24 09:30:00'),
(2, 3, 'ISSUE_REPORTED', NULL, 'Reported', 'Water supply failure reported by camp supervisor.', '2026-10-25 11:15:00'),
(2, 2, 'STATUS_CHANGE', 'Reported', 'Work Order Assigned', 'Work Order WO-2026-0002 issued to Western Electrical & Water Maintenance Task Force.', '2026-10-25 13:00:00'),
(6, 3, 'ISSUE_REPORTED', NULL, 'Reported', 'Foundation scouring noticed during routine bridge check.', '2026-10-20 10:00:00'),
(6, 2, 'STATUS_CHANGE', 'Reported', 'In Progress', 'Work order issued for reinforced concrete apron.', '2026-10-21 09:00:00'),
(6, 1, 'STATUS_CHANGE', 'In Progress', 'Resolved', 'Repair completed and inspected by Senior Engineer. Culvert apron secured.', '2026-10-23 17:00:00');

-- Work Orders
INSERT INTO work_orders (id, work_order_no, issue_id, contractor_or_unit, lead_engineer, estimated_cost, actual_cost, start_date, target_date, completion_date, status, scope_of_work, progress_percentage, created_by, created_at) VALUES
(1, 'WO-2026-0001', 1, '74th Border Infrastructure Task Force', 'Er. Tenzin Dorjee', 285000.00, 140000.00, '2026-10-24', '2026-10-29', NULL, 'In Progress', 'Deploy heavy hydraulic excavator to clear 60m rockfall; install 25m gabion wire mesh wall to stabilize uphill talus slope; resurface damaged bituminous layer.', 65, 1, '2026-10-24 09:30:00'),
(2, 'WO-2026-0002', 2, 'Western Electrical & Water Works Corps', 'Er. Sunita Rathore', 75000.00, 0.00, '2026-10-25', '2026-10-28', NULL, 'Assigned', 'Replace damaged 7.5 HP MPPT solar pump inverter; inspect lightning arrestor ground rod resistance; flush pump intake lines and test water purity.', 10, 2, '2026-10-25 13:00:00'),
(3, 'WO-2026-0003', 6, 'Himalayan Civil Works Unit 12', 'Er. Arvind Rawat', 120000.00, 115000.00, '2026-10-21', '2026-10-23', '2026-10-23', 'Completed', 'Cast M25 grade reinforced concrete rip-rap apron around culvert foundation; clear upstream waterway sediment.', 100, 2, '2026-10-21 09:00:00');

-- Resource Allocations
INSERT INTO resource_allocations (id, work_order_id, resource_id, quantity_allocated, allocated_by, allocated_at) VALUES
(1, 1, 1, 80.00, 1, '2026-10-24 10:00:00'),
(2, 1, 5, 1.00, 1, '2026-10-24 10:00:00'),
(3, 3, 7, 65.00, 2, '2026-10-21 09:30:00');

-- Audit Logs
INSERT INTO audit_logs (id, user_id, username, action, entity_type, entity_id, details, ip_address, created_at) VALUES
(1, 1, 'admin', 'SYSTEM_INITIALIZED', 'System', 'SYSTEM', 'SeemaSetu database schema initialized with baseline configurations.', '127.0.0.1', '2026-10-20 08:00:00'),
(2, 3, 'reporter_amit', 'ISSUE_CREATED', 'Issue', 'SS-2026-0001', 'Reported landslide blockage on Km 34 link road.', '192.168.1.45', '2026-10-24 08:30:00'),
(3, 1, 'admin', 'WORK_ORDER_CREATED', 'WorkOrder', 'WO-2026-0001', 'Created emergency work order for 74th Task Force with budget ₹2,85,000.', '192.168.1.10', '2026-10-24 09:30:00'),
(4, 3, 'reporter_amit', 'ISSUE_CREATED', 'Issue', 'SS-2026-0002', 'Reported solar borewell pump breakdown at Transit Camp 4.', '192.168.1.45', '2026-10-25 11:15:00'),
(5, 2, 'officer_sharma', 'WORK_ORDER_CREATED', 'WorkOrder', 'WO-2026-0002', 'Issued pump repair order to Western Corps.', '192.168.1.22', '2026-10-25 13:00:00');
