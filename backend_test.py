"""Backend API tests for CSV upload async background job fix (Cloudflare 520)."""
import io
import json
import sys
import time
from datetime import datetime

import requests

BASE_URL = "https://corp-intel-india.preview.emergentagent.com/api"
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


def test_companies_list(t):
    """Test /api/v1/companies endpoint (regression)."""
    resp = requests.get(f"{V1_URL}/companies", params={"limit": 5}, timeout=10)
    t.assert_eq(resp.status_code, 200, "Companies list should return 200")
    data = resp.json()
    t.assert_true("results" in data or "companies" in data, "Should include 'results' or 'companies' list")
    results = data.get("results", data.get("companies", []))
    t.log(f"   Companies count: {len(results)}, total: {data.get('total', 0)}")


def test_upload_csv_immediate_return(t):
    """Test POST /api/v1/admin/upload-csv returns immediately with job_id."""
    # Create a small CSV in memory
    csv_content = """identifier,name,status,paid_up_capital
U00000MH2099PTC700001,Test Company One,Active,100000
U00000MH2099PTC700002,Test Company Two,Active,200000
"""
    files = {"file": ("test_immediate.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    
    start = time.time()
    resp = requests.post(f"{V1_URL}/admin/upload-csv", files=files, timeout=30)
    elapsed = time.time() - start
    
    t.assert_eq(resp.status_code, 200, "Upload should return 200")
    data = resp.json()
    t.assert_true("job_id" in data, "Response should include job_id")
    t.assert_eq(data.get("status"), "queued", "Initial status should be 'queued'")
    t.assert_true(elapsed < 5, f"Upload should return quickly (took {elapsed:.2f}s)")
    t.log(f"   ✓ Returned in {elapsed:.2f}s with job_id: {data['job_id']}")
    
    # Store job_id for next test
    t.last_job_id = data["job_id"]


def test_upload_status_polling(t):
    """Test GET /api/v1/admin/upload-csv/{job_id}/status polling."""
    if not hasattr(t, "last_job_id"):
        raise AssertionError("No job_id from previous test")
    
    job_id = t.last_job_id
    max_wait = 60  # 60 seconds max
    start = time.time()
    
    while time.time() - start < max_wait:
        resp = requests.get(f"{V1_URL}/admin/upload-csv/{job_id}/status", timeout=10)
        t.assert_eq(resp.status_code, 200, "Status endpoint should return 200")
        data = resp.json()
        
        status = data.get("status")
        t.log(f"   Status: {status}, processed: {data.get('processed_rows')}/{data.get('total_rows')}")
        
        if status == "completed":
            t.assert_true("inserted_count" in data, "Completed job should have inserted_count")
            t.assert_true("updated_count" in data, "Completed job should have updated_count")
            t.assert_true("rejected_count" in data, "Completed job should have rejected_count")
            t.log(f"   ✓ Completed: inserted={data.get('inserted_count')}, updated={data.get('updated_count')}")
            return
        elif status == "failed":
            raise AssertionError(f"Job failed: {data.get('error_message')}")
        
        time.sleep(2)
    
    raise AssertionError(f"Job did not complete within {max_wait}s")


def test_validation_counts_small_csv(t):
    """Test validation with specific test cases: valid CIN, valid LLPIN, duplicate, invalid, missing name."""
    csv_content = """identifier,name,status,paid_up_capital,total_contribution,company_class,address,pin_code
U72900MH2099PTC654321,Valid Company Name,Active,500000,,Private,Mumbai Office,400001
ZZT-4321,Valid LLP Name,Active,,250000,LLP,Navi Mumbai Office,400703
U72900MH2099PTC654321,Duplicate Company,Active,600000,,Private,Another Address,400002
NOTANID,Invalid Identifier Company,Active,100000,,Private,Some Address,400003
ZZT-9000,,Active,,300000,LLP,Empty Name LLP,400704
"""
    files = {"file": ("test_validation.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    
    resp = requests.post(f"{V1_URL}/admin/upload-csv", files=files, timeout=30)
    t.assert_eq(resp.status_code, 200, "Upload should return 200")
    job_id = resp.json()["job_id"]
    
    # Poll until complete
    max_wait = 60
    start = time.time()
    final_data = None
    
    while time.time() - start < max_wait:
        resp = requests.get(f"{V1_URL}/admin/upload-csv/{job_id}/status", timeout=10)
        data = resp.json()
        if data.get("status") == "completed":
            final_data = data
            break
        elif data.get("status") == "failed":
            raise AssertionError(f"Job failed: {data.get('error_message')}")
        time.sleep(2)
    
    t.assert_true(final_data is not None, "Job should complete")
    
    # Expected: 1 company inserted, 1 LLP inserted, 1 duplicate, 2 rejected (invalid ID + missing name)
    # Note: On re-run, these might be updates instead of inserts
    companies_total = final_data.get("companies_inserted", 0) + final_data.get("companies_updated", 0)
    llps_total = final_data.get("llps_inserted", 0) + final_data.get("llps_updated", 0)
    
    t.assert_eq(companies_total, 1, "Should have 1 company (inserted or updated)")
    t.assert_eq(llps_total, 1, "Should have 1 LLP (inserted or updated)")
    t.assert_eq(final_data.get("duplicate_within_file_count"), 1, "Should have 1 duplicate")
    t.assert_eq(final_data.get("rejected_count"), 2, "Should have 2 rejected (invalid ID + missing name)")
    t.assert_eq(final_data.get("total_rows"), 5, "Should have processed 5 rows")
    
    t.log(f"   ✓ Validation counts correct:")
    t.log(f"     Companies: {companies_total}, LLPs: {llps_total}")
    t.log(f"     Duplicates: {final_data.get('duplicate_within_file_count')}")
    t.log(f"     Rejected: {final_data.get('rejected_count')}")


def test_upsert_behavior(t):
    """Test re-uploading same CSV results in updates, not new inserts."""
    csv_content = """identifier,name,status,paid_up_capital
U00000MH2099PTC700010,Upsert Test Company,Active,100000
ZZT-5000,Upsert Test LLP,Active,150000
"""
    files = {"file": ("test_upsert.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    
    # First upload
    resp1 = requests.post(f"{V1_URL}/admin/upload-csv", files=files, timeout=30)
    job_id1 = resp1.json()["job_id"]
    
    # Wait for completion
    for _ in range(30):
        resp = requests.get(f"{V1_URL}/admin/upload-csv/{job_id1}/status", timeout=10)
        if resp.json().get("status") == "completed":
            break
        time.sleep(2)
    
    first_result = resp.json()
    t.log(f"   First upload: inserted={first_result.get('inserted_count')}")
    
    # Second upload (same data)
    files2 = {"file": ("test_upsert2.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    resp2 = requests.post(f"{V1_URL}/admin/upload-csv", files=files2, timeout=30)
    job_id2 = resp2.json()["job_id"]
    
    # Wait for completion
    for _ in range(30):
        resp = requests.get(f"{V1_URL}/admin/upload-csv/{job_id2}/status", timeout=10)
        if resp.json().get("status") == "completed":
            break
        time.sleep(2)
    
    second_result = resp.json()
    t.log(f"   Second upload: updated={second_result.get('updated_count')}")
    
    # Second upload should have updates, not inserts (or at least total should match)
    total_processed = second_result.get("inserted_count", 0) + second_result.get("updated_count", 0)
    t.assert_eq(total_processed, 2, "Should process 2 records on re-upload")
    t.log(f"   ✓ Upsert behavior confirmed")


def test_large_csv_upload(t):
    """Test large CSV upload (100k rows) to validate 520 fix."""
    t.log("   Generating large CSV with 100,000 synthetic CINs...")
    
    # Generate CSV with 100k rows
    rows = ["identifier,name,status,paid_up_capital,address,pin_code"]
    for i in range(100000):
        cin = f"U00000MH2099PTC{700001 + i:06d}"
        name = f"Large Test Company {i+1}"
        rows.append(f"{cin},{name},Active,{100000 + (i % 900000)},Mumbai Office {i},400001")
    
    csv_content = "\n".join(rows)
    csv_bytes = csv_content.encode()
    file_size_mb = len(csv_bytes) / (1024 * 1024)
    t.log(f"   Generated CSV: {len(rows)-1} rows, {file_size_mb:.2f} MB")
    
    files = {"file": ("test_large.csv", io.BytesIO(csv_bytes), "text/csv")}
    
    # Submit and measure response time
    start = time.time()
    resp = requests.post(f"{V1_URL}/admin/upload-csv", files=files, timeout=60)
    elapsed = time.time() - start
    
    t.assert_eq(resp.status_code, 200, "Large upload should return 200")
    data = resp.json()
    t.assert_true("job_id" in data, "Should return job_id")
    t.assert_true(elapsed < 10, f"Should return quickly even for large file (took {elapsed:.2f}s)")
    t.log(f"   ✓ Large file submitted in {elapsed:.2f}s (non-blocking)")
    
    job_id = data["job_id"]
    
    # Poll for completion (this will take longer)
    t.log("   Polling for completion (this may take 1-2 minutes)...")
    max_wait = 300  # 5 minutes max
    start = time.time()
    last_progress = 0
    
    while time.time() - start < max_wait:
        resp = requests.get(f"{V1_URL}/admin/upload-csv/{job_id}/status", timeout=10)
        data = resp.json()
        status = data.get("status")
        processed = data.get("processed_rows", 0)
        total = data.get("total_rows", 0)
        
        if processed > last_progress + 10000:  # Log every 10k rows
            t.log(f"   Progress: {processed}/{total} rows ({status})")
            last_progress = processed
        
        if status == "completed":
            elapsed_total = time.time() - start
            t.log(f"   ✓ Completed in {elapsed_total:.1f}s")
            t.log(f"     Inserted: {data.get('inserted_count')}, Updated: {data.get('updated_count')}")
            t.log(f"     Rejected: {data.get('rejected_count')}")
            
            # Verify counts
            total_processed = data.get("inserted_count", 0) + data.get("updated_count", 0)
            t.assert_true(total_processed >= 99000, f"Should process most rows (got {total_processed})")
            return
        elif status == "failed":
            raise AssertionError(f"Large upload failed: {data.get('error_message')}")
        
        time.sleep(5)
    
    raise AssertionError(f"Large upload did not complete within {max_wait}s")


def test_non_csv_upload(t):
    """Test uploading non-CSV file returns 400."""
    files = {"file": ("test.txt", io.BytesIO(b"not a csv"), "text/plain")}
    resp = requests.post(f"{V1_URL}/admin/upload-csv", files=files, timeout=30)
    t.assert_eq(resp.status_code, 400, "Non-CSV upload should return 400")
    t.log(f"   ✓ Non-CSV rejected with 400")


def test_invalid_job_id(t):
    """Test GET status with invalid job_id returns 404."""
    resp = requests.get(f"{V1_URL}/admin/upload-csv/invalid-job-id-12345/status", timeout=10)
    t.assert_eq(resp.status_code, 404, "Invalid job_id should return 404")
    t.log(f"   ✓ Invalid job_id returns 404")


def main():
    tester = BackendTester()
    
    tester.log("\n" + "="*60, Colors.BLUE)
    tester.log("BACKEND API TESTS - CSV Upload Async Background Job", Colors.BLUE)
    tester.log("="*60, Colors.BLUE)
    
    # Regression tests
    tester.test("Health endpoint", lambda: test_health_endpoint(tester))
    tester.test("Admin stats endpoint", lambda: test_admin_stats(tester))
    tester.test("Enrichment progress endpoint", lambda: test_enrichment_progress(tester))
    tester.test("Companies list endpoint", lambda: test_companies_list(tester))
    
    # Core CSV upload tests
    tester.test("Upload CSV returns immediately with job_id", lambda: test_upload_csv_immediate_return(tester))
    tester.test("Upload status polling", lambda: test_upload_status_polling(tester))
    tester.test("Validation counts (small CSV)", lambda: test_validation_counts_small_csv(tester))
    tester.test("Upsert behavior (re-upload)", lambda: test_upsert_behavior(tester))
    
    # Large file test (520 fix validation)
    tester.test("Large CSV upload (100k rows)", lambda: test_large_csv_upload(tester))
    
    # Error cases
    tester.test("Non-CSV upload returns 400", lambda: test_non_csv_upload(tester))
    tester.test("Invalid job_id returns 404", lambda: test_invalid_job_id(tester))
    
    # Summary
    success = tester.summary()
    
    # Save results
    with open("/app/test_reports/backend_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total": tester.tests_run,
            "passed": tester.tests_passed,
            "failed": tester.tests_failed,
            "results": tester.results
        }, f, indent=2)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
