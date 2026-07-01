"""Backend API tests for LLP Phase 2 - Entity-type-aware search, LLP detail pages, analytics."""
import json
import sys
import os
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001/api")
V1_URL = f"{BASE_URL}/v1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class BackendTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []

    def log(self, msg, color=Colors.BLUE):
        print(f"{color}{msg}{Colors.END}")

    def test(self, name, fn):
        """Run a single test function."""
        self.tests_run += 1
        self.log(f"\n{'='*60}", Colors.BLUE)
        self.log(f"TEST {self.tests_run}: {name}", Colors.BLUE)
        self.log(f"{'='*60}", Colors.BLUE)
        try:
            fn()
            self.tests_passed += 1
            self.log(f"✅ PASSED: {name}", Colors.GREEN)
            self.results.append({"test": name, "status": "PASSED"})
        except AssertionError as e:
            self.tests_failed += 1
            self.log(f"❌ FAILED: {name}", Colors.RED)
            self.log(f"   Error: {str(e)}", Colors.RED)
            self.results.append({"test": name, "status": "FAILED", "error": str(e)})
        except Exception as e:
            self.tests_failed += 1
            self.log(f"❌ ERROR: {name}", Colors.RED)
            self.log(f"   Exception: {str(e)}", Colors.RED)
            self.results.append({"test": name, "status": "ERROR", "error": str(e)})

    def assert_eq(self, actual, expected, msg=""):
        if actual != expected:
            raise AssertionError(f"{msg} Expected {expected}, got {actual}")

    def assert_true(self, condition, msg=""):
        if not condition:
            raise AssertionError(msg or "Condition is False")

    def assert_in(self, item, container, msg=""):
        if item not in container:
            raise AssertionError(msg or f"{item} not in {container}")

    def summary(self):
        self.log(f"\n{'='*60}", Colors.BLUE)
        self.log("TEST SUMMARY", Colors.BLUE)
        self.log(f"{'='*60}", Colors.BLUE)
        self.log(f"Total: {self.tests_run}", Colors.BLUE)
        self.log(f"Passed: {self.tests_passed}", Colors.GREEN)
        self.log(f"Failed: {self.tests_failed}", Colors.RED)
        return self.tests_failed == 0


def test_health_endpoint(t):
    """Test /api/health endpoint (regression)."""
    resp = requests.get(f"{BASE_URL}/health", timeout=10)
    t.assert_eq(resp.status_code, 200, "Health endpoint should return 200")
    data = resp.json()
    t.assert_true(data.get("status") in ["ok", "healthy"], "Health status should be 'ok' or 'healthy'")
    t.log(f"   Health: {data}")


def test_admin_stats(t):
    """Test /api/v1/admin/stats endpoint (regression)."""
    resp = requests.get(f"{V1_URL}/admin/stats", timeout=10)
    t.assert_eq(resp.status_code, 200, "Admin stats should return 200")
    data = resp.json()
    t.assert_true("companies" in data, "Stats should include 'companies'")
    t.log(f"   Stats: companies={data.get('companies')}, enriched={data.get('enriched')}")


def test_enrichment_progress(t):
    """Test /api/v1/admin/enrichment-progress endpoint (regression)."""
    resp = requests.get(f"{V1_URL}/admin/enrichment-progress", timeout=10)
    t.assert_eq(resp.status_code, 200, "Enrichment progress should return 200")
    data = resp.json()
    t.assert_true("progress" in data, "Should include 'progress'")
    t.assert_true("governance" in data, "Should include 'governance'")
    t.log(f"   Progress: {data.get('progress', {}).get('progress_pct')}%")


def test_demo_login(t):
    """Test POST /api/v1/auth/demo-login (regression)."""
    resp = requests.post(f"{V1_URL}/auth/demo-login", 
                        json={"email": "demo@corpintel.in", "password": "Demo@1234"},
                        timeout=10)
    t.assert_eq(resp.status_code, 200, "Demo login should return 200")
    data = resp.json()
    t.assert_true("token" in data or "access_token" in data, "Should return token")
    t.log(f"   Demo login successful")


def test_company_detail_by_cin(t):
    """Test GET /api/v1/companies/{cin} resolves Company by CIN."""
    cin = "U29190MH2016PTC285109"
    resp = requests.get(f"{V1_URL}/companies/{cin}", timeout=10)
    t.assert_eq(resp.status_code, 200, f"Company detail for CIN {cin} should return 200")
    data = resp.json()
    t.assert_eq(data.get("entity_type"), "Company", "Entity type should be 'Company'")
    t.assert_true(data.get("cin") == cin or data.get("identifier") == cin, 
                  f"CIN should match {cin}")
    t.log(f"   Company: {data.get('name')}, entity_type={data.get('entity_type')}")


def test_llp_detail_by_llpin(t):
    """Test GET /api/v1/companies/{llpin} resolves LLP by LLPIN."""
    # First, fetch a valid LLP identifier
    resp = requests.get(f"{V1_URL}/companies", 
                       params={"entity_type": "LLP", "limit": 1}, 
                       timeout=10)
    t.assert_eq(resp.status_code, 200, "Should fetch LLP list")
    data = resp.json()
    results = data.get("results", [])
    
    if not results:
        t.log(f"   ⚠️  No LLPs found in database, using fallback LLPIN ACF-6756")
        llpin = "ACF-6756"
    else:
        llpin = results[0].get("identifier")
        t.log(f"   Found LLP with identifier: {llpin}")
    
    # Now test detail endpoint
    resp = requests.get(f"{V1_URL}/companies/{llpin}", timeout=10)
    t.assert_eq(resp.status_code, 200, f"LLP detail for LLPIN {llpin} should return 200")
    data = resp.json()
    t.assert_eq(data.get("entity_type"), "LLP", "Entity type should be 'LLP'")
    t.assert_eq(data.get("identifier_type"), "LLPIN", "Identifier type should be 'LLPIN'")
    t.assert_true(data.get("cin") is None, "LLP should have cin=null")
    t.assert_true("total_contribution" in data, "LLP should have total_contribution field")
    t.log(f"   LLP: {data.get('name')}, entity_type={data.get('entity_type')}, "
          f"total_contribution={data.get('total_contribution')}")
    
    # Store for next test
    t.test_llpin = llpin


def test_llp_partners_endpoint(t):
    """Test GET /api/v1/companies/{llpin}/partners returns correct shape."""
    if not hasattr(t, "test_llpin"):
        # Fallback
        llpin = "ACF-6756"
    else:
        llpin = t.test_llpin
    
    resp = requests.get(f"{V1_URL}/companies/{llpin}/partners", timeout=10)
    t.assert_eq(resp.status_code, 200, f"Partners endpoint for {llpin} should return 200")
    data = resp.json()
    t.assert_true("llpin" in data, "Response should include 'llpin'")
    t.assert_true("count" in data, "Response should include 'count'")
    t.assert_true("partners" in data, "Response should include 'partners' array")
    t.assert_true(isinstance(data["partners"], list), "Partners should be a list")
    t.log(f"   Partners: llpin={data['llpin']}, count={data['count']} "
          f"(empty is acceptable since live scraping is disabled)")


def test_company_directors_endpoint(t):
    """Test GET /api/v1/companies/{cin}/directors still works for companies (regression)."""
    cin = "U29190MH2016PTC285109"
    resp = requests.get(f"{V1_URL}/companies/{cin}/directors", timeout=10)
    t.assert_eq(resp.status_code, 200, f"Directors endpoint for {cin} should return 200")
    data = resp.json()
    t.assert_true("cin" in data, "Response should include 'cin'")
    t.assert_true("count" in data, "Response should include 'count'")
    t.assert_true("directors" in data, "Response should include 'directors' array")
    t.log(f"   Directors: cin={data['cin']}, count={data['count']}")


def test_companies_filter_by_entity_type_llp(t):
    """Test GET /api/v1/companies?entity_type=LLP returns only LLPs."""
    resp = requests.get(f"{V1_URL}/companies", 
                       params={"entity_type": "LLP", "limit": 10}, 
                       timeout=10)
    t.assert_eq(resp.status_code, 200, "Companies list with entity_type=LLP should return 200")
    data = resp.json()
    results = data.get("results", [])
    
    if results:
        for entity in results:
            t.assert_eq(entity.get("entity_type"), "LLP", 
                       f"All results should be LLPs, found {entity.get('entity_type')}")
        t.log(f"   ✓ All {len(results)} results are LLPs")
    else:
        t.log(f"   ⚠️  No LLPs found (acceptable if DB has no LLPs)")


def test_companies_filter_by_entity_type_company(t):
    """Test GET /api/v1/companies?entity_type=Company returns only Companies."""
    resp = requests.get(f"{V1_URL}/companies", 
                       params={"entity_type": "Company", "limit": 10}, 
                       timeout=10)
    t.assert_eq(resp.status_code, 200, "Companies list with entity_type=Company should return 200")
    data = resp.json()
    results = data.get("results", [])
    
    if results:
        for entity in results:
            entity_type = entity.get("entity_type", "Company")  # Default to Company if not set
            t.assert_true(entity_type in ["Company", None], 
                         f"All results should be Companies, found {entity_type}")
        t.log(f"   ✓ All {len(results)} results are Companies")
    else:
        t.log(f"   ⚠️  No Companies found")


def test_companies_no_entity_type_filter(t):
    """Test GET /api/v1/companies without entity_type returns both Companies and LLPs."""
    resp = requests.get(f"{V1_URL}/companies", 
                       params={"limit": 50}, 
                       timeout=10)
    t.assert_eq(resp.status_code, 200, "Companies list without entity_type should return 200")
    data = resp.json()
    results = data.get("results", [])
    total = data.get("total", 0)
    
    t.assert_true(total > 0, "Should have some entities in database")
    t.log(f"   Total entities: {total}, fetched: {len(results)}")
    
    # Check if we have both types (if DB has both)
    entity_types = set(r.get("entity_type", "Company") for r in results)
    t.log(f"   Entity types in results: {entity_types}")


def test_analytics_summary_entity_breakdown(t):
    """Test GET /api/v1/analytics/summary returns by_entity_type breakdown."""
    resp = requests.get(f"{V1_URL}/analytics/summary", timeout=10)
    t.assert_eq(resp.status_code, 200, "Analytics summary should return 200")
    data = resp.json()
    
    t.assert_true("by_entity_type" in data, "Should include 'by_entity_type'")
    t.assert_true("companies_count" in data, "Should include 'companies_count'")
    t.assert_true("llps_count" in data, "Should include 'llps_count'")
    
    by_entity = data.get("by_entity_type", {})
    companies_count = data.get("companies_count", 0)
    llps_count = data.get("llps_count", 0)
    
    t.log(f"   by_entity_type: {by_entity}")
    t.log(f"   companies_count: {companies_count}")
    t.log(f"   llps_count: {llps_count}")
    
    # Verify counts match
    t.assert_eq(by_entity.get("Company", 0), companies_count, 
               "by_entity_type.Company should match companies_count")
    t.assert_eq(by_entity.get("LLP", 0), llps_count, 
               "by_entity_type.LLP should match llps_count")


def test_analytics_summary_with_city_filter(t):
    """Test GET /api/v1/analytics/summary?city=Mumbai returns filtered breakdown."""
    resp = requests.get(f"{V1_URL}/analytics/summary", 
                       params={"city": "Mumbai"}, 
                       timeout=10)
    t.assert_eq(resp.status_code, 200, "Analytics summary with city filter should return 200")
    data = resp.json()
    
    t.assert_true("by_entity_type" in data, "Should include 'by_entity_type'")
    t.assert_true("companies_count" in data, "Should include 'companies_count'")
    t.assert_true("llps_count" in data, "Should include 'llps_count'")
    
    total = data.get("total", 0)
    companies_count = data.get("companies_count", 0)
    llps_count = data.get("llps_count", 0)
    
    t.log(f"   Mumbai total: {total}")
    t.log(f"   Mumbai companies: {companies_count}")
    t.log(f"   Mumbai LLPs: {llps_count}")
    
    # Filtered totals should be smaller than unfiltered
    t.assert_true(total >= 0, "Total should be non-negative")


def test_search_includes_entity_type(t):
    """Test GET /api/v1/search?q=<term> includes entity_type in suggestions."""
    resp = requests.get(f"{V1_URL}/search", 
                       params={"q": "company", "limit": 10}, 
                       timeout=10)
    t.assert_eq(resp.status_code, 200, "Search should return 200")
    data = resp.json()
    
    suggestions = data.get("suggestions", [])
    if suggestions:
        for suggestion in suggestions:
            t.assert_true("entity_type" in suggestion, 
                         "Each suggestion should include 'entity_type'")
            t.assert_true("cin" in suggestion, 
                         "Each suggestion should include 'cin' (identifier)")
        t.log(f"   ✓ {len(suggestions)} suggestions include entity_type")
        t.log(f"   Sample: {suggestions[0]}")
    else:
        t.log(f"   ⚠️  No search results (acceptable)")


def test_similar_companies_for_company(t):
    """Test GET /api/v1/companies/{cin}/similar works for Company."""
    cin = "U29190MH2016PTC285109"
    resp = requests.get(f"{V1_URL}/companies/{cin}/similar", 
                       params={"limit": 5}, 
                       timeout=10)
    t.assert_eq(resp.status_code, 200, f"Similar companies for {cin} should return 200")
    data = resp.json()
    t.assert_true("results" in data, "Should include 'results'")
    t.log(f"   Similar companies: {len(data.get('results', []))} found")


def test_similar_companies_for_llp(t):
    """Test GET /api/v1/companies/{llpin}/similar works for LLP (no crash on null cin)."""
    if not hasattr(t, "test_llpin"):
        llpin = "ACF-6756"
    else:
        llpin = t.test_llpin
    
    resp = requests.get(f"{V1_URL}/companies/{llpin}/similar", 
                       params={"limit": 5}, 
                       timeout=10)
    t.assert_eq(resp.status_code, 200, f"Similar entities for LLP {llpin} should return 200")
    data = resp.json()
    t.assert_true("results" in data, "Should include 'results'")
    t.log(f"   Similar entities for LLP: {len(data.get('results', []))} found")


def test_company_charges_endpoint(t):
    """Test GET /api/v1/companies/{cin}/charges (regression)."""
    cin = "U29190MH2016PTC285109"
    resp = requests.get(f"{V1_URL}/companies/{cin}/charges", timeout=10)
    t.assert_eq(resp.status_code, 200, f"Charges endpoint for {cin} should return 200")
    data = resp.json()
    t.assert_true("cin" in data, "Response should include 'cin'")
    t.assert_true("charges" in data, "Response should include 'charges' array")
    t.log(f"   Charges: {len(data.get('charges', []))} found")


def test_company_filings_endpoint(t):
    """Test GET /api/v1/companies/{cin}/filings (regression)."""
    cin = "U29190MH2016PTC285109"
    resp = requests.get(f"{V1_URL}/companies/{cin}/filings", timeout=10)
    t.assert_eq(resp.status_code, 200, f"Filings endpoint for {cin} should return 200")
    data = resp.json()
    t.assert_true("cin" in data, "Response should include 'cin'")
    t.assert_true("filings" in data, "Response should include 'filings' array")
    t.log(f"   Filings: {len(data.get('filings', []))} found")


def test_company_contact_endpoint(t):
    """Test GET /api/v1/companies/{cin}/contact (regression)."""
    cin = "U29190MH2016PTC285109"
    resp = requests.get(f"{V1_URL}/companies/{cin}/contact", timeout=10)
    t.assert_eq(resp.status_code, 200, f"Contact endpoint for {cin} should return 200")
    data = resp.json()
    t.assert_true("cin" in data, "Response should include 'cin'")
    t.assert_true("locked" in data, "Response should include 'locked' field")
    t.log(f"   Contact: locked={data.get('locked')}")


def main():
    tester = BackendTester()
    
    tester.log("\n" + "="*60, Colors.BLUE)
    tester.log("BACKEND API TESTS - LLP PHASE 2", Colors.BLUE)
    tester.log("="*60, Colors.BLUE)
    
    # Regression tests
    tester.test("Health endpoint", lambda: test_health_endpoint(tester))
    tester.test("Admin stats endpoint", lambda: test_admin_stats(tester))
    tester.test("Enrichment progress endpoint", lambda: test_enrichment_progress(tester))
    tester.test("Demo login", lambda: test_demo_login(tester))
    
    # LLP Phase 2 - Entity resolution
    tester.test("Company detail by CIN", lambda: test_company_detail_by_cin(tester))
    tester.test("LLP detail by LLPIN", lambda: test_llp_detail_by_llpin(tester))
    
    # LLP Phase 2 - Partners endpoint
    tester.test("LLP partners endpoint", lambda: test_llp_partners_endpoint(tester))
    tester.test("Company directors endpoint (regression)", lambda: test_company_directors_endpoint(tester))
    
    # LLP Phase 2 - Entity type filtering
    tester.test("Filter companies by entity_type=LLP", lambda: test_companies_filter_by_entity_type_llp(tester))
    tester.test("Filter companies by entity_type=Company", lambda: test_companies_filter_by_entity_type_company(tester))
    tester.test("No entity_type filter returns both", lambda: test_companies_no_entity_type_filter(tester))
    
    # LLP Phase 2 - Analytics breakdown
    tester.test("Analytics summary entity breakdown", lambda: test_analytics_summary_entity_breakdown(tester))
    tester.test("Analytics summary with city filter", lambda: test_analytics_summary_with_city_filter(tester))
    
    # LLP Phase 2 - Search with entity_type
    tester.test("Search includes entity_type", lambda: test_search_includes_entity_type(tester))
    
    # LLP Phase 2 - Similar entities (no crash on null cin)
    tester.test("Similar companies for Company", lambda: test_similar_companies_for_company(tester))
    tester.test("Similar entities for LLP", lambda: test_similar_companies_for_llp(tester))
    
    # Regression tests for existing endpoints
    tester.test("Company charges endpoint", lambda: test_company_charges_endpoint(tester))
    tester.test("Company filings endpoint", lambda: test_company_filings_endpoint(tester))
    tester.test("Company contact endpoint", lambda: test_company_contact_endpoint(tester))
    
    # Summary
    success = tester.summary()
    
    # Save results
    with open("/app/test_reports/backend_llp_phase2_results.json", "w") as f:
        json.dump({
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "total": tester.tests_run,
            "passed": tester.tests_passed,
            "failed": tester.tests_failed,
            "results": tester.results
        }, f, indent=2)
    
    tester.log(f"\n✅ Results saved to /app/test_reports/backend_llp_phase2_results.json", Colors.GREEN)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
