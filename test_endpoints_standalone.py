"""
Standalone endpoint tests for all tools (DAT, SOV, PPTX)
Run this with: python test_endpoints_standalone.py
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = 5

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"  {status} {name}")
    if details and not passed:
        print(f"    {Colors.YELLOW}{details}{Colors.END}")

def print_section(name):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

# Store results
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}

def run_test(test_name, test_func):
    """Run a test and track results"""
    results["total"] += 1
    try:
        test_func()
        results["passed"] += 1
        print_test(test_name, True)
        return True
    except AssertionError as e:
        results["failed"] += 1
        results["errors"].append({"test": test_name, "error": str(e)})
        print_test(test_name, False, str(e))
        return False
    except Exception as e:
        results["failed"] += 1
        error_msg = f"{type(e).__name__}: {str(e)}"
        results["errors"].append({"test": test_name, "error": error_msg})
        print_test(test_name, False, error_msg)
        return False

# ============================================================================
# GATEWAY TESTS
# ============================================================================

def test_gateway_health():
    response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy", f"Gateway not healthy: {data}"
    assert "tools" in data, "No tools info in health response"

def test_gateway_docs():
    response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

# ============================================================================
# PPTX TESTS
# ============================================================================

def test_pptx_health():
    response = requests.get(f"{BASE_URL}/api/pptx/health", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy", f"PPTX not healthy: {data}"

def test_pptx_docs():
    response = requests.get(f"{BASE_URL}/api/pptx/docs", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

def test_pptx_list_projects():
    response = requests.get(f"{BASE_URL}/api/pptx/api/v1/projects", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"

def test_pptx_create_project():
    payload = {"name": "Test Project", "description": "Automated test"}
    response = requests.post(f"{BASE_URL}/api/pptx/api/v1/projects", json=payload, timeout=TIMEOUT)
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "id" in data, f"No id in response: {data}"

# ============================================================================
# DAT TESTS
# ============================================================================

def test_dat_health():
    response = requests.get(f"{BASE_URL}/api/dat/health", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy", f"DAT not healthy: {data}"

def test_dat_docs():
    response = requests.get(f"{BASE_URL}/api/dat/docs", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

def test_dat_list_runs():
    response = requests.get(f"{BASE_URL}/api/dat/api/v1/runs", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"

def test_dat_create_run():
    payload = {}  # Empty dict for POST body
    response = requests.post(f"{BASE_URL}/api/dat/api/v1/runs", json=payload, timeout=TIMEOUT)
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
    data = response.json()
    assert "run_id" in data, f"No run_id in response: {data}"

# ============================================================================
# SOV TESTS
# ============================================================================

def test_sov_health():
    response = requests.get(f"{BASE_URL}/api/sov/health", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy", f"SOV not healthy: {data}"

def test_sov_docs():
    response = requests.get(f"{BASE_URL}/api/sov/docs", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

def test_sov_list_analyses():
    response = requests.get(f"{BASE_URL}/api/sov/api/v1/analyses", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"

# ============================================================================
# CROSS-TOOL TESTS
# ============================================================================

def test_list_datasets():
    response = requests.get(f"{BASE_URL}/api/v1/datasets", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"

def test_list_datasets_by_tool():
    for tool in ["dat", "sov", "pptx"]:
        response = requests.get(f"{BASE_URL}/api/v1/datasets", params={"tool": tool}, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200 for {tool}, got {response.status_code}"

def test_list_pipelines():
    response = requests.get(f"{BASE_URL}/api/v1/pipelines", timeout=TIMEOUT)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), f"Expected list, got {type(data)}"

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Engineering Tools - Comprehensive Endpoint Tests{Colors.END}")
    print(f"{Colors.BLUE}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    print(f"\n{Colors.YELLOW}⚠ Make sure the gateway is running: .\\start.ps1{Colors.END}\n")
    
    # Gateway Tests
    print_section("Gateway Tests")
    run_test("Gateway health endpoint", test_gateway_health)
    run_test("Gateway OpenAPI docs", test_gateway_docs)
    
    # PPTX Tests
    print_section("PowerPoint Generator Tests")
    run_test("PPTX health endpoint", test_pptx_health)
    run_test("PPTX OpenAPI docs", test_pptx_docs)
    run_test("PPTX list projects", test_pptx_list_projects)
    run_test("PPTX create project", test_pptx_create_project)
    
    # DAT Tests
    print_section("Data Aggregator Tests")
    run_test("DAT health endpoint", test_dat_health)
    run_test("DAT OpenAPI docs", test_dat_docs)
    run_test("DAT list runs", test_dat_list_runs)
    run_test("DAT create run", test_dat_create_run)
    
    # SOV Tests
    print_section("SOV Analyzer Tests")
    run_test("SOV health endpoint", test_sov_health)
    run_test("SOV OpenAPI docs", test_sov_docs)
    run_test("SOV list analyses", test_sov_list_analyses)
    
    # Cross-Tool Tests
    print_section("Cross-Tool Integration Tests")
    run_test("List all datasets", test_list_datasets)
    run_test("Filter datasets by tool", test_list_datasets_by_tool)
    run_test("List pipelines", test_list_pipelines)
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"Total Tests: {results['total']}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
    
    if results['failed'] > 0:
        print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
        for error in results['errors']:
            print(f"  • {error['test']}")
            print(f"    {error['error']}")
    
    print(f"\n{Colors.BLUE}Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")
    
    # Exit with error code if any tests failed
    exit(0 if results['failed'] == 0 else 1)
