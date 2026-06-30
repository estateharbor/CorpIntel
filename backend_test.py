"""Backend API tests for CSV upload feature (Companies + LLPs)."""
import io
import sys
import requests
from datetime import datetime

BASE_URL = "https://corp-intel-india.preview.emergentagent.com/api/v1"
API_BASE = "https://corp-intel-india.preview.emergentagent.com/api"

class CSVUploadTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def log(self, test_name, passed, message=""):
        """Log test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ PASS: {test_name}")
        else:
            print(f"❌ FAIL: {test_name}")
        if message:
            print(f"   {message}")
        self.results.append({"test": test_name, "passed": passed, "message": message})

    def test_health(self):
        """Test health endpoint."""
        try:
            resp = requests.get(f"{API_BASE}/health", timeout=10)
            passed = resp.status_code == 200
            self.log("GET /api/health", passed, f"Status: {resp.status_code}")
            return passed
        except Exception as e:
            self.log("GET /api/health", False, f"Error: {e}")
            return False

    def test_upload_csv_valid(self):
        """Test CSV upload with valid CIN, valid LLPIN, invalid identifier, and missing name."""
        csv_content = """identifier,name,status,date_of_incorporation,paid_up_capital,total_contribution,authorized_capital,company_class,principal_activity,roc,address,pin_code,registered_state
U72900MH2099PTC123456,Test Company Ltd,Active,15-03-2020,500000,,1000000,Private,Computer programming,RoC-Mumbai,"Office 12, Mumbai",400053,Maharashtra
ZZT-4321,Test LLP One,Active,22-07-2021,,250000,,LLP,Design services,RoC-Mumbai,"Unit 5, Navi Mumbai",400703,Maharashtra
NOTANID,Invalid Company,Active,01-01-2020,100000,,200000,Private,Trading,RoC-Mumbai,"Address",400001,Maharashtra
ZZT-9876,,Active,10-10-2020,,150000,,LLP,Consulting,RoC-Mumbai,"Address",400002,Maharashtra"""

        try:
            files = {"file": ("test_upload.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
            resp = requests.post(f"{BASE_URL}/admin/upload-csv", files=files, timeout=30)
            
            if resp.status_code != 200:
                self.log("POST /admin/upload-csv (valid CSV)", False, 
                        f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
                return False
            
            data = resp.json()
            
            # Check expected counts
            companies_inserted = data.get("companies_inserted", 0)
            llps_inserted = data.get("llps_inserted", 0)
            rejected_count = data.get("rejected_count", 0)
            total_rows = data.get("total_rows", 0)
            
            checks = [
                (total_rows == 4, f"total_rows: expected 4, got {total_rows}"),
                (companies_inserted == 1, f"companies_inserted: expected 1, got {companies_inserted}"),
                (llps_inserted == 1, f"llps_inserted: expected 1, got {llps_inserted}"),
                (rejected_count == 2, f"rejected_count: expected 2, got {rejected_count}"),
            ]
            
            all_passed = all(check[0] for check in checks)
            messages = [check[1] for check in checks if not check[0]]
            
            self.log("POST /admin/upload-csv (valid CSV)", all_passed, 
                    "; ".join(messages) if messages else f"All counts correct: {data}")
            
            # Store for re-upload test
            self.first_upload_csv = csv_content
            return all_passed
            
        except Exception as e:
            self.log("POST /admin/upload-csv (valid CSV)", False, f"Error: {e}")
            return False

    def test_reupload_csv(self):
        """Test re-uploading same CSV (should update, not insert)."""
        if not hasattr(self, "first_upload_csv"):
            self.log("POST /admin/upload-csv (re-upload)", False, "Skipped: first upload failed")
            return False
        
        try:
            files = {"file": ("test_reupload.csv", io.BytesIO(self.first_upload_csv.encode("utf-8")), "text/csv")}
            resp = requests.post(f"{BASE_URL}/admin/upload-csv", files=files, timeout=30)
            
            if resp.status_code != 200:
                self.log("POST /admin/upload-csv (re-upload)", False, 
                        f"Expected 200, got {resp.status_code}: {resp.text[:200]}")
                return False
            
            data = resp.json()
            
            companies_updated = data.get("companies_updated", 0)
            llps_updated = data.get("llps_updated", 0)
            companies_inserted = data.get("companies_inserted", 0)
            llps_inserted = data.get("llps_inserted", 0)
            
            checks = [
                (companies_updated == 1, f"companies_updated: expected 1, got {companies_updated}"),
                (llps_updated == 1, f"llps_updated: expected 1, got {llps_updated}"),
                (companies_inserted == 0, f"companies_inserted: expected 0, got {companies_inserted}"),
                (llps_inserted == 0, f"llps_inserted: expected 0, got {llps_inserted}"),
            ]
            
            all_passed = all(check[0] for check in checks)
            messages = [check[1] for check in checks if not check[0]]
            
            self.log("POST /admin/upload-csv (re-upload)", all_passed, 
                    "; ".join(messages) if messages else f"Upsert working correctly: {data}")
            return all_passed
            
        except Exception as e:
            self.log("POST /admin/upload-csv (re-upload)", False, f"Error: {e}")
            return False

    def test_get_companies(self):
        """Test GET /companies endpoint (should include uploaded LLP)."""
        try:
            resp = requests.get(f"{BASE_URL}/companies", params={"limit": 50}, timeout=10)
            passed = resp.status_code == 200
            
            if passed:
                data = resp.json()
                total = data.get("total", 0)
                results = data.get("results", [])
                self.log("GET /companies", True, f"Status 200, total={total}, results={len(results)}")
            else:
                self.log("GET /companies", False, f"Status: {resp.status_code}")
            
            return passed
        except Exception as e:
            self.log("GET /companies", False, f"Error: {e}")
            return False

    def test_upload_non_csv(self):
        """Test uploading non-CSV file (should return 400)."""
        try:
            files = {"file": ("test.txt", io.BytesIO(b"This is not a CSV"), "text/plain")}
            resp = requests.post(f"{BASE_URL}/admin/upload-csv", files=files, timeout=10)
            
            passed = resp.status_code == 400
            self.log("POST /admin/upload-csv (non-CSV)", passed, 
                    f"Expected 400, got {resp.status_code}: {resp.text[:100]}")
            return passed
        except Exception as e:
            self.log("POST /admin/upload-csv (non-CSV)", False, f"Error: {e}")
            return False

    def test_upload_empty_file(self):
        """Test uploading empty file (should return 400)."""
        try:
            files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
            resp = requests.post(f"{BASE_URL}/admin/upload-csv", files=files, timeout=10)
            
            passed = resp.status_code == 400
            self.log("POST /admin/upload-csv (empty file)", passed, 
                    f"Expected 400, got {resp.status_code}: {resp.text[:100]}")
            return passed
        except Exception as e:
            self.log("POST /admin/upload-csv (empty file)", False, f"Error: {e}")
            return False

    def test_enrichment_progress(self):
        """Test GET /admin/enrichment-progress (regression)."""
        try:
            resp = requests.get(f"{BASE_URL}/admin/enrichment-progress", timeout=10)
            passed = resp.status_code == 200
            
            if passed:
                data = resp.json()
                progress = data.get("progress", {})
                self.log("GET /admin/enrichment-progress", True, 
                        f"Status 200, total={progress.get('total', 0)}, enriched={progress.get('enriched', 0)}")
            else:
                self.log("GET /admin/enrichment-progress", False, f"Status: {resp.status_code}")
            
            return passed
        except Exception as e:
            self.log("GET /admin/enrichment-progress", False, f"Error: {e}")
            return False

    def test_admin_stats(self):
        """Test GET /admin/stats (regression)."""
        try:
            resp = requests.get(f"{BASE_URL}/admin/stats", timeout=10)
            passed = resp.status_code == 200
            
            if passed:
                data = resp.json()
                self.log("GET /admin/stats", True, 
                        f"Status 200, companies={data.get('companies', 0)}, enriched={data.get('enriched', 0)}")
            else:
                self.log("GET /admin/stats", False, f"Status: {resp.status_code}")
            
            return passed
        except Exception as e:
            self.log("GET /admin/stats", False, f"Error: {e}")
            return False

    def run_all(self):
        """Run all tests."""
        print("\n" + "="*70)
        print("CSV UPLOAD BACKEND TESTS - CorpIntel India")
        print("="*70 + "\n")
        
        # Basic health check
        self.test_health()
        
        # CSV upload tests
        self.test_upload_csv_valid()
        self.test_reupload_csv()
        self.test_get_companies()
        self.test_upload_non_csv()
        self.test_upload_empty_file()
        
        # Regression tests
        self.test_enrichment_progress()
        self.test_admin_stats()
        
        # Summary
        print("\n" + "="*70)
        print(f"SUMMARY: {self.tests_passed}/{self.tests_run} tests passed")
        print("="*70 + "\n")
        
        return self.tests_passed == self.tests_run


def main():
    tester = CSVUploadTester()
    success = tester.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
