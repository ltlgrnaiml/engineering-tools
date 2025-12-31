#!/usr/bin/env python
"""Demo: Phoenix + LangChain + RAG Integration.

This script demonstrates:
1. Starting Phoenix for local observability
2. Using LangChain with xAI (Grok)
3. RAG integration with Knowledge Archive
4. Viewing traces in Phoenix UI

Run with: python scripts/demo_phoenix_rag.py

Phoenix UI will be available at: http://localhost:6006
"""

import os
import sys
import time

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Load .env file
from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def check_dependencies():
    """Check if required packages are installed."""
    missing = []

    try:
        import phoenix
    except ImportError:
        missing.append("arize-phoenix")

    try:
        from phoenix.otel import register
    except ImportError:
        missing.append("arize-phoenix-otel")

    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        missing.append("langchain-openai")

    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
    except ImportError:
        missing.append("openinference-instrumentation-langchain")

    if missing:
        print("❌ Missing dependencies. Install with:")
        print(f"   pip install {' '.join(missing)}")
        print("\nOr install all AI dependencies:")
        print("   pip install -e '.[ai]'")
        return False

    return True


def check_api_key():
    """Check if XAI_API_KEY is set."""
    api_key = os.getenv("XAI_API_KEY", "")
    if not api_key:
        print("❌ XAI_API_KEY environment variable is required.")
        print("   Get your key at: https://console.x.ai/")
        print("\n   Set it with:")
        print("   export XAI_API_KEY='your-key-here'  # Linux/Mac")
        print("   set XAI_API_KEY=your-key-here      # Windows CMD")
        print("   $env:XAI_API_KEY='your-key-here'   # Windows PowerShell")
        return False
    return True


def demo_basic_llm():
    """Demo 1: Basic LLM call with tracing."""
    print("\n" + "="*60)
    print("Demo 1: Basic LLM Call")
    print("="*60)

    from gateway.services.llm import get_xai_chat_model

    llm = get_xai_chat_model(temperature=0.5)

    print("\n📤 Sending: 'What is RAG in AI? Answer in one sentence.'")
    response = llm.invoke("What is RAG in AI? Answer in one sentence.")
    print(f"\n📥 Response: {response.content}")
    print("\n✅ Check Phoenix UI for trace details!")


def demo_rag_chain():
    """Demo 2: RAG chain with Knowledge Archive."""
    print("\n" + "="*60)
    print("Demo 2: RAG Chain with Knowledge Archive")
    print("="*60)

    from gateway.services.llm import create_rag_chain

    # Create RAG chain (uses Knowledge Archive for retrieval)
    chain = create_rag_chain(temperature=0.3)

    question = "What ADRs are related to deterministic IDs?"
    print(f"\n📤 Question: '{question}'")

    response = chain.invoke(question)

    print(f"\n📥 Answer: {response.answer[:500]}...")
    print(f"\n📚 Sources: {response.sources}")
    print("\n✅ Check Phoenix UI for full RAG trace!")


def demo_conversation():
    """Demo 3: Multi-turn conversation."""
    print("\n" + "="*60)
    print("Demo 3: Multi-turn Conversation")
    print("="*60)

    from langchain_core.messages import HumanMessage

    from gateway.services.llm import get_xai_chat_model

    llm = get_xai_chat_model(temperature=0.7)

    messages = []

    # Turn 1
    q1 = "What is the engineering tools platform?"
    print(f"\n👤 User: {q1}")
    messages.append(HumanMessage(content=q1))

    response1 = llm.invoke(messages)
    print(f"🤖 Assistant: {response1.content[:300]}...")
    messages.append(response1)

    # Turn 2
    q2 = "What tools does it include?"
    print(f"\n👤 User: {q2}")
    messages.append(HumanMessage(content=q2))

    response2 = llm.invoke(messages)
    print(f"🤖 Assistant: {response2.content[:300]}...")

    print("\n✅ Check Phoenix UI to see conversation trace!")


def main():
    """Run the Phoenix + RAG demo."""
    print("🔥 Phoenix + LangChain + RAG Demo")
    print("="*60)

    # Check dependencies
    if not check_dependencies():
        return 1

    if not check_api_key():
        return 1

    # Initialize Phoenix
    print("\n🚀 Starting Phoenix observability...")
    from gateway.services.observability import init_phoenix

    if not init_phoenix(project_name="engineering-tools-demo"):
        print("❌ Failed to start Phoenix")
        return 1

    print("\n" + "="*60)
    print("🔭 Phoenix UI: http://localhost:6006")
    print("   Open this URL to see your traces!")
    print("="*60)

    # Give Phoenix a moment to start
    time.sleep(2)

    try:
        # Run demos
        demo_basic_llm()

        print("\n⏳ Waiting 2 seconds between demos...")
        time.sleep(2)

        demo_rag_chain()

        print("\n⏳ Waiting 2 seconds between demos...")
        time.sleep(2)

        demo_conversation()

        # Summary
        print("\n" + "="*60)
        print("🎉 Demo Complete!")
        print("="*60)
        print("\n📊 View all traces at: http://localhost:6006")
        print("\nYou should see:")
        print("  - LLM call latencies")
        print("  - Token counts and costs")
        print("  - Full request/response content")
        print("  - RAG retrieval steps")
        print("  - Conversation history")

        print("\n⏳ Phoenix will stay running. Press Ctrl+C to exit.")

        # Keep running so user can explore Phoenix
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    finally:
        from gateway.services.observability import shutdown_phoenix
        shutdown_phoenix()

    return 0


if __name__ == "__main__":
    sys.exit(main())
