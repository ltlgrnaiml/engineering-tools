#!/usr/bin/env python
"""Test xAI Collections API - Upload files to collection.

Based on xAI API documentation:
https://docs.x.ai/docs/guides/using-collections
"""

import os
import httpx
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

XAI_API_KEY = os.getenv("XAI_API_KEY")
COLLECTION_ID = "collection_1e39adef-7681-4805-8687-3fe14e46201d"
BASE_URL = "https://api.x.ai/v1"


def list_collections():
    """List all collections."""
    response = httpx.get(
        f"{BASE_URL}/collections",
        headers={"Authorization": f"Bearer {XAI_API_KEY}"},
        timeout=30,
    )
    print(f"List Collections: {response.status_code}")
    print(response.json())
    return response.json()


def get_collection(collection_id: str):
    """Get collection details."""
    response = httpx.get(
        f"{BASE_URL}/collections/{collection_id}",
        headers={"Authorization": f"Bearer {XAI_API_KEY}"},
        timeout=30,
    )
    print(f"Get Collection: {response.status_code}")
    print(response.json())
    return response.json()


def upload_file(collection_id: str, file_path: Path, metadata: dict = None):
    """Upload a file to a collection.
    
    Args:
        collection_id: The collection ID.
        file_path: Path to the file to upload.
        metadata: Optional metadata dict.
    """
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "text/plain")}
        data = {}
        if metadata:
            import json
            data["metadata"] = json.dumps(metadata)
        
        response = httpx.post(
            f"{BASE_URL}/collections/{collection_id}/documents",
            headers={"Authorization": f"Bearer {XAI_API_KEY}"},
            files=files,
            data=data,
            timeout=60,
        )
    
    print(f"Upload File: {response.status_code}")
    print(response.text)
    return response


def list_documents(collection_id: str):
    """List documents in a collection."""
    response = httpx.get(
        f"{BASE_URL}/collections/{collection_id}/documents",
        headers={"Authorization": f"Bearer {XAI_API_KEY}"},
        timeout=30,
    )
    print(f"List Documents: {response.status_code}")
    print(response.json())
    return response.json()


def main():
    print("=" * 60)
    print("xAI Collections API Test")
    print("=" * 60)
    
    if not XAI_API_KEY:
        print("ERROR: XAI_API_KEY not set in .env")
        return
    
    print(f"\nCollection ID: {COLLECTION_ID}")
    print(f"API Key: {XAI_API_KEY[:10]}...")
    
    # Test 1: Get collection info
    print("\n--- Test 1: Get Collection Info ---")
    try:
        get_collection(COLLECTION_ID)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: List documents
    print("\n--- Test 2: List Documents ---")
    try:
        list_documents(COLLECTION_ID)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Upload a sample ADR
    print("\n--- Test 3: Upload Sample Document ---")
    test_file = Path(__file__).parent.parent / ".adrs" / "core" / "ADR-0010_type-safety-contract-discipline.json"
    if test_file.exists():
        print(f"Found: {test_file}")
        metadata = {
            "doc_type": "adr",
            "doc_id": "ADR-0010",
            "status": "active",
            "tags": "contracts,ssot",
        }
        try:
            upload_file(COLLECTION_ID, test_file, metadata)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Test file not found: {test_file}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
