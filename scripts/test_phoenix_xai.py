#!/usr/bin/env python
"""Test xAI connection through Phoenix.

Verifies that Phoenix can call xAI models via the OpenAI-compatible API.
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def test_xai_via_phoenix():
    """Test xAI through Phoenix's client."""
    from phoenix.evals import OpenAIModel

    print("🔬 Testing xAI connection through Phoenix...")
    print("="*60)

    # Get xAI credentials
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("❌ XAI_API_KEY not found")
        return False

    print(f"✅ API Key: {api_key[:20]}...")

    # Create OpenAI-compatible model pointing to xAI
    try:
        model = OpenAIModel(
            model="grok-3-fast",
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )
        print("✅ Model configured: grok-3-fast @ api.x.ai")
    except Exception as e:
        print(f"❌ Model config failed: {e}")
        return False

    # Test with a simple prompt
    test_prompt = "What is 2+2? Answer with just the number."

    print(f"\n📝 Test prompt: '{test_prompt}'")
    print("-"*40)

    try:
        response = model(test_prompt)
        print(f"✅ Response: {response}")
        print("-"*40)
        print("\n🎉 xAI connection via Phoenix: SUCCESS!")
        return True
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False


def test_xai_direct():
    """Test xAI directly via OpenAI SDK (fallback test)."""
    from openai import OpenAI

    print("\n🔬 Testing xAI directly via OpenAI SDK...")
    print("="*60)

    api_key = os.getenv("XAI_API_KEY")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )

    try:
        response = client.chat.completions.create(
            model="grok-3-fast",
            messages=[{"role": "user", "content": "Say 'Hello Phoenix!' in exactly 2 words."}],
            max_tokens=10,
        )
        result = response.choices[0].message.content
        print(f"✅ Direct xAI response: {result}")
        return True
    except Exception as e:
        print(f"❌ Direct API call failed: {e}")
        return False


def test_exp002_prompt():
    """Test with EXP-002 scenario prompt."""
    from openai import OpenAI

    print("\n🔬 Testing EXP-002 Scenario Prompt...")
    print("="*60)

    api_key = os.getenv("XAI_API_KEY")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )

    # EXP-002 test prompt (shortened for quick test)
    prompt = """You are helping design a feature for DevTools Workflow Manager.

Title: Artifact Version History

Requirements:
1. Create version snapshots before overwriting artifacts
2. Store version metadata (timestamp, author, summary)
3. Allow viewing previous versions
4. Support restoring previous versions

Constraints:
- File-based storage (no separate database)
- Minimal storage overhead
- Integrate with existing API

Generate a brief DISCUSSION document outline (just section headers and 1-sentence summaries).
Keep response under 200 words."""

    print("📝 Sending EXP-002 test prompt...")
    print("-"*40)

    try:
        response = client.chat.completions.create(
            model="grok-3-fast",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        result = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else "unknown"

        print(f"✅ Response ({tokens_used} tokens):\n")
        print(result)
        print("-"*40)
        print("\n🎉 EXP-002 prompt test: SUCCESS!")
        return True
    except Exception as e:
        print(f"❌ EXP-002 test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Phoenix + xAI Integration Test")
    print("="*60)

    # Test 1: Direct xAI
    direct_ok = test_xai_direct()

    # Test 2: Phoenix wrapper (may have different behavior)
    # phoenix_ok = test_xai_via_phoenix()

    # Test 3: EXP-002 prompt
    if direct_ok:
        exp002_ok = test_exp002_prompt()

    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    print(f"  Direct xAI: {'✅ PASS' if direct_ok else '❌ FAIL'}")
    # print(f"  Phoenix wrapper: {'✅ PASS' if phoenix_ok else '❌ FAIL'}")
    if direct_ok:
        print(f"  EXP-002 prompt: {'✅ PASS' if exp002_ok else '❌ FAIL'}")
