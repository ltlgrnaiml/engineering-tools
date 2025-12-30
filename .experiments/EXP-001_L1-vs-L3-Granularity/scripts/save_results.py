#!/usr/bin/env python3
"""
EXP-001 Automatic Results Recorder

Run this script at the END of experiment execution to automatically
capture and save results. The AI model should run this script
and answer the prompts.

Usage:
    python .experiments/EXP-001_L1-vs-L3-Granularity/scripts/save_results.py
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_branch() -> str:
    """Get current git branch name."""
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def detect_model_from_branch(branch: str) -> dict:
    """Map branch name to model info."""
    model_map = {
        "experiment/l1-opus": {
            "model_id": "claude-opus-4.5-thinking",
            "model_name": "Claude Opus 4.5 Thinking",
            "cost_multiplier": 5,
            "granularity": "L1",
        },
        "experiment/l1-sonnet": {
            "model_id": "claude-sonnet-4.5-thinking",
            "model_name": "Claude Sonnet 4.5 Thinking",
            "cost_multiplier": 3,
            "granularity": "L1",
        },
        "experiment/l1-gpt52": {
            "model_id": "gpt-5.2-high-reasoning-fast",
            "model_name": "GPT-5.2 High Reasoning Fast",
            "cost_multiplier": 6,
            "granularity": "L1",
        },
        "experiment/l1-gemini3pro": {
            "model_id": "gemini-3-pro-high",
            "model_name": "Gemini 3 Pro High",
            "cost_multiplier": 3,
            "granularity": "L1",
        },
        "experiment/l3-grok": {
            "model_id": "grok-code-fast-1",
            "model_name": "Grok Code Fast 1",
            "cost_multiplier": 0,
            "granularity": "L3",
        },
        "experiment/l3-haiku": {
            "model_id": "claude-haiku",
            "model_name": "Claude Haiku",
            "cost_multiplier": 1,
            "granularity": "L3",
        },
        "experiment/l3-gemini-flash": {
            "model_id": "gemini-flash-3-high",
            "model_name": "Gemini Flash 3 High",
            "cost_multiplier": 1,
            "granularity": "L3",
        },
        "experiment/l3-gpt51": {
            "model_id": "gpt-5.1-codex-max-high",
            "model_name": "GPT-5.1-Codex Max High",
            "cost_multiplier": 1,
            "granularity": "L3",
        },
    }
    return model_map.get(branch, {})


def run_verification(cmd: str) -> dict:
    """Run a verification command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "command": cmd,
            "passed": result.returncode == 0,
            "stdout": result.stdout[:500] if result.stdout else "",
            "stderr": result.stderr[:500] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"command": cmd, "passed": False, "error": "timeout"}
    except Exception as e:
        return {"command": cmd, "passed": False, "error": str(e)}


def main():
    """Main entry point for results recording."""
    print("=" * 60)
    print("EXP-001 Automatic Results Recorder")
    print("=" * 60)
    
    # Detect branch and model
    branch = get_git_branch()
    model_info = detect_model_from_branch(branch)
    
    if not model_info:
        print(f"ERROR: Unknown branch '{branch}'")
        print("Expected branches: experiment/l1-* or experiment/l3-*")
        sys.exit(1)
    
    print(f"\nDetected Branch: {branch}")
    print(f"Model: {model_info['model_name']}")
    print(f"Granularity: {model_info['granularity']}")
    print(f"Cost Multiplier: {model_info['cost_multiplier']}x")
    
    # Collect metrics from AI
    print("\n" + "-" * 60)
    print("Please provide the following metrics:")
    print("-" * 60)
    
    start_time = input("Start time (HH:MM or ISO format): ").strip()
    end_time = input("End time (HH:MM or ISO format, or press Enter for now): ").strip()
    if not end_time:
        end_time = datetime.now().isoformat()
    
    total_messages = input("Total AI messages in Cascade: ").strip()
    errors_encountered = input("Number of errors encountered: ").strip()
    
    # Run verification commands
    print("\n" + "-" * 60)
    print("Running verification commands...")
    print("-" * 60)
    
    verifications = {
        "T-M1-01_contracts": run_verification(
            'python -c "from shared.contracts.devtools.workflow import ArtifactType, GraphNode"'
        ),
        "T-M1-02_service": run_verification(
            'grep "def scan_artifacts" gateway/services/workflow_service.py'
        ),
        "T-M1-03_list_endpoint": run_verification(
            'grep "artifacts" gateway/routes/devtools.py'
        ),
        "T-M1-04_graph_endpoint": run_verification(
            'grep "artifacts/graph" gateway/routes/devtools.py'
        ),
        "T-M1-05_crud_endpoints": run_verification(
            'grep -E "@router\\.(post|delete)" gateway/routes/devtools.py'
        ),
        "T-M1-06_tests": run_verification(
            'test -f tests/gateway/test_devtools_workflow.py && echo "EXISTS"'
        ),
    }
    
    # Calculate scores
    tasks_passed = sum(1 for v in verifications.values() if v.get("passed", False))
    tasks_total = len(verifications)
    
    print(f"\nVerification Results: {tasks_passed}/{tasks_total} tasks passed")
    for task_id, result in verifications.items():
        status = "✅" if result.get("passed") else "❌"
        print(f"  {status} {task_id}")
    
    # Build results object
    results = {
        "experiment_id": "EXP-001",
        "branch": branch,
        "model": model_info,
        "execution": {
            "start_time": start_time,
            "end_time": end_time,
            "total_messages": int(total_messages) if total_messages.isdigit() else 0,
            "errors_encountered": int(errors_encountered) if errors_encountered.isdigit() else 0,
        },
        "verifications": verifications,
        "scores": {
            "tasks_passed": tasks_passed,
            "tasks_total": tasks_total,
            "completion_rate": round(tasks_passed / tasks_total * 100, 1),
        },
        "recorded_at": datetime.now().isoformat(),
    }
    
    # Determine output path
    results_dir = Path(".experiments/EXP-001_L1-vs-L3-Granularity/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    model_short = model_info["model_id"].replace("-", "_").upper()
    output_file = results_dir / f"RESULTS_{model_short}.json"
    
    # Save results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ Results saved to: {output_file}")
    print("=" * 60)
    
    # Print summary for easy copy
    print("\n📊 Quick Summary:")
    print(f"   Model: {model_info['model_name']}")
    print(f"   Granularity: {model_info['granularity']}")
    print(f"   Tasks Passed: {tasks_passed}/{tasks_total}")
    print(f"   Completion Rate: {results['scores']['completion_rate']}%")
    print(f"   Cost Multiplier: {model_info['cost_multiplier']}x")
    
    if model_info["cost_multiplier"] > 0:
        efficiency = results["scores"]["completion_rate"] / model_info["cost_multiplier"]
        print(f"   Efficiency Score: {efficiency:.1f}")
    else:
        print(f"   Efficiency Score: ∞ (free model)")


if __name__ == "__main__":
    main()
