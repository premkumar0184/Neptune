#!/usr/bin/env python3
"""
PhotoGIMP Unified Test Runner & Quality Gate

Executes:
1. PhotoGIMP Configuration & Shortcut Validator (verify_config.py)
2. PhotoGIMP Installer Verification (install.sh --batch)
3. Headless GIMP Plugin Suite End-to-End Regression Suite (tests/gimp_e2e_suite.py)

Usage:
  python3 tests/run_all_tests.py
"""

import os
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
VERIFY_SCRIPT = os.path.join(PROJECT_ROOT, "PhotoGIMP", "scripts", "verify_config.py")
INSTALL_SCRIPT = os.path.join(PROJECT_ROOT, "PhotoGIMP", "install.sh")
E2E_SUITE = os.path.join(SCRIPT_DIR, "gimp_e2e_suite.py")


def print_header(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def run_stage(title, cmd, cwd=PROJECT_ROOT):
    print_header(title)
    print(f"Executing: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    start = time.time()
    result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str))
    elapsed = time.time() - start
    print(f"Stage completed in {elapsed:.2f}s with exit code {result.returncode}")
    if result.returncode != 0:
        print(f"\n[ERROR] Stage '{title}' failed with exit code {result.returncode}")
        return False
    return True


def main():
    print("*" * 70)
    print(" PhotoGIMP / Linux Photo Editor Quality Gate & Regression Runner")
    print("*" * 70)

    stages = [
        (
            "Stage 1: Configuration & Plugin Inventory Audit",
            [sys.executable, VERIFY_SCRIPT],
        ),
        (
            "Stage 2: Installer Non-Interactive Deployment Test",
            [INSTALL_SCRIPT, "--batch"],
        ),
        (
            "Stage 3: Headless GIMP Plugin Suite Regression Verification",
            [
                "gimp",
                "--no-interface",
                "--console-messages",
                "--batch-interpreter=python-fu-eval",
                "--batch",
                f"exec(open('{E2E_SUITE}').read())",
                "--quit",
            ],
        ),
    ]

    total_start = time.time()
    all_passed = True

    for title, cmd in stages:
        success = run_stage(title, cmd)
        if not success:
            all_passed = False
            break

    total_elapsed = time.time() - total_start

    print_header("FINAL QUALITY GATE SUMMARY")
    if all_passed:
        print(f"[SUCCESS] All quality gate stages passed in {total_elapsed:.2f}s!")
        print("Product features and Photoshop workflows are fully verified.")
        sys.exit(0)
    else:
        print(f"[FAILURE] Quality gate failed after {total_elapsed:.2f}s.")
        sys.exit(1)


if __name__ == "__main__":
    main()
