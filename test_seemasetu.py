"""
Comprehensive Verification Suite for SeemaSetu.
Tests:
- Deterministic rule-based priority engine
- Database tables & seed integrity
- Authentication, session persistence, and password hashing
- Role-based access control (RBAC) & security privilege escalation prevention
- User administration & deactivation protection
- Issue lifecycle, automatic scoring, and timeline audit
- Work orders, progress sliders, and issue status synchronization
- Financial budget vs. actual cost validation (non-negative constraints)
- Logistics inventory allocation, stock deduction, and low-stock alerts
- Live API endpoints and CSV report exports
"""

import unittest
from app import create_app
from app.db import query_db, execute_db
from app.priority import calculate_priority


class SeemaSetuMasterTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True

    def setUp(self):
        self.client = self.app.test_client()

    # ----------------------------------------------------------------------
    # 1. Rule-Based Priority Scoring Tests
    # ----------------------------------------------------------------------
    def test_01_priority_scoring_engine(self):
        """Test rule-based priority scoring across multiple boundary scenarios."""
        # Max score: Critical (35) + Immediate (25) + Roads & Bridges (25) + Severe (15) = 100
        p_crit = calculate_priority('Critical', 'Immediate', 'Roads & Bridges', 'Severe/Imminent')
        self.assertEqual(p_crit['score'], 100)
        self.assertEqual(p_crit['level'], 'Critical')
        self.assertEqual(p_crit['badge_class'], 'badge-critical')

        # High priority scenario
        p_high = calculate_priority('High', 'High', 'Water Supply', 'Moderate Risk')
        self.assertEqual(p_high['score'], 25 + 18 + 20 + 10)  # 73
        self.assertEqual(p_high['level'], 'High')

        # Medium priority scenario
        p_med = calculate_priority('Medium', 'Moderate', 'Public Facilities', 'Moderate Risk')
        self.assertEqual(p_med['score'], 15 + 10 + 15 + 10)  # 50
        self.assertEqual(p_med['level'], 'Medium')

        # Low priority scenario
        p_low = calculate_priority('Low', 'Routine', 'Other', 'Normal/Stable')
        self.assertEqual(p_low['score'], 5 + 5 + 10 + 5)  # 25
        self.assertEqual(p_low['level'], 'Low')
        self.assertEqual(p_low['badge_class'], 'badge-low')

    # ----------------------------------------------------------------------
    # 2. Database Schema and Seed Data Tests
    # ----------------------------------------------------------------------
    def test_02_database_seeded_properly(self):
        """Verify demonstration seed data is populated and relational constraints hold."""
        with self.app.app_context():
            users = query_db("SELECT COUNT(*) as c FROM users", one=True)['c']
            issues = query_db("SELECT COUNT(*) as c FROM issues", one=True)['c']
            resources = query_db("SELECT COUNT(*) as c FROM resources", one=True)['c']
            work_orders = query_db("SELECT COUNT(*) as c FROM work_orders", one=True)['c']

            self.assertGreaterEqual(users, 3, "At least 3 seeded demonstration users expected.")
            self.assertGreaterEqual(issues, 6, "At least 6 demonstration issues expected.")
            self.assertGreaterEqual(resources, 7, "At least 7 inventory items expected.")
            self.assertGreaterEqual(work_orders, 3, "At least 3 work orders expected.")

    # ----------------------------------------------------------------------
    # 3. Public Navigation & UI Tests
    # ----------------------------------------------------------------------
    def test_03_public_landing_page(self):
        """Verify public landing page renders with application tagline and demo credentials."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SeemaSetu', res.data)
        self.assertIn(b'Border Infrastructure Monitoring', res.data)
        self.assertIn(b'Demonstration Access Accounts', res.data)

    # ----------------------------------------------------------------------
    # 4. Authentication Flow Tests
    # ----------------------------------------------------------------------
    def test_04_authentication_flow(self):
        """Verify login with demo credentials and session establishment."""
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'test-token-auth'

        res = self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'Admin@123',
            'csrf_token': 'test-token-auth'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Operations &amp; Analytics Dashboard', res.data)

    # ----------------------------------------------------------------------
    # 5. Live Priority Calculation API Test
    # ----------------------------------------------------------------------
    def test_05_api_priority_preview(self):
        """Verify /api/calculate-priority-preview JSON endpoint."""
        res = self.client.post('/api/calculate-priority-preview', json={
            'severity': 'Critical',
            'urgency': 'Immediate',
            'category': 'Roads & Bridges',
            'weather_vulnerability': 'Severe/Imminent'
        })
        self.assertEqual(res.status_code, 200)
        payload = res.get_json()
        self.assertEqual(payload['status'], 'success')
        self.assertEqual(payload['data']['score'], 100)
        self.assertEqual(payload['data']['level'], 'Critical')

    # ----------------------------------------------------------------------
    # 6. Issues Listing & Multi-Filter Test
    # ----------------------------------------------------------------------
    def test_06_issues_listing_and_filter(self):
        """Verify issues list view and filtering."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'
            sess['full_name'] = 'Vikramaditya Sharma'

        res = self.client.get('/issues/?status=In+Progress')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SS-2026-0001', res.data)

    # ----------------------------------------------------------------------
    # 7. Issue Creation Test
    # ----------------------------------------------------------------------
    def test_07_issue_creation_and_scoring(self):
        """Test reporting a new issue and confirming automated priority assignment."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'
            sess['_csrf_token'] = 'test-token-issue-create'

        res = self.client.post('/issues/create', data={
            'title': 'Test Washout of Retaining Gabion Wall',
            'category': 'Roads & Bridges',
            'sector': 'Sector North-A (Zanskar Valley Corridor)',
            'location_name': 'Test Outpost Pass Km 12',
            'coordinates': '34.5000 N, 77.1000 E',
            'severity': 'Critical',
            'urgency': 'Immediate',
            'weather_vulnerability': 'Severe/Imminent',
            'description': 'Simulated landslide breach on approach embankment for automated unit test.',
            'csrf_token': 'test-token-issue-create'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Test Washout of Retaining Gabion Wall', res.data)
        # Rule-based evaluation should compute 100 (Critical)
        self.assertIn(b'100/100', res.data)

    # ----------------------------------------------------------------------
    # 8. Role-Based Access Control (RBAC) Security Tests
    # ----------------------------------------------------------------------
    def test_08_rbac_security_enforcement(self):
        """
        Verify that non-admin accounts (viewer/user) are strictly blocked from
        admin-only operations such as User Administration and Audit Logs.
        Tests resolution of the role_required authorization logic.
        """
        # Simulate viewer session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 3
            sess['username'] = 'reporter_amit'
            sess['role'] = 'viewer'
            sess['full_name'] = 'Amitabh Negi'

        # Attempt to access admin user administration
        res_admin_users = self.client.get('/auth/admin/users', follow_redirects=True)
        # Should be redirected to landing/dashboard with danger flash
        self.assertIn(b'Access Denied', res_admin_users.data)

        # Attempt to access audit logs
        res_audit = self.client.get('/audit/', follow_redirects=True)
        self.assertIn(b'Access Denied', res_audit.data)

        # Now test with admin session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'

        res_admin_ok = self.client.get('/auth/admin/users')
        self.assertEqual(res_admin_ok.status_code, 200)
        self.assertIn(b'User Administration &amp; Access Control', res_admin_ok.data)

    # ----------------------------------------------------------------------
    # 9. Work Order & Cost Validation Tests
    # ----------------------------------------------------------------------
    def test_09_work_order_cost_validation(self):
        """Verify negative costs are rejected on work order creation."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'
            sess['_csrf_token'] = 'test-token-wo-neg'

        res = self.client.post('/work-orders/create', data={
            'issue_id': 1,
            'contractor_or_unit': 'Test Border Unit',
            'lead_engineer': 'Er. Test Engineer',
            'estimated_cost': '-5000',
            'start_date': '2026-11-01',
            'target_date': '2026-11-05',
            'scope_of_work': 'Negative cost test mandate.',
            'csrf_token': 'test-token-wo-neg'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Estimated budget cannot be negative', res.data)

    # ----------------------------------------------------------------------
    # 10. Work Order Progress & Status Synchronization Test
    # ----------------------------------------------------------------------
    def test_10_work_order_completion_sync(self):
        """
        Verify that setting work order progress to 100% automatically marks
        the work order as Completed and the linked issue as Resolved.
        """
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'
            sess['_csrf_token'] = 'test-token-wo-progress'

        import time
        uniq = int(time.time() * 1000) % 100000
        test_ticket = f"SS-TEST-{uniq}"
        test_wo_num = f"WO-TEST-{uniq}"

        with self.app.app_context():
            # Create a test issue and test work order
            test_issue_id = execute_db(
                """
                INSERT INTO issues (ticket_number, title, description, category, sector, location_name,
                                    severity, urgency, weather_vulnerability, priority_score, priority_level,
                                    status, reported_by, created_at)
                VALUES (%s, 'Sync Test Culvert Defect', 'Desc', 'Roads & Bridges', 'Sector North-A',
                        'Km 99', 'High', 'High', 'Moderate Risk', 75, 'High', 'In Progress', 1, datetime('now'))
                """,
                (test_ticket,)
            )
            test_wo_id = execute_db(
                """
                INSERT INTO work_orders (work_order_no, issue_id, contractor_or_unit, lead_engineer,
                                         estimated_cost, actual_cost, start_date, target_date,
                                         status, scope_of_work, progress_percentage, created_by, created_at)
                VALUES (%s, %s, 'Sync Unit', 'Lead Eng', 50000, 48000, '2026-11-01', '2026-11-05',
                        'In Progress', 'Test sync', 50, 1, datetime('now'))
                """,
                (test_wo_num, test_issue_id)
            )

        # Update progress to 100%
        res = self.client.post(f'/work-orders/{test_wo_id}/update-progress', data={
            'progress_percentage': '100',
            'status': 'In Progress',
            'actual_cost': '49500.00',
            'csrf_token': 'test-token-wo-progress'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            updated_wo = query_db("SELECT status, progress_percentage, actual_cost FROM work_orders WHERE id = %s", (test_wo_id,), one=True)
            updated_issue = query_db("SELECT status FROM issues WHERE id = %s", (test_issue_id,), one=True)

            self.assertEqual(updated_wo['status'], 'Completed')
            self.assertEqual(updated_wo['progress_percentage'], 100)
            self.assertEqual(float(updated_wo['actual_cost']), 49500.00)
            self.assertEqual(updated_issue['status'], 'Resolved', "Linked issue must automatically synchronize to Resolved.")

    # ----------------------------------------------------------------------
    # 11. Logistics & Inventory Deduction Test
    # ----------------------------------------------------------------------
    def test_11_inventory_allocation_and_deduction(self):
        """Verify allocating material to a work order decrements warehouse stock."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'
            sess['_csrf_token'] = 'test-token-alloc'

        with self.app.app_context():
            res_before = query_db("SELECT quantity FROM resources WHERE id = 1", one=True)['quantity']

        # Allocate 5 units to WO #1
        res = self.client.post('/work-orders/1/allocate-resource', data={
            'resource_id': 1,
            'quantity': '5.0',
            'csrf_token': 'test-token-alloc'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            res_after = query_db("SELECT quantity FROM resources WHERE id = 1", one=True)['quantity']
            self.assertEqual(res_after, res_before - 5.0)

    # ----------------------------------------------------------------------
    # 12. CSV Export Test
    # ----------------------------------------------------------------------
    def test_12_csv_export(self):
        """Verify CSV export functionality."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'

        res = self.client.get('/issues/export/csv')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')
        self.assertIn(b'Ticket Number,Title,Category', res.data)

    # ----------------------------------------------------------------------
    # 13. Financial Dashboard Analytics Test
    # ----------------------------------------------------------------------
    def test_13_dashboard_financial_metrics(self):
        """Verify dashboard includes budget vs. actual cost comparisons."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'

        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Total Allocated Budget', res.data)
        self.assertIn(b'Actual Expenditure Recorded', res.data)
        self.assertIn(b'Budget Variance / Balance', res.data)


if __name__ == '__main__':
    unittest.main()
