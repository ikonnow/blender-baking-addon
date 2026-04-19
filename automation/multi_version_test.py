import subprocess
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

env_paths_str = os.environ.get("BLENDER_PATHS", "")
BLENDER_PATHS = [p.strip() for p in env_paths_str.split(";") if p.strip()]

if not BLENDER_PATHS:
    BLENDER_PATHS = [
        r"D:\Program Files\blender-3.3\blender.exe",
        r"D:\Program Files\Blender-3.6\blender.exe",
        r"D:\Program Files\blender-4.2\blender.exe",
        r"D:\Program Files\blender-4.5\blender.exe",
        r"D:\Program Files\blender-5.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.3\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
    ]

current_dir = str(Path(__file__).resolve().parent)
runner_script = str(Path(current_dir) / "cli_runner.py")


def get_blender_version(path):
    try:
        res = subprocess.run(
            [path, "--version"], capture_output=True, text=True, check=True
        )
        return res.stdout.splitlines()[0]
    except Exception:
        return "Unknown Version"


def run_tests_on_blender(blender_path, suite="all", category=None, verification=False):
    """Run tests on a specific Blender version."""
    # All tests now run through cli_runner.py
    cmd = [blender_path, "--background", "--factory-startup", "--python", runner_script]

    if verification:
        cmd.extend(["--", "--suite", "verification"])
    else:
        if suite != "all":
            cmd.extend(["--", "--suite", suite])
        if category:
            cmd.extend(["--", "--category", category])

    test_env = os.environ.copy()
    test_env["PYTHONIOENCODING"] = "utf-8"

    try:
        process = subprocess.run(
            cmd, capture_output=True, env=test_env, check=False, timeout=300
        )

        stdout = process.stdout.decode("utf-8", errors="replace")
        stderr = process.stderr.decode("utf-8", errors="replace")

        # Success is determined by cli_runner.py output
        success = (
            "CONSOLIDATED SUITES PASSED" in stdout
            or "ALL TESTS PASSED" in stdout
        )
        return {
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": process.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Timeout", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


def main():
    parser = argparse.ArgumentParser(description="BakeTool Multi-Version Test Runner")
    parser.add_argument(
        "--suite",
        type=str,
        default="all",
        help="Test suite to run (all, memory, export, etc.)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Test category to run (core, memory, export, etc.)",
    )
    parser.add_argument(
        "--verification",
        action="store_true",
        help="Run comprehensive verification suite",
    )
    parser.add_argument(
        "--json", type=str, default=None, help="Save detailed results as JSON"
    )
    parser.add_argument(
        "--list", action="store_true", help="List available Blender versions"
    )

    args, unknown = parser.parse_known_args()

    print("\n" + "=" * 80)
    print("      BAKETOOL v1.0.0 CROSS-VERSION TEST SUITE")
    print("=" * 80)
    print(f"  Test Mode: {'Verification' if args.verification else 'Unit Tests'}")
    if args.suite != "all":
        print(f"  Suite: {args.suite}")
    if args.category:
        print(f"  Category: {args.category}")
    print("=" * 80)

    if args.list:
        print("\n>>> Searching for Blender installations...")
        valid_paths = [p for p in BLENDER_PATHS if Path(p).exists()]
        if valid_paths:
            print("\n  Found Blender versions:")
            for p in valid_paths:
                ver = get_blender_version(p)
                print(f"    - {ver}: {p}")
        else:
            print("\n  No Blender installations found in default paths.")
            print("  Set BLENDER_PATHS environment variable to specify paths.")
        return

    results = []
    valid_paths = [p for p in BLENDER_PATHS if Path(p).exists()]

    if not valid_paths:
        print("\n[ERROR] No valid Blender executables found.")
        print(
            "Set BLENDER_PATHS environment variable (semicolon-separated) or edit multi_version_test.py"
        )
        return

    print(f"\n>>> Testing {len(valid_paths)} Blender versions...\n")
    print(f"{'Blender Version':<40} | {'Status':<10}")
    print("-" * 80)

    total_pass = 0
    total_fail = 0

    for path in valid_paths:
        full_ver = get_blender_version(path)
        ver_short = full_ver[:35] if len(full_ver) > 35 else full_ver

        result = run_tests_on_blender(
            path,
            suite=args.suite,
            category=args.category,
            verification=args.verification,
        )

        if result["success"]:
            status = "PASS"
            status_color = "\033[92m"
            total_pass += 1
        else:
            status = "FAIL"
            status_color = "\033[91m"
            total_fail += 1

        print(f"{ver_short:<40} | {status_color}{status:<10}\033[0m")

        if not result["success"]:
            # Print a snippet of stderr for debugging
            if result["stderr"]:
                print(f"    | Stderr Snippet: {result['stderr'][:200]}...")
            elif result["stdout"]:
                print(f"    | Last Output: {result['stdout'].splitlines()[-5:]}")

        results.append(
            {
                "version": full_ver,
                "path": path,
                "status": status,
                "success": result["success"],
                "stderr": result["stderr"],
                "timestamp": datetime.now().isoformat(),
            }
        )

    print("-" * 80)
    print(f"\n  SUMMARY: {total_pass} PASS | {total_fail} FAIL")

    report_dir = Path(current_dir).parent / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"cross_version_report_{timestamp}.txt"
    json_path = report_dir / f"cross_version_report_{timestamp}.json"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("BAKETOOL v1.0.0 CROSS-VERSION TEST REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Test Mode: {'Verification' if args.verification else 'Unit Tests'}\n")
        f.write("=" * 60 + "\n\n")
        f.write("RESULTS:\n")
        for r in results:
            f.write(f"\n[{r['status']}] {r['version']}\n")
            f.write(f"  Path: {r['path']}\n")
            if r["stderr"]:
                f.write(f"  Error: {r['stderr'][:500]}\n")
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"SUMMARY: {total_pass} PASS | {total_fail} FAIL\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "test_mode": "verification" if args.verification else "unit_tests",
                "suite": args.suite,
                "category": args.category,
                "summary": {"pass": total_pass, "fail": total_fail},
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\n>>> Reports saved:")
    print(f"    Text: {report_path.resolve()}")
    print(f"    JSON: {json_path.resolve()}")
    print("=" * 80 + "\n")

    return total_fail == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
