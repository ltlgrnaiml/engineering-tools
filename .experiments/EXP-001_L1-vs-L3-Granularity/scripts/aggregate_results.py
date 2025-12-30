#!/usr/bin/env python3
"""
EXP-001 Results Aggregator

Run this script from the MAIN workspace (engineering-tools) after all
experiments complete. It will collect results from all worktrees and
generate the final analysis.

Usage:
    python .experiments/EXP-001_L1-vs-L3-Granularity/scripts/aggregate_results.py
"""

import json
from pathlib import Path


def collect_results_from_worktrees() -> list[dict]:
    """Collect all results JSON files from worktrees."""
    results = []
    base_path = Path("C:/Users/Mycahya/CascadeProjects")
    
    worktrees = [
        "exp-l1-opus",
        "exp-l1-sonnet",
        "exp-l1-gpt52",
        "exp-l1-gemini3pro",
        "exp-l3-grok",
        "exp-l3-haiku",
        "exp-l3-gemini-flash",
        "exp-l3-gpt51",
    ]
    
    for worktree in worktrees:
        results_dir = base_path / worktree / ".experiments/EXP-001_L1-vs-L3-Granularity/results"
        if results_dir.exists():
            for result_file in results_dir.glob("RESULTS_*.json"):
                try:
                    with open(result_file) as f:
                        data = json.load(f)
                        data["_source_worktree"] = worktree
                        data["_source_file"] = str(result_file)
                        results.append(data)
                        print(f"✅ Loaded: {worktree} -> {result_file.name}")
                except Exception as e:
                    print(f"❌ Failed to load {result_file}: {e}")
    
    return results


def calculate_efficiency(result: dict) -> float:
    """Calculate efficiency score (completion_rate / cost)."""
    cost = result.get("model", {}).get("cost_multiplier", 1)
    completion = result.get("scores", {}).get("completion_rate", 0)
    
    if cost == 0:
        return float("inf") if completion > 0 else 0
    return completion / cost


def generate_analysis(results: list[dict]) -> dict:
    """Generate comprehensive analysis from results."""
    if not results:
        return {"error": "No results found"}
    
    # Add efficiency to each result
    for r in results:
        r["efficiency"] = calculate_efficiency(r)
    
    # Sort by efficiency
    sorted_results = sorted(
        results,
        key=lambda x: x["efficiency"] if x["efficiency"] != float("inf") else 999999,
        reverse=True,
    )
    
    # Group by granularity
    l1_results = [r for r in results if r.get("model", {}).get("granularity") == "L1"]
    l3_results = [r for r in results if r.get("model", {}).get("granularity") == "L3"]
    
    # Find bests
    best_l1 = max(l1_results, key=lambda x: x.get("scores", {}).get("completion_rate", 0)) if l1_results else None
    best_l3 = max(l3_results, key=lambda x: x.get("scores", {}).get("completion_rate", 0)) if l3_results else None
    best_efficiency = sorted_results[0] if sorted_results else None
    
    return {
        "total_experiments": len(results),
        "l1_experiments": len(l1_results),
        "l3_experiments": len(l3_results),
        "rankings": [
            {
                "rank": i + 1,
                "model": r.get("model", {}).get("model_name"),
                "granularity": r.get("model", {}).get("granularity"),
                "completion_rate": r.get("scores", {}).get("completion_rate"),
                "cost": r.get("model", {}).get("cost_multiplier"),
                "efficiency": r["efficiency"] if r["efficiency"] != float("inf") else "∞",
            }
            for i, r in enumerate(sorted_results)
        ],
        "best_l1": {
            "model": best_l1.get("model", {}).get("model_name") if best_l1 else None,
            "completion_rate": best_l1.get("scores", {}).get("completion_rate") if best_l1 else None,
        },
        "best_l3": {
            "model": best_l3.get("model", {}).get("model_name") if best_l3 else None,
            "completion_rate": best_l3.get("scores", {}).get("completion_rate") if best_l3 else None,
        },
        "best_efficiency": {
            "model": best_efficiency.get("model", {}).get("model_name") if best_efficiency else None,
            "granularity": best_efficiency.get("model", {}).get("granularity") if best_efficiency else None,
            "efficiency": best_efficiency["efficiency"] if best_efficiency and best_efficiency["efficiency"] != float("inf") else "∞",
        },
        "raw_results": results,
    }


def main():
    """Main entry point."""
    print("=" * 60)
    print("EXP-001 Results Aggregator")
    print("=" * 60)
    
    # Collect from worktrees
    print("\nCollecting results from worktrees...")
    results = collect_results_from_worktrees()
    
    if not results:
        print("\n❌ No results found!")
        print("   Make sure experiments have been run and save_results.py was executed.")
        return
    
    # Generate analysis
    print(f"\n📊 Found {len(results)} experiment results")
    analysis = generate_analysis(results)
    
    # Save aggregated results
    output_dir = Path(".experiments/EXP-001_L1-vs-L3-Granularity/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "AGGREGATED_RESULTS.json"
    with open(output_file, "w") as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\n✅ Aggregated results saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)
    
    print("\n📊 Cost-Effectiveness Ranking:")
    print("-" * 60)
    print(f"{'Rank':<5} {'Model':<30} {'Gran':<4} {'Score':<8} {'Cost':<6} {'Eff':<8}")
    print("-" * 60)
    
    for r in analysis["rankings"]:
        eff_str = f"{r['efficiency']:.1f}" if isinstance(r['efficiency'], (int, float)) else r['efficiency']
        print(f"{r['rank']:<5} {r['model'][:29]:<30} {r['granularity']:<4} {r['completion_rate']:<8} {r['cost']}x{'':<4} {eff_str:<8}")
    
    print("\n" + "-" * 60)
    print(f"🏆 Best L1: {analysis['best_l1']['model']} ({analysis['best_l1']['completion_rate']}%)")
    print(f"🏆 Best L3: {analysis['best_l3']['model']} ({analysis['best_l3']['completion_rate']}%)")
    print(f"🏆 Best Efficiency: {analysis['best_efficiency']['model']} ({analysis['best_efficiency']['granularity']}) - {analysis['best_efficiency']['efficiency']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
