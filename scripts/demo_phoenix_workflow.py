#!/usr/bin/env python
"""Demo: Phoenix Workflow with xAI Tracing.

Shows how to:
1. Instrument code with Phoenix tracing
2. Run LLM calls that get traced
3. View traces in Phoenix UI

Run with: python scripts/demo_phoenix_workflow.py
Then check traces at: http://localhost:6006/projects
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def setup_phoenix_tracing():
    """Initialize Phoenix tracing for LangChain."""
    print("🔧 Setting up Phoenix tracing...")
    
    # Register Phoenix as the trace provider
    from phoenix.otel import register
    tracer_provider = register(
        project_name="engineering-tools",
        endpoint="http://localhost:6006/v1/traces",
    )
    
    # Instrument LangChain
    from openinference.instrumentation.langchain import LangChainInstrumentor
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    
    print("✅ Phoenix tracing enabled")
    print("   Project: engineering-tools")
    print("   Traces: http://localhost:6006/projects")
    return tracer_provider


def demo_simple_llm_call():
    """Demo 1: Simple LLM call with tracing."""
    print("\n" + "="*60)
    print("📝 Demo 1: Simple LLM Call")
    print("="*60)
    
    from gateway.services.llm import get_xai_chat_model
    
    llm = get_xai_chat_model(model="grok-3-fast", temperature=0.3)
    
    prompt = "What is RAG (Retrieval-Augmented Generation) in one sentence?"
    print(f"\n📤 Prompt: {prompt}")
    
    response = llm.invoke(prompt)
    print(f"\n📥 Response: {response.content}")
    print("\n✅ Check Phoenix → Projects → engineering-tools for trace!")


def demo_rag_chain():
    """Demo 2: RAG chain with Knowledge Archive."""
    print("\n" + "="*60)
    print("📝 Demo 2: RAG Chain with Knowledge Archive")
    print("="*60)
    
    from gateway.services.llm import create_rag_chain
    
    chain = create_rag_chain(model="grok-3-fast")
    
    question = "What ADRs relate to the AI development workflow?"
    print(f"\n📤 Question: {question}")
    
    try:
        response = chain.invoke(question)
        print(f"\n📥 Answer: {response.answer[:500]}...")
        print(f"\n📚 Sources: {response.sources[:5]}")
    except Exception as e:
        print(f"\n⚠️ RAG unavailable (Knowledge Archive not indexed): {e}")
        print("   This is expected if you haven't run the indexer yet.")


def demo_structured_output():
    """Demo 3: Structured output generation."""
    print("\n" + "="*60)
    print("📝 Demo 3: Structured Output (Artifact Generation)")
    print("="*60)
    
    from gateway.services.llm_service import generate_structured
    from pydantic import BaseModel
    
    class DiscussionOutline(BaseModel):
        title: str
        problem_statement: str
        options: list[str]
        recommendation: str
    
    prompt = """Generate a DISCUSSION outline for:
    Title: Artifact Version History
    Context: Need to track versions of workflow artifacts (ADR, SPEC, PLAN files)
    """
    
    print(f"\n📤 Generating structured output...")
    
    response = generate_structured(
        prompt=prompt,
        schema=DiscussionOutline,
        system_prompt="You are helping design features for a DevTools workflow manager.",
    )
    
    if response.success:
        print(f"\n📥 Generated DISCUSSION:")
        print(f"   Title: {response.data['title']}")
        print(f"   Problem: {response.data['problem_statement'][:100]}...")
        print(f"   Options: {len(response.data['options'])} options")
        print(f"   Recommendation: {response.data['recommendation'][:100]}...")
    else:
        print(f"\n❌ Generation failed: {response.error}")


def demo_exp002_scenario():
    """Demo 4: Run EXP-002 test scenario."""
    print("\n" + "="*60)
    print("📝 Demo 4: EXP-002 Model Quality Test")
    print("="*60)
    
    from gateway.services.llm import get_xai_chat_model
    
    llm = get_xai_chat_model(model="grok-4-fast-reasoning", temperature=0.5)
    
    # EXP-002 test prompt
    prompt = """You are helping design a feature for DevTools Workflow Manager.

Title: Artifact Version History

The user wants to add version history tracking to workflow artifacts:
1. Create version snapshots before overwriting artifacts
2. Store version metadata (timestamp, author hint, change summary)
3. Allow viewing previous versions
4. Support restoring a previous version as the current version

Key constraints:
- Must work with the existing file-based artifact storage
- Should not significantly increase storage requirements for small edits
- Version data should be stored alongside artifacts, not in a separate database
- Must integrate with the existing artifact API endpoints

Generate a DISCUSSION document that analyzes this feature request with:
- Problem statement
- 3+ design options with pros/cons
- Recommended approach
- Open questions
"""
    
    print("\n📤 Running EXP-002 scenario with grok-4-fast-reasoning...")
    
    response = llm.invoke(prompt)
    
    print(f"\n📥 Response ({len(response.content)} chars):")
    print("-"*40)
    # Show first 1000 chars
    print(response.content[:1000])
    if len(response.content) > 1000:
        print(f"\n... [{len(response.content) - 1000} more chars]")
    print("-"*40)
    
    print("\n✅ Full trace available in Phoenix!")
    print("   Go to: http://localhost:6006/projects → engineering-tools → Traces")


def main():
    print("🚀 Phoenix Workflow Demo")
    print("="*60)
    print("This demo shows how your code integrates with Phoenix tracing.")
    print("Make sure Phoenix is running at http://localhost:6006")
    print("="*60)
    
    # Setup tracing first
    setup_phoenix_tracing()
    
    # Run demos
    demo_simple_llm_call()
    demo_structured_output()
    demo_exp002_scenario()
    
    # Summary
    print("\n" + "="*60)
    print("🎯 Summary")
    print("="*60)
    print("""
How it works:
1. Phoenix OTEL register() creates a trace provider
2. LangChainInstrumentor instruments all LangChain calls
3. Every llm.invoke() is automatically traced
4. Traces appear in Phoenix UI under your project

View your traces:
  http://localhost:6006/projects → engineering-tools → Traces

Each trace shows:
  - Input/output messages
  - Token usage
  - Latency
  - Model used
  - Full conversation history

Next steps:
  - Run experiments in Phoenix Playground
  - Compare models side-by-side
  - Use Phoenix evaluators with rubrics
""")


if __name__ == "__main__":
    main()
