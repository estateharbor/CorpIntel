"""Comprehensive backend API testing for CorpIntel India."""
import requests
import sys
from datetime import datetime

BASE_URL = "https://corp-intel-india.preview.emergentagent.com"

class CorpIntelAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.demo_user = None
        self.test_cin = None
        self.test_alert_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log(self, msg, level="INFO"):
        print(f"[{level}] {msg}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, check_response=None):
        """Run a single API test."""
        url = f"{self.base_url}{endpoint}"
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)
        if self.token and 'Authorization' not in req_headers:
            req_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        self.log(f"\n🔍 Test {self.tests_run}: {name}")
        self.log(f"   {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=req_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=req_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}", "PASS")
                
                # Additional response checks
                if check_response and response.status_code < 400:
                    try:
                        resp_json = response.json()
                        check_result = check_response(resp_json)
                        if not check_result:
                            self.log(f"⚠️  Response validation failed", "WARN")
                            success = False
                            self.tests_passed -= 1
                    except Exception as e:
                        self.log(f"⚠️  Response check error: {e}", "WARN")
                
                return success, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.content
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}", "FAIL")
                try:
                    self.log(f"   Response: {response.json()}", "FAIL")
                except:
                    self.log(f"   Response: {response.text[:200]}", "FAIL")
                self.failed_tests.append(f"{name} - Expected {expected_status}, got {response.status_code}")
                return False, {}

        except Exception as e:
            self.log(f"❌ FAILED - Error: {str(e)}", "FAIL")
            self.failed_tests.append(f"{name} - Exception: {str(e)}")
            return False, {}

    # ===== HEALTH & META =====
    def test_health(self):
        """Test GET /api/health."""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "/api/health",
            200,
            check_response=lambda r: 'companies' in r and 'sample_mode' in r
        )
        if success:
            self.log(f"   Companies: {response.get('companies')}, Sample Mode: {response.get('sample_mode')}")
        return success

    # ===== AUTH =====
    def test_demo_login(self):
        """Test POST /api/v1/auth/demo-login."""
        success, response = self.run_test(
            "Demo Login",
            "POST",
            "/api/v1/auth/demo-login",
            200,
            check_response=lambda r: 'access_token' in r and r.get('user', {}).get('plan') == 'pro'
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.demo_user = response.get('user')
            self.log(f"   Token acquired for user: {self.demo_user.get('email')}")
        return success

    def test_register(self):
        """Test POST /api/v1/auth/register."""
        test_email = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
        success, response = self.run_test(
            "Register New User",
            "POST",
            "/api/v1/auth/register",
            200,
            data={"email": test_email, "password": "Test@1234", "name": "Test User"},
            check_response=lambda r: 'access_token' in r and 'user' in r
        )
        return success

    def test_login(self):
        """Test POST /api/v1/auth/login."""
        # First register a user
        test_email = f"login_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
        requests.post(f"{self.base_url}/api/v1/auth/register", 
                     json={"email": test_email, "password": "Test@1234", "name": "Login Test"})
        
        success, response = self.run_test(
            "Login with Email/Password",
            "POST",
            "/api/v1/auth/login",
            200,
            data={"email": test_email, "password": "Test@1234"},
            check_response=lambda r: 'access_token' in r
        )
        return success

    def test_auth_me(self):
        """Test GET /api/v1/auth/me."""
        if not self.token:
            self.log("⚠️  Skipping /auth/me - no token available", "WARN")
            return False
        
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "/api/v1/auth/me",
            200,
            check_response=lambda r: 'user_id' in r and 'email' in r
        )
        return success

    # ===== COMPANIES =====
    def test_list_companies(self):
        """Test GET /api/v1/companies with filters."""
        success, response = self.run_test(
            "List Companies (no filters)",
            "GET",
            "/api/v1/companies?page=1&limit=10",
            200,
            check_response=lambda r: 'results' in r and 'total' in r
        )
        
        if success and response.get('results'):
            self.test_cin = response['results'][0].get('cin')
            self.log(f"   Found {response.get('total')} companies, using CIN: {self.test_cin}")
        
        # Test with filters
        self.run_test(
            "List Companies (with city filter)",
            "GET",
            "/api/v1/companies?city=Mumbai&limit=5",
            200,
            check_response=lambda r: 'results' in r
        )
        
        self.run_test(
            "List Companies (with search)",
            "GET",
            "/api/v1/companies?search=tech&limit=5",
            200,
            check_response=lambda r: 'results' in r
        )
        
        return success

    def test_company_detail(self):
        """Test GET /api/v1/companies/{cin}."""
        if not self.test_cin:
            self.log("⚠️  Skipping company detail - no CIN available", "WARN")
            return False
        
        success, response = self.run_test(
            "Get Company Detail",
            "GET",
            f"/api/v1/companies/{self.test_cin}",
            200,
            check_response=lambda r: 'cin' in r and 'name' in r and 'director_count' in r
        )
        return success

    def test_company_directors(self):
        """Test GET /api/v1/companies/{cin}/directors."""
        if not self.test_cin:
            self.log("⚠️  Skipping directors - no CIN available", "WARN")
            return False
        
        success, response = self.run_test(
            "Get Company Directors",
            "GET",
            f"/api/v1/companies/{self.test_cin}/directors",
            200,
            check_response=lambda r: 'directors' in r and 'count' in r
        )
        return success

    def test_company_charges(self):
        """Test GET /api/v1/companies/{cin}/charges."""
        if not self.test_cin:
            self.log("⚠️  Skipping charges - no CIN available", "WARN")
            return False
        
        success, response = self.run_test(
            "Get Company Charges",
            "GET",
            f"/api/v1/companies/{self.test_cin}/charges",
            200,
            check_response=lambda r: 'charges' in r
        )
        return success

    def test_company_filings(self):
        """Test GET /api/v1/companies/{cin}/filings."""
        if not self.test_cin:
            self.log("⚠️  Skipping filings - no CIN available", "WARN")
            return False
        
        success, response = self.run_test(
            "Get Company Filings",
            "GET",
            f"/api/v1/companies/{self.test_cin}/filings",
            200,
            check_response=lambda r: 'filings' in r
        )
        return success

    def test_company_similar(self):
        """Test GET /api/v1/companies/{cin}/similar."""
        if not self.test_cin:
            self.log("⚠️  Skipping similar - no CIN available", "WARN")
            return False
        
        success, response = self.run_test(
            "Get Similar Companies",
            "GET",
            f"/api/v1/companies/{self.test_cin}/similar?limit=6",
            200,
            check_response=lambda r: 'results' in r
        )
        return success

    def test_company_contact_locked(self):
        """Test GET /api/v1/companies/{cin}/contact (should be locked for free/anon)."""
        if not self.test_cin:
            self.log("⚠️  Skipping contact locked - no CIN available", "WARN")
            return False
        
        # Test without auth (should be locked)
        success, response = self.run_test(
            "Get Company Contact (anon - should be locked)",
            "GET",
            f"/api/v1/companies/{self.test_cin}/contact",
            200,
            headers={'Authorization': ''},  # No auth
            check_response=lambda r: r.get('locked') == True
        )
        return success

    def test_company_contact_unlocked(self):
        """Test GET /api/v1/companies/{cin}/contact (should be unlocked for pro)."""
        if not self.test_cin or not self.token:
            self.log("⚠️  Skipping contact unlocked - no CIN or token", "WARN")
            return False
        
        success, response = self.run_test(
            "Get Company Contact (pro - should be unlocked)",
            "GET",
            f"/api/v1/companies/{self.test_cin}/contact",
            200,
            check_response=lambda r: r.get('locked') == False
        )
        return success

    # ===== ANALYTICS =====
    def test_analytics_summary(self):
        """Test GET /api/v1/analytics/summary."""
        success, response = self.run_test(
            "Analytics Summary",
            "GET",
            "/api/v1/analytics/summary",
            200,
            check_response=lambda r: 'total' in r and 'by_city' in r
        )
        return success

    def test_analytics_trends(self):
        """Test GET /api/v1/analytics/trends."""
        success, response = self.run_test(
            "Analytics Trends",
            "GET",
            "/api/v1/analytics/trends?months=12",
            200,
            check_response=lambda r: 'trends' in r
        )
        return success

    def test_analytics_sectors(self):
        """Test GET /api/v1/analytics/sectors."""
        success, response = self.run_test(
            "Analytics Sectors",
            "GET",
            "/api/v1/analytics/sectors?limit=10",
            200,
            check_response=lambda r: 'sectors' in r
        )
        return success

    def test_analytics_capital(self):
        """Test GET /api/v1/analytics/capital."""
        success, response = self.run_test(
            "Analytics Capital Distribution",
            "GET",
            "/api/v1/analytics/capital",
            200,
            check_response=lambda r: 'distribution' in r
        )
        return success

    def test_analytics_heatmap(self):
        """Test GET /api/v1/analytics/heatmap."""
        success, response = self.run_test(
            "Analytics Heatmap",
            "GET",
            "/api/v1/analytics/heatmap?city=Mumbai",
            200,
            check_response=lambda r: 'heatmap' in r
        )
        return success

    # ===== SEARCH =====
    def test_search_quick(self):
        """Test GET /api/v1/search?q=."""
        success, response = self.run_test(
            "Quick Search",
            "GET",
            "/api/v1/search?q=tech&limit=5",
            200,
            check_response=lambda r: 'results' in r and 'suggestions' in r
        )
        return success

    def test_search_advanced(self):
        """Test POST /api/v1/search/advanced."""
        success, response = self.run_test(
            "Advanced Search",
            "POST",
            "/api/v1/search/advanced",
            200,
            data={
                "city": ["Mumbai"],
                "sector": None,
                "status": None,
                "company_class": None,
                "search": "tech",
                "page": 1,
                "limit": 10,
                "sort_by": "date_of_incorporation",
                "order": "desc"
            },
            check_response=lambda r: 'results' in r
        )
        return success

    def test_search_save(self):
        """Test POST /api/v1/search/save (auth required)."""
        if not self.token:
            self.log("⚠️  Skipping save search - no token", "WARN")
            return False
        
        success, response = self.run_test(
            "Save Search",
            "POST",
            "/api/v1/search/save",
            200,
            data={
                "name": "Test Search",
                "criteria": {"city": ["Mumbai"], "sector": ["Technology"]}
            },
            check_response=lambda r: 'saved' in r
        )
        return success

    def test_search_saved_list(self):
        """Test GET /api/v1/search/saved (auth required)."""
        if not self.token:
            self.log("⚠️  Skipping saved searches list - no token", "WARN")
            return False
        
        success, response = self.run_test(
            "List Saved Searches",
            "GET",
            "/api/v1/search/saved",
            200,
            check_response=lambda r: 'saved_searches' in r
        )
        return success

    # ===== EXPORT =====
    def test_export_csv(self):
        """Test POST /api/v1/export/csv (auth + pro required)."""
        if not self.token:
            self.log("⚠️  Skipping CSV export - no token", "WARN")
            return False
        
        success, response = self.run_test(
            "Export CSV",
            "POST",
            "/api/v1/export/csv",
            200,
            data={"city": ["Mumbai"], "limit": 10}
        )
        if success:
            self.log(f"   CSV export returned {len(response) if isinstance(response, bytes) else 'data'} bytes")
        return success

    def test_export_excel(self):
        """Test POST /api/v1/export/excel (auth + pro required)."""
        if not self.token:
            self.log("⚠️  Skipping Excel export - no token", "WARN")
            return False
        
        success, response = self.run_test(
            "Export Excel",
            "POST",
            "/api/v1/export/excel",
            200,
            data={"city": ["Mumbai"], "limit": 10}
        )
        if success:
            self.log(f"   Excel export returned {len(response) if isinstance(response, bytes) else 'data'} bytes")
        return success

    def test_export_pdf(self):
        """Test POST /api/v1/export/pdf (auth + pro required)."""
        if not self.token:
            self.log("⚠️  Skipping PDF export - no token", "WARN")
            return False
        
        success, response = self.run_test(
            "Export PDF",
            "POST",
            "/api/v1/export/pdf",
            200,
            data={"city": ["Mumbai"], "limit": 10}
        )
        if success:
            self.log(f"   PDF export returned {len(response) if isinstance(response, bytes) else 'data'} bytes")
        return success

    # ===== ALERTS =====
    def test_alerts_create(self):
        """Test POST /api/v1/alerts (auth required)."""
        if not self.token:
            self.log("⚠️  Skipping create alert - no token", "WARN")
            return False
        
        success, response = self.run_test(
            "Create Alert",
            "POST",
            "/api/v1/alerts",
            200,
            data={
                "name": "Test Alert",
                "cities": ["Mumbai"],
                "sectors": ["Technology"],
                "min_capital": 1000000,
                "frequency": "daily"
            },
            check_response=lambda r: 'alert' in r and 'id' in r.get('alert', {})
        )
        if success and response.get('alert'):
            self.test_alert_id = response['alert'].get('id')
            self.log(f"   Alert created with ID: {self.test_alert_id}")
        return success

    def test_alerts_list(self):
        """Test GET /api/v1/alerts (auth required)."""
        if not self.token:
            self.log("⚠️  Skipping list alerts - no token", "WARN")
            return False
        
        success, response = self.run_test(
            "List Alerts",
            "GET",
            "/api/v1/alerts",
            200,
            check_response=lambda r: 'alerts' in r
        )
        return success

    def test_alerts_toggle(self):
        """Test PATCH /api/v1/alerts/{id}/toggle (auth required)."""
        if not self.token or not self.test_alert_id:
            self.log("⚠️  Skipping toggle alert - no token or alert ID", "WARN")
            return False
        
        success, response = self.run_test(
            "Toggle Alert",
            "PATCH",
            f"/api/v1/alerts/{self.test_alert_id}/toggle",
            200,
            check_response=lambda r: 'alerts' in r
        )
        return success

    def test_alerts_delete(self):
        """Test DELETE /api/v1/alerts/{id} (auth required)."""
        if not self.token or not self.test_alert_id:
            self.log("⚠️  Skipping delete alert - no token or alert ID", "WARN")
            return False
        
        success, response = self.run_test(
            "Delete Alert",
            "DELETE",
            f"/api/v1/alerts/{self.test_alert_id}",
            200
        )
        return success

    # ===== ADMIN =====
    def test_admin_stats(self):
        """Test GET /api/v1/admin/stats."""
        success, response = self.run_test(
            "Admin Stats",
            "GET",
            "/api/v1/admin/stats",
            200,
            check_response=lambda r: 'companies' in r and 'data_sources' in r
        )
        return success

    def test_admin_ingest_seed(self):
        """Test POST /api/v1/admin/ingest/seed."""
        success, response = self.run_test(
            "Admin Ingest Seed",
            "POST",
            "/api/v1/admin/ingest/seed?count=10",
            200,
            check_response=lambda r: 'mode' in r
        )
        return success

    def test_admin_enrichment_progress(self):
        """Test GET /api/v1/admin/enrichment-progress (NEW MCA enrichment dashboard endpoint)."""
        success, response = self.run_test(
            "Admin Enrichment Progress",
            "GET",
            "/api/v1/admin/enrichment-progress",
            200,
            check_response=lambda r: (
                'progress' in r and
                'governance' in r and
                'commands' in r and
                'cohort_description' in r and
                r['progress'].get('total') is not None and
                r['progress'].get('enriched') is not None and
                r['progress'].get('remaining') is not None and
                r['progress'].get('not_yet_attempted') is not None and
                r['progress'].get('attempted_failed') is not None and
                r['progress'].get('permanently_failed') is not None and
                r['progress'].get('progress_pct') is not None and
                r['governance'].get('sessions_today') is not None and
                r['governance'].get('max_sessions_per_day') == 3 and
                r['governance'].get('min_gap_hours') == 3 and
                r['governance'].get('batch_size') == 400 and
                r['governance'].get('time_budget_minutes') == 110 and
                r['governance'].get('max_consecutive_failures') == 5 and
                r['governance'].get('can_start_now') is not None and
                r['governance'].get('auto_enrichment_disabled') == True and
                'run_session' in r['commands'] and
                'retry_failed' in r['commands'] and
                'set_cookie' in r['commands']
            )
        )
        if success:
            self.log(f"   Progress: {response['progress']['enriched']}/{response['progress']['total']} enriched ({response['progress']['progress_pct']}%)")
            self.log(f"   Sessions today: {response['governance']['sessions_today']}/{response['governance']['max_sessions_per_day']}")
            self.log(f"   Can start now: {response['governance']['can_start_now']}")
            self.log(f"   Auto enrichment disabled: {response['governance']['auto_enrichment_disabled']}")
        return success

    # ===== PAYMENTS =====
    def test_payments_plans(self):
        """Test GET /api/v1/payments/plans."""
        success, response = self.run_test(
            "Get Payment Plans",
            "GET",
            "/api/v1/payments/plans",
            200,
            check_response=lambda r: 'plans' in r and 'configured' in r
        )
        return success

    def test_payments_checkout(self):
        """Test POST /api/v1/payments/checkout (auth required)."""
        if not self.token:
            self.log("⚠️  Skipping checkout - no token", "WARN")
            return False
        
        success, response = self.run_test(
            "Create Checkout Session",
            "POST",
            "/api/v1/payments/checkout",
            200,
            data={
                "plan_id": "pro",
                "origin_url": "https://corp-intel-india.preview.emergentagent.com"
            },
            check_response=lambda r: 'url' in r and 'session_id' in r
        )
        if success:
            self.log(f"   Checkout URL: {response.get('url', '')[:80]}...")
        return success

    # ===== RUN ALL TESTS =====
    def run_all_tests(self):
        """Run all backend tests in sequence."""
        self.log("\n" + "="*80)
        self.log("CORPINTEL INDIA - BACKEND API TEST SUITE")
        self.log("="*80)
        
        # Health
        self.log("\n--- HEALTH & META ---")
        self.test_health()
        
        # Auth
        self.log("\n--- AUTHENTICATION ---")
        self.test_demo_login()
        self.test_register()
        self.test_login()
        self.test_auth_me()
        
        # Companies
        self.log("\n--- COMPANIES ---")
        self.test_list_companies()
        self.test_company_detail()
        self.test_company_directors()
        self.test_company_charges()
        self.test_company_filings()
        self.test_company_similar()
        self.test_company_contact_locked()
        self.test_company_contact_unlocked()
        
        # Analytics
        self.log("\n--- ANALYTICS ---")
        self.test_analytics_summary()
        self.test_analytics_trends()
        self.test_analytics_sectors()
        self.test_analytics_capital()
        self.test_analytics_heatmap()
        
        # Search
        self.log("\n--- SEARCH ---")
        self.test_search_quick()
        self.test_search_advanced()
        self.test_search_save()
        self.test_search_saved_list()
        
        # Export
        self.log("\n--- EXPORT ---")
        self.test_export_csv()
        self.test_export_excel()
        self.test_export_pdf()
        
        # Alerts
        self.log("\n--- ALERTS ---")
        self.test_alerts_create()
        self.test_alerts_list()
        self.test_alerts_toggle()
        self.test_alerts_delete()
        
        # Admin
        self.log("\n--- ADMIN ---")
        self.test_admin_stats()
        self.test_admin_ingest_seed()
        self.test_admin_enrichment_progress()
        
        # Payments
        self.log("\n--- PAYMENTS ---")
        self.test_payments_plans()
        self.test_payments_checkout()
        
        # Summary
        self.log("\n" + "="*80)
        self.log("TEST SUMMARY")
        self.log("="*80)
        self.log(f"Total Tests: {self.tests_run}")
        self.log(f"Passed: {self.tests_passed}")
        self.log(f"Failed: {self.tests_run - self.tests_passed}")
        self.log(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.failed_tests:
            self.log("\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                self.log(f"  {i}. {test}")
        
        return 0 if self.tests_passed == self.tests_run else 1


def main():
    tester = CorpIntelAPITester()
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())
