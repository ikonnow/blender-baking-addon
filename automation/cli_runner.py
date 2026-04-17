import sys
import unittest
import argparse
import bpy
import os
from pathlib import Path

try:
    from env_setup import setup_environment
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from env_setup import setup_environment

AVAILABLE_SUITES = [
    "unit",
    "shading",
    "negative",
    "memory",
    "export",
    "api",
    "context_lifecycle",
    "cleanup",
    "denoise",
    "parameter_matrix",
    "preset",
    "production_workflow",
    "udim_advanced",
    "ui_logic",
    "code_review",
]


def main():
    parser = argparse.ArgumentParser(description="BakeTool Unified CLI Test Runner")
    parser.add_argument(
        "--suite",
        type=str,
        default="all",
        choices=["all"] + AVAILABLE_SUITES,
        help="Run a specific test suite or 'all' suites",
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Run a specific test case (e.g. baketool.test_cases.suite_api.SuiteAPI)",
    )
    parser.add_argument(
        "--discover", action="store_true", help="Discover and run all suite_*.py files"
    )
    parser.add_argument(
        "--json", type=str, help="Path to save the test results as JSON"
    )
    parser.add_argument(
        "--category",
        type=str,
        default="all",
        choices=["all", "core", "memory", "export", "ui", "integration"],
        help="Run tests by category (memory=memory tests, export=export tests, etc.)",
    )
    parser.add_argument(
        "--list", action="store_true", help="List all available test suites"
    )

    if "--" in sys.argv:
        args_idx = sys.argv.index("--") + 1
        cli_args = sys.argv[args_idx:]
    else:
        cli_args = []

    args = parser.parse_args(cli_args)

    addon_name, addon_root = setup_environment()
    parent_dir = str(addon_root.parent)
    test_dir = str(addon_root / "test_cases")

    if args.list:
        print("\n>>> Available Test Suites:")
        for s in AVAILABLE_SUITES:
            print(f"    - {s}")
        print("\n>>> Available Categories:")
        print("    - all: All tests")
        print("    - core: Core functionality tests")
        print("    - memory: Memory and leak tests")
        print("    - export: Export safety tests")
        print("    - ui: UI and panel tests")
        print("    - integration: Integration tests")
        return

    try:
        import baketool

        try:
            baketool.unregister()
        except Exception:
            pass
        baketool.register()
        print(">>> Addon registered successfully.")

        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        if args.test:
            print(f">>> Loading specific test: {args.test}")
            suite = loader.loadTestsFromName(args.test)
        elif args.discover:
            print(">>> Discovering all suite_*.py...")
            suite = loader.discover(
                start_dir=test_dir, pattern="suite_*.py", top_level_dir=parent_dir
            )
        elif args.category != "all":
            print(f">>> Loading tests by category: {args.category}")
            suite = _load_category(args.category, loader)
        else:
            if args.suite == "all":
                pattern = "suite_*.py"
            else:
                pattern = f"suite_{args.suite}.py"
            print(f">>> Loading suites matching pattern: {pattern}")
            suite = loader.discover(
                start_dir=test_dir, pattern=pattern, top_level_dir=parent_dir
            )

        print(f">>> Running {suite.countTestCases()} tests...")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if args.json:
            import json
            import time

            report = {
                "timestamp": time.time(),
                "blender_version": list(bpy.app.version),
                "blender_version_str": bpy.app.version_string,
                "os": sys.platform,
                "summary": {
                    "total": result.testsRun,
                    "passed": result.testsRun
                    - len(result.failures)
                    - len(result.errors),
                    "failures": len(result.failures),
                    "errors": len(result.errors),
                    "skipped": len(result.skipped),
                },
                "details": {
                    "failures": [str(f[0]) + ": " + str(f[1]) for f in result.failures],
                    "errors": [str(e[0]) + ": " + str(e[1]) for e in result.errors],
                },
            }
            json_path = Path(args.json)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4)
            print(f">>> JSON Report saved to: {args.json}")

        if result.wasSuccessful():
            print("\n>>> CONSOLIDATED SUITES PASSED")
            print(">>> ALL TESTS PASSED")
            sys.exit(0)
        else:
            print("\n>>> TESTS FAILED")
            sys.exit(1)

    except Exception as e:
        import traceback

        traceback.print_exc()
        sys.exit(1)


def _load_category(category, loader):
    """Load test suites by category."""
    suite = unittest.TestSuite()
    test_dir = str(Path(__file__).parent.parent / "test_cases")
    parent_dir = str(Path(__file__).parent.parent.parent)

    category_map = {
        "core": ["suite_unit.py", "suite_negative.py", "suite_api.py"],
        "memory": ["suite_memory.py"],
        "export": ["suite_export.py"],
        "ui": ["suite_ui_logic.py"],
        "integration": ["suite_production_workflow.py", "suite_context_lifecycle.py"],
    }

    patterns = category_map.get(category, ["suite_*.py"])

    for pattern in patterns:
        discovered = loader.discover(
            start_dir=test_dir, pattern=pattern, top_level_dir=parent_dir
        )
        suite.addTests(discovered)

    return suite


if __name__ == "__main__":
    main()
