#!/usr/bin/env python
"""
Regression testing report generator for BillOps.

Run this script to generate comprehensive test reports.
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path


def run_tests():
    """Run full test suite and generate report."""
    print("=" * 80)
    print("BillOps Regression Testing Suite")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    # Create reports directory
    reports_dir = Path("test_reports")
    reports_dir.mkdir(exist_ok=True)

    # Test configurations
    test_configs = [
        {
            "name": "Unit Tests",
            "cmd": ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"],
            "marker": "unit",
        },
        {
            "name": "Integration Tests",
            "cmd": ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"],
            "marker": "integration",
        },
        {
            "name": "End-to-End Tests",
            "cmd": ["python", "-m", "pytest", "tests/e2e/", "-v", "--tb=short"],
            "marker": "e2e",
        },
    ]

    results = {}
    total_passed = 0
    total_failed = 0
    total_skipped = 0

    for config in test_configs:
        print()
        print("-" * 80)
        print(f"Running: {config['name']}")
        print("-" * 80)

        try:
            # Run tests
            result = subprocess.run(
                config["cmd"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            output = result.stdout
            errors = result.stderr

            # Parse output
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            skipped = output.count(" SKIPPED")

            results[config["name"]] = {
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "return_code": result.returncode,
            }

            total_passed += passed
            total_failed += failed
            total_skipped += skipped

            # Print summary
            print(f"✓ Passed: {passed}")
            print(f"✗ Failed: {failed}")
            print(f"⊘ Skipped: {skipped}")
            print(f"Status: {results[config['name']]['status']}")

            # Print errors if any
            if failed > 0 or result.returncode != 0:
                print()
                print("Errors/Failures:")
                print(errors if errors else output)

        except subprocess.TimeoutExpired:
            print(f"✗ TIMEOUT: Test suite exceeded 5 minute limit")
            results[config["name"]] = {
                "status": "TIMEOUT",
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            }
            total_failed += 1

        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            results[config["name"]] = {
                "status": "ERROR",
                "passed": 0,
                "failed": 0,
                "skipped": 0,
            }
            total_failed += 1

    # Generate coverage report
    print()
    print("-" * 80)
    print("Code Coverage Report")
    print("-" * 80)

    try:
        coverage_result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "--cov=app", "--cov-report=html"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        print("✓ Coverage report generated: htmlcov/index.html")
    except Exception as e:
        print(f"⚠ Could not generate coverage report: {str(e)}")

    # Print final summary
    print()
    print("=" * 80)
    print("REGRESSION TEST SUMMARY")
    print("=" * 80)

    for test_name, result in results.items():
        status_symbol = "✓" if result["status"] == "PASSED" else "✗"
        print(f"{status_symbol} {test_name}")
        print(
            f"  Passed: {result['passed']}, Failed: {result['failed']}, Skipped: {result['skipped']}"
        )

    print()
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Total Skipped: {total_skipped}")
    print(f"Total Tests: {total_passed + total_failed + total_skipped}")

    # Overall status
    overall_status = "PASSED" if total_failed == 0 else "FAILED"
    status_symbol = "✓" if overall_status == "PASSED" else "✗"
    print()
    print(f"{status_symbol} Overall Status: {overall_status}")
    print(f"Completed at: {datetime.now().isoformat()}")
    print("=" * 80)

    # Save report
    report_file = reports_dir / f"regression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "overall_status": overall_status,
        },
    }

    with open(report_file, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"Report saved to: {report_file}")

    return 0 if overall_status == "PASSED" else 1


if __name__ == "__main__":
    sys.exit(run_tests())
