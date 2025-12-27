#!/usr/bin/env python
"""Quick validation for solo-dev environment.

A streamlined validation script for fast feedback during development.
Runs essential checks without full schema generation.

Usage:
    python tools/quick_validate.py           # Quick validation
    python tools/quick_validate.py --watch   # Watch mode (re-run on changes)
    python tools/quick_validate.py --fix     # Auto-fix simple issues
"""

import argparse
import importlib
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ANSI colors for terminal
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_imports() -> tuple[int, int]:
    """Quick check that all contract modules import successfully."""
    modules = [
        "shared.contracts.core.dataset",
        "shared.contracts.core.pipeline",
        "shared.contracts.core.audit",
        "shared.contracts.core.id_generator",
        "shared.contracts.core.rendering",
        "shared.contracts.dat.stage",
        "shared.contracts.dat.cancellation",
        "shared.contracts.pptx.template",
        "shared.contracts.sov.anova",
        "shared.contracts.messages.catalog",
        "shared.contracts.devtools.api",
    ]
    
    passed = 0
    failed = 0
    
    for module in modules:
        try:
            importlib.import_module(module)
            importlib.reload(sys.modules[module])  # Force reload for watch mode
            passed += 1
        except Exception as e:
            print(f"  {RED}✗{RESET} {module}: {e}")
            failed += 1
    
    return passed, failed


def check_versions() -> tuple[int, int]:
    """Check that contract modules have __version__."""
    modules = [
        "shared.contracts",
        "shared.contracts.core",
        "shared.contracts.dat",
        "shared.contracts.messages",
    ]
    
    passed = 0
    warnings = 0
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "__version__"):
                passed += 1
            else:
                print(f"  {YELLOW}⚠{RESET} {module_name}: missing __version__")
                warnings += 1
        except ImportError:
            pass
    
    return passed, warnings


def check_pydantic_schemas() -> tuple[int, int]:
    """Quick check that key models can generate JSON schemas."""
    from pydantic import BaseModel
    
    key_models = [
        ("shared.contracts.core.dataset", "DataSetManifest"),
        ("shared.contracts.core.pipeline", "Pipeline"),
        ("shared.contracts.core.audit", "AuditTrail"),
        ("shared.contracts.core.id_generator", "IDConfig"),
        ("shared.contracts.dat.cancellation", "CancellationRequest"),
        ("shared.contracts.messages.catalog", "MessageCatalog"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, model_name in key_models:
        try:
            module = importlib.import_module(module_name)
            model = getattr(module, model_name)
            model.model_json_schema()
            passed += 1
        except Exception as e:
            print(f"  {RED}✗{RESET} {model_name}: {e}")
            failed += 1
    
    return passed, failed


def run_validation() -> bool:
    """Run quick validation suite."""
    print(f"\n{BOLD}Quick Contract Validation{RESET}")
    print("=" * 40)
    
    all_passed = True
    
    # Check imports
    print(f"\n{BOLD}[1/3] Contract Imports{RESET}")
    passed, failed = check_imports()
    if failed > 0:
        all_passed = False
    print(f"      {passed} passed, {failed} failed")
    
    # Check versions
    print(f"\n{BOLD}[2/3] Contract Versioning{RESET}")
    passed, warnings = check_versions()
    print(f"      {passed} versioned, {warnings} warnings")
    
    # Check schemas
    print(f"\n{BOLD}[3/3] JSON Schema Generation{RESET}")
    passed, failed = check_pydantic_schemas()
    if failed > 0:
        all_passed = False
    print(f"      {passed} passed, {failed} failed")
    
    # Summary
    print("\n" + "=" * 40)
    if all_passed:
        print(f"{GREEN}{BOLD}✓ All checks passed{RESET}")
    else:
        print(f"{RED}{BOLD}✗ Some checks failed{RESET}")
    
    return all_passed


def watch_mode() -> None:
    """Watch for changes and re-run validation."""
    print(f"\n{BOLD}Watch Mode{RESET} - Press Ctrl+C to exit")
    print("Watching: shared/contracts/")
    
    contracts_dir = PROJECT_ROOT / "shared" / "contracts"
    
    def get_mtimes() -> dict[Path, float]:
        return {
            p: p.stat().st_mtime
            for p in contracts_dir.rglob("*.py")
            if "__pycache__" not in str(p)
        }
    
    last_mtimes = get_mtimes()
    run_validation()
    
    try:
        while True:
            time.sleep(1)
            current_mtimes = get_mtimes()
            
            changed = [
                p for p, mtime in current_mtimes.items()
                if p not in last_mtimes or last_mtimes[p] != mtime
            ]
            
            if changed:
                print(f"\n{YELLOW}Changed:{RESET} {[p.name for p in changed]}")
                
                # Clear module cache for changed files
                for p in changed:
                    module_name = str(p.relative_to(PROJECT_ROOT)).replace("/", ".").replace("\\", ".")[:-3]
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                
                run_validation()
                last_mtimes = current_mtimes
                
    except KeyboardInterrupt:
        print("\n\nExiting watch mode.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick contract validation")
    parser.add_argument("--watch", action="store_true", help="Watch mode")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues (placeholder)")
    args = parser.parse_args()
    
    if args.watch:
        watch_mode()
        return 0
    
    success = run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
