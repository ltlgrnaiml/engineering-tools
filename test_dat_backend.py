#!/usr/bin/env python3
"""Test DAT backend API functionality."""

import requests
import json
import time
from pathlib import Path

def test_backend():
    """Test the DAT backend functionality."""
    base_url = "http://localhost:8001"

    print("🧪 Testing DAT Backend API")
    print("=" * 40)

    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        if resp.status_code == 200:
            print("✅ Health check passed")
            data = resp.json()
            print(f"   Status: {data['status']}, Tool: {data['tool']}, Version: {data['version']}")
        else:
            print(f"❌ Health check failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

    # Test 2: Test job queue status
    print("\n2. Testing job queue status...")
    try:
        resp = requests.get(f"{base_url}/jobs/queue/status", timeout=5)
        if resp.status_code == 200:
            print("✅ Job queue status check passed")
            data = resp.json()
            print(f"   Queue healthy: {data['queue_healthy']}")
            print(f"   Pending jobs: {data['pending_count']}")
            print(f"   Running jobs: {data['running_count']}")
        else:
            print(f"❌ Job queue status failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Job queue status error: {e}")
        return False

    # Test 3: Test API documentation
    print("\n3. Testing API documentation...")
    try:
        resp = requests.get(f"{base_url}/docs", timeout=5)
        if resp.status_code == 200:
            print("✅ API docs accessible")
        else:
            print(f"⚠️  API docs not accessible: {resp.status_code}")
    except Exception as e:
        print(f"⚠️  API docs error: {e}")

    # Test 4: Test OpenAPI schema
    print("\n4. Testing OpenAPI schema...")
    try:
        resp = requests.get(f"{base_url}/openapi.json", timeout=5)
        if resp.status_code == 200:
            schema = resp.json()
            print("✅ OpenAPI schema accessible")
            paths = list(schema.get('paths', {}).keys())
            print(f"   Available endpoints: {len(paths)}")
            job_paths = [p for p in paths if 'jobs' in p]
            print(f"   Job endpoints: {len(job_paths)}")
            dat_paths = [p for p in paths if '/v1/' in p]
            print(f"   DAT endpoints: {len(dat_paths)}")
        else:
            print(f"❌ OpenAPI schema failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ OpenAPI schema error: {e}")
        return False

    print("\n🎉 All basic tests passed! DAT backend is running correctly.")
    return True

if __name__ == "__main__":
    test_backend()
