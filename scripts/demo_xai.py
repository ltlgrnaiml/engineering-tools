#!/usr/bin/env python3
"""Demo script for xAI Grok API integration.

This script demonstrates:
1. Loading API key from environment variable
2. Making a chat completion request using OpenAI-compatible API
3. Both sync and streaming responses

Usage:
    python scripts/demo_xai.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(project_root / ".env")


def get_api_key() -> str:
    """Get xAI API key from environment.

    Returns:
        The XAI_API_KEY value.

    Raises:
        SystemExit: If XAI_API_KEY is not set.
    """
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        print("ERROR: XAI_API_KEY environment variable not set.")
        print("Please set it in .env file or export it:")
        print("  export XAI_API_KEY=your-api-key-here")
        sys.exit(1)
    return api_key


def demo_with_httpx() -> None:
    """Demo using httpx (no extra dependencies needed)."""
    import httpx

    api_key = get_api_key()

    print("\n" + "=" * 60)
    print("xAI Grok API Demo (using httpx)")
    print("=" * 60)

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello and introduce yourself briefly."},
        ],
        "model": "grok-4-latest",
        "stream": False,
        "temperature": 0.7,
    }

    print("\n📤 Sending request to xAI API...")
    print(f"   Model: {payload['model']}")

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        message = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        print("\n📥 Response received!")
        print("-" * 40)
        print(message)
        print("-" * 40)
        print(f"\n📊 Usage: {usage.get('prompt_tokens', '?')} prompt + "
              f"{usage.get('completion_tokens', '?')} completion = "
              f"{usage.get('total_tokens', '?')} total tokens")

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"   {e.response.text}")
    except httpx.RequestError as e:
        print(f"\n❌ Request Error: {e}")


def demo_with_openai_sdk() -> None:
    """Demo using OpenAI SDK (if installed)."""
    try:
        from openai import OpenAI
    except ImportError:
        print("\n⚠️  OpenAI SDK not installed. Skipping OpenAI SDK demo.")
        print("   Install with: uv sync --extra ai")
        return

    api_key = get_api_key()

    print("\n" + "=" * 60)
    print("xAI Grok API Demo (using OpenAI SDK)")
    print("=" * 60)

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )

    print("\n📤 Sending request via OpenAI SDK...")

    try:
        response = client.chat.completions.create(
            model="grok-4-latest",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What's 2+2? Reply in one sentence."},
            ],
            temperature=0,
        )

        message = response.choices[0].message.content
        usage = response.usage

        print("\n📥 Response received!")
        print("-" * 40)
        print(message)
        print("-" * 40)
        if usage:
            print(f"\n📊 Usage: {usage.prompt_tokens} prompt + "
                  f"{usage.completion_tokens} completion = "
                  f"{usage.total_tokens} total tokens")

    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_streaming() -> None:
    """Demo streaming response using httpx."""
    import httpx

    api_key = get_api_key()

    print("\n" + "=" * 60)
    print("xAI Grok API Demo (Streaming)")
    print("=" * 60)

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Count from 1 to 5, one number per line."},
        ],
        "model": "grok-4-latest",
        "stream": True,
        "temperature": 0,
    }

    print("\n📤 Sending streaming request...")
    print("\n📥 Streaming response:")
    print("-" * 40)

    try:
        with httpx.stream("POST", url, headers=headers, json=payload, timeout=30.0) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    print(content, end="", flush=True)
        print("\n" + "-" * 40)
        print("\n✅ Streaming complete!")

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"\n❌ Request Error: {e}")


def main() -> None:
    """Run all demos."""
    print("\n🚀 xAI Grok API Integration Demo")
    print("=" * 60)

    # Check API key first
    api_key = get_api_key()
    print(f"✅ XAI_API_KEY loaded (ends with ...{api_key[-8:]})")

    # Run demos
    demo_with_httpx()
    demo_with_openai_sdk()
    demo_streaming()

    print("\n" + "=" * 60)
    print("✅ All demos complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
