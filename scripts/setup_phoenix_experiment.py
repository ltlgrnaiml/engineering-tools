#!/usr/bin/env python
"""Setup Phoenix experiment from EXP-002 test scenario.

This script:
1. Starts Phoenix server
2. Creates a dataset from EXP-002 test scenario
3. Creates prompt variants for testing
4. Configures LLM evaluator based on rubrics

Run with: python scripts/setup_phoenix_experiment.py
"""

import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Load .env
from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def check_phoenix():
    """Check if Phoenix is available."""
    try:
        import phoenix as px
        print(f"✅ Phoenix {px.__version__} available")
        return True
    except ImportError:
        print("❌ Phoenix not installed")
        return False


def start_phoenix():
    """Start Phoenix server."""
    import phoenix as px

    # Launch Phoenix
    session = px.launch_app()
    print("✅ Phoenix UI: http://localhost:6006")
    return session


def create_exp002_dataset():
    """Create Phoenix dataset from EXP-002 test scenario."""
    import phoenix as px

    # EXP-002 Test Scenario
    test_scenario = {
        "title": "Artifact Version History",
        "description": """Add version history tracking to artifacts in the DevTools Workflow Manager. 
When an artifact (Discussion, ADR, SPEC, or Plan) is saved, the system should:
1. Create a new version snapshot before overwriting
2. Store version metadata (timestamp, author hint, change summary)
3. Allow viewing previous versions
4. Support restoring a previous version as the current version

Key constraints:
- Must work with the existing file-based artifact storage
- Should not significantly increase storage requirements for small edits
- Version data should be stored alongside artifacts, not in a separate database
- Must integrate with the existing artifact API endpoints"""
    }

    # Create dataset with the test scenario as examples
    client = px.Client()

    # Check if dataset exists
    try:
        dataset = client.get_dataset(name="EXP-002-Model-Quality")
        print("✅ Dataset 'EXP-002-Model-Quality' already exists")
    except:
        # Create new dataset
        dataset = client.upload_dataset(
            dataset_name="EXP-002-Model-Quality",
            inputs=[
                {"title": test_scenario["title"], "description": test_scenario["description"]}
            ],
            outputs=[
                {"expected_artifacts": ["DISC", "ADR", "SPEC", "PLAN"]}
            ],
        )
        print("✅ Created dataset 'EXP-002-Model-Quality'")

    return dataset


def print_xai_config():
    """Print xAI configuration instructions for Phoenix."""
    xai_key = os.getenv("XAI_API_KEY", "")

    print("\n" + "="*60)
    print("📋 xAI Configuration for Phoenix Playground")
    print("="*60)
    print("\nOption 1: Configure in Phoenix UI")
    print("-" * 40)
    print("1. Open http://localhost:6006")
    print("2. Go to Settings → API Keys")
    print("3. Set OpenAI API Key to your xAI key")
    print("4. In Playground → Model Config:")
    print("   - Base URL: https://api.x.ai/v1")
    print("   - Model: grok-3-fast (or grok-4-fast-reasoning)")

    print("\nOption 2: Environment Variables (already set)")
    print("-" * 40)
    if xai_key:
        print(f"   XAI_API_KEY: {xai_key[:20]}...")
        print("   XAI_BASE_URL: https://api.x.ai/v1")
    else:
        print("   ❌ XAI_API_KEY not found in .env")

    print("\n" + "="*60)


def print_rubric_evaluator():
    """Print the rubric-based evaluator prompt."""
    evaluator_prompt = '''You are evaluating AI-generated documentation for a DevTools Workflow Manager.

Score each criterion from 0-3:
- 0 = Missing
- 1 = Weak  
- 2 = Adequate
- 3 = Strong

## DISCUSSION Criteria (25 pts total):
- Problem Statement (3 pts): Is the problem clearly stated with context?
- Option Analysis (5 pts): Are 3+ options listed with pros/cons?
- Technical Depth (5 pts): Is there deep architectural insight?
- Project Awareness (5 pts): Does it reference existing ADRs/contracts?
- Open Questions (3 pts): Are there actionable decision points?
- Clarity (2 pts): Is it well-organized?
- Stakeholder ID (2 pts): Are roles and concerns identified?

## ADR Criteria (25 pts total):
- Decision Statement (4 pts): Clear "We will..." with rationale?
- Context Accuracy (3 pts): Rich context with history?
- Alternatives (4 pts): 3+ alternatives with trade-offs?
- Consequences (4 pts): Positive, negative, and risks?
- Schema Compliance (3 pts): Valid JSON with all required fields?
- Architectural Fit (4 pts): Builds on existing ADRs?
- Actionability (3 pts): Clear next steps?

## SPEC Criteria (25 pts total):
- Requirements Coverage (5 pts): All requirements + edge cases?
- API Contract (5 pts): Full request/response schemas?
- Data Model (4 pts): Schema + validation rules?
- UI/UX (3 pts): Wireframes/behavior detail?
- Error Handling (3 pts): Error codes + messages?
- Integration Points (3 pts): Sequence/flow diagrams?
- Testability (2 pts): Acceptance criteria?

## PLAN Criteria (25 pts total):
- Task Granularity (5 pts): 1-4 hour tasks?
- Dependency Ordering (4 pts): DAG with clear deps?
- Completeness (4 pts): All work + contingencies?
- Verification (4 pts): TDD approach?
- Milestones (3 pts): Clear milestones + criteria?
- Estimates (3 pts): All estimated + confidence?
- Context (2 pts): Rich context per task?

Output JSON:
{
  "disc_score": <0-25>,
  "adr_score": <0-25>,
  "spec_score": <0-25>,
  "plan_score": <0-25>,
  "total_score": <0-100>,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "recommendation": "excellent|good|fair|poor"
}'''

    print("\n" + "="*60)
    print("📊 Rubric-Based Evaluator Prompt")
    print("="*60)
    print("\nUse this prompt in Phoenix to create an LLM evaluator:")
    print("-" * 40)
    print(evaluator_prompt[:500] + "...\n")
    print("(Full prompt saved to .experiments/EXP-002_Model-Quality-Evaluation/EVALUATOR_PROMPT.txt)")

    # Save full prompt
    evaluator_path = os.path.join(
        PROJECT_ROOT,
        ".experiments/EXP-002_Model-Quality-Evaluation/EVALUATOR_PROMPT.txt"
    )
    with open(evaluator_path, "w") as f:
        f.write(evaluator_prompt)

    return evaluator_prompt


def main():
    """Setup Phoenix experiment."""
    print("🔬 Setting up Phoenix Experiment from EXP-002")
    print("="*60)

    # Check Phoenix
    if not check_phoenix():
        print("\nInstall with: pip install arize-phoenix")
        return 1

    # Start Phoenix
    print("\n📡 Starting Phoenix server...")
    session = start_phoenix()

    # Print xAI configuration
    print_xai_config()

    # Create dataset
    print("\n📦 Creating experiment dataset...")
    try:
        dataset = create_exp002_dataset()
    except Exception as e:
        print(f"⚠️ Dataset creation skipped: {e}")

    # Print evaluator prompt
    print_rubric_evaluator()

    # Summary
    print("\n" + "="*60)
    print("🎯 Next Steps")
    print("="*60)
    print("""
1. Open Phoenix UI: http://localhost:6006

2. Configure xAI in Settings → API Keys:
   - Set OpenAI API Key to your xAI key
   
3. Go to Playground → Model Config:
   - Set Base URL: https://api.x.ai/v1
   - Select model: grok-3-fast
   
4. Test the EXP-002 prompt:
   - Paste the test scenario description
   - Generate DISC/ADR/SPEC/PLAN
   - Compare across models
   
5. Create experiment to track results

Press Ctrl+C to stop Phoenix when done.
""")

    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Phoenix...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
