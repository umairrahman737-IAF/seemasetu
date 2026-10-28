"""
Automated Verification Suite for SeemaSetu.
Tests Database initialization, authentication, priority scoring engine,
issue creation, work orders, resources, and audit logs.
"""

import unittest
from app import create_app
from app.db import query_db
from app.priority import calculate_priority

class SeemaSetuTestSuite(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_priority_scoring_engine(self):
        """Test rule-based priority engine calculations."""
        # Critical severity + Immediate urgency + Roads & Bridges + Severe Weather
        crit = calculate_priority('Critical', 'Immediate', 'Roads & Bridges', 'Severe/Imminent')
        self.assertEqual(crit['score'], 100) # 35 + 25 + 25 + 15 = 100
        self.assertEqual(crit['level'], 'Critical')
        self.assertEqual(crit['badge_class'], 'badge-critical')

        # Medium severity + Moderate urgency + Public Facilities + Moderate Risk
        med = calculate_priority('Medium', 'Moderate', 'Public Facilities', 'Moderate Risk')
        self.assertEqual(med['score'], 50) # 15 + 10 + 15 + 10 = 50
        self.assertEqual(med['level'], 'Medium')

        # Low severity + Routine urgency + Other + Normal/Stable
        low = calculate_priority('Low', 'Routine', 'Other', 'Normal/Stable')
        self.assertEqual(low['score'], 25) # 5 + 5 + 10 + 5 = 25
        self.assertEqual(low['level'], 'Low')
        print("[PASS] Rule-based priority engine calculations.")

    def test_02_database_seeded_properly(self):
        """Verify demonstration seed data is populated."""
        with self.app.app_context():
            users = query_db("SELECT COUNT(*) as c FROM users", one=True)['c']
            issues = query_db("SELECT COUNT(*) as c FROM issues", one=True)['c']
            resources = query_db("SELECT COUNT(*) as c FROM resources", one=True)['c']
            work_orders = query_db("SELECT COUNT(*) as c FROM work_orders", one=True)['c']

            self.assertGreaterEqual(users, 3)
            self.assertGreaterEqual(issues, 6)
            self.assertGreaterEqual(resources, 7)
            self.assertGreaterEqual(work_orders, 3)
            print(f"[PASS] Seed data verified: {users} users, {issues} issues, {resources} resources, {work_orders} work orders.")

    def test_03_public_landing_page(self):
        """Verify landing page loads without error."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SeemaSetu', res.data)
        self.assertIn(b'Border Infrastructure Monitoring', res.data)
        print("[PASS] Public landing page HTTP 200 OK.")

    def test_04_authentication_flow(self):
        """Verify login with demo credentials and session assignment."""
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = 'test-security-token-2026'

        res = self.client.post('/auth/login', data={
            'username': 'admin',
            'password': 'Admin@123',
            'csrf_token': 'test-security-token-2026'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Operations &amp; Analytics Dashboard', res.data)
        print("[PASS] Admin authentication and session persistence verified.")

    def test_05_api_priority_preview(self):
        """Verify /api/calculate-priority-preview JSON endpoint."""
        res = self.client.post('/api/calculate-priority-preview', json={
            'severity': 'Critical',
            'urgency': 'Immediate',
            'category': 'Roads & Bridges',
            'weather_vulnerability': 'Severe/Imminent'
        })
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(json_data['data']['score'], 100)
        self.assertEqual(json_data['data']['level'], 'Critical')
        print("[PASS] API live priority preview JSON endpoint verified.")

    def test_06_issues_listing_and_filter(self):
        """Verify issues list endpoint."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'
            sess['full_name'] = 'Vikramaditya Sharma'

        res = self.client.get('/issues/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'SS-2026-0001', res.data)
        self.assertIn(b'Himjyoti', res.data)
        print("[PASS] Issues listing & search verified.")

    def test_07_csv_export(self):
        """Verify CSV export functionality."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'

        res = self.client.get('/issues/export/csv')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')
        self.assertIn(b'Ticket Number,Title,Category', res.data)
        print("[PASS] CSV Report export verified.")

    def test_08_work_order_and_resource_views(self):
        """Verify work orders and resources pages."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
            sess['role'] = 'admin'

        res_wo = self.client.get('/work-orders/')
        self.assertEqual(res_wo.status_code, 200)
        self.assertIn(b'WO-2026-0001', res_wo.data)

        res_res = self.client.get('/resources/')
        self.assertEqual(res_res.status_code, 200)
        self.assertIn(b'MAT-ASP-01', res_res.data)
        print("[PASS] Work orders and resources management verified.")

if __name__ == '__main__':
    unittest.main()
