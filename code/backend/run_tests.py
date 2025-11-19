#!/usr/bin/env python3
"""
Test runner for QuantumNest Capital backend
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
        )

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"Return code: {result.returncode}")
        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


def check_syntax():
    """Check Python syntax for all files"""
    print("\n" + "=" * 80)
    print("CHECKING PYTHON SYNTAX")
    print("=" * 80)

    python_files = list(Path("app").rglob("*.py"))
    python_files.extend(list(Path("tests").rglob("*.py")))

    failed_files = []

    for file_path in python_files:
        try:
            subprocess.run(
                [sys.executable, "-m", "py_compile", str(file_path)],
                check=True,
                capture_output=True,
            )
            print(f"✓ {file_path}")
        except subprocess.CalledProcessError as e:
            print(f"✗ {file_path}: {e.stderr.decode()}")
            failed_files.append(str(file_path))

    if failed_files:
        print(f"\nSyntax errors found in {len(failed_files)} files:")
        for file_path in failed_files:
            print(f"  - {file_path}")
        return False
    else:
        print(f"\n✓ All {len(python_files)} Python files have valid syntax")
        return True


def check_imports():
    """Check if all imports can be resolved"""
    print("\n" + "=" * 80)
    print("CHECKING IMPORTS")
    print("=" * 80)

    test_script = """
import sys
sys.path.insert(0, '.')

try:
    # Test core imports
    from app.core.config import get_settings
    from app.core.logging import get_logger
    from app.models.models import User, Account, Portfolio, Transaction
    print("✓ Core imports successful")

    # Test auth imports
    from app.auth.authentication import AdvancedAuthenticationSystem
    from app.auth.authorization import RoleBasedAccessControl
    print("✓ Auth imports successful")

    # Test service imports
    from app.services.trading_service import TradingService
    from app.services.market_data_service import MarketDataService
    from app.services.risk_management_service import RiskManagementService
    print("✓ Service imports successful")

    # Test AI imports
    from app.ai.fraud_detection import AdvancedFraudDetectionSystem
    from app.ai.financial_advisor import AIFinancialAdvisor
    from app.ai.portfolio_optimization import PortfolioOptimizer
    print("✓ AI imports successful")

    # Test utility imports
    from app.utils.encryption import encryption_manager
    print("✓ Utility imports successful")

    print("\\n✓ All imports successful")

except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
"""

    with open("test_imports.py", "w") as f:
        f.write(test_script)

    try:
        result = subprocess.run(
            [sys.executable, "test_imports.py"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        success = result.returncode == 0

    except subprocess.TimeoutExpired:
        print("✗ Import check timed out")
        success = False
    except Exception as e:
        print(f"✗ Import check failed: {e}")
        success = False
    finally:
        # Clean up
        if os.path.exists("test_imports.py"):
            os.remove("test_imports.py")

    return success


def run_unit_tests():
    """Run unit tests"""
    if not os.path.exists("tests"):
        print("No tests directory found, skipping unit tests")
        return True

    return run_command("python -m pytest tests/ -v --tb=short", "Unit Tests")


def check_code_quality():
    """Check code quality with basic linting"""
    print("\n" + "=" * 80)
    print("CHECKING CODE QUALITY")
    print("=" * 80)

    # Basic code quality checks
    checks = [
        (
            "Line length check",
            "find app -name '*.py' -exec wc -L {} + | awk '$1 > 120 {print $2 \" has lines longer than 120 characters\"}'",
        ),
        (
            "TODO/FIXME check",
            "grep -r 'TODO\\|FIXME\\|XXX' app/ || echo 'No TODO/FIXME/XXX found'",
        ),
        (
            "Print statement check",
            "grep -r 'print(' app/ | grep -v logger | grep -v '# debug' || echo 'No problematic print statements found'",
        ),
    ]

    all_passed = True

    for description, command in checks:
        print(f"\n{description}:")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )

            if result.stdout.strip():
                print(result.stdout)

            if result.stderr.strip():
                print(f"Error: {result.stderr}")
                all_passed = False

        except Exception as e:
            print(f"Error running check: {e}")
            all_passed = False

    return all_passed


def check_security():
    """Basic security checks"""
    print("\n" + "=" * 80)
    print("CHECKING SECURITY")
    print("=" * 80)

    security_issues = []

    # Check for hardcoded secrets
    try:
        result = subprocess.run(
            "grep -r 'password.*=.*[\"\\']' app/ | grep -v 'password_hash' | grep -v 'hashed_password' || echo 'No hardcoded passwords found'",
            shell=True,
            capture_output=True,
            text=True,
        )

        if "No hardcoded passwords found" not in result.stdout:
            security_issues.append("Potential hardcoded passwords found")
            print("⚠️  Potential hardcoded passwords:")
            print(result.stdout)
        else:
            print("✓ No hardcoded passwords found")

    except Exception as e:
        print(f"Error checking for hardcoded passwords: {e}")

    # Check for SQL injection patterns
    try:
        result = subprocess.run(
            "grep -r 'execute.*%\\|query.*%\\|SELECT.*%' app/ || echo 'No SQL injection patterns found'",
            shell=True,
            capture_output=True,
            text=True,
        )

        if "No SQL injection patterns found" not in result.stdout:
            security_issues.append("Potential SQL injection patterns found")
            print("⚠️  Potential SQL injection patterns:")
            print(result.stdout)
        else:
            print("✓ No SQL injection patterns found")

    except Exception as e:
        print(f"Error checking for SQL injection: {e}")

    # Check for debug mode in production
    try:
        result = subprocess.run(
            "grep -r 'debug.*=.*True' app/ || echo 'No debug mode found'",
            shell=True,
            capture_output=True,
            text=True,
        )

        if "No debug mode found" not in result.stdout:
            security_issues.append("Debug mode enabled")
            print("⚠️  Debug mode enabled:")
            print(result.stdout)
        else:
            print("✓ No debug mode enabled")

    except Exception as e:
        print(f"Error checking for debug mode: {e}")

    if security_issues:
        print(f"\n⚠️  {len(security_issues)} security issues found:")
        for issue in security_issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✓ No security issues found")
        return True


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="QuantumNest Capital Test Runner")
    parser.add_argument("--syntax", action="store_true", help="Check syntax only")
    parser.add_argument("--imports", action="store_true", help="Check imports only")
    parser.add_argument("--tests", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--quality", action="store_true", help="Check code quality only"
    )
    parser.add_argument("--security", action="store_true", help="Check security only")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")

    args = parser.parse_args()

    # If no specific check is requested, run all
    if not any([args.syntax, args.imports, args.tests, args.quality, args.security]):
        args.all = True

    print("QuantumNest Capital Backend Test Runner")
    print("=" * 80)

    results = {}

    if args.all or args.syntax:
        results["syntax"] = check_syntax()

    if args.all or args.imports:
        results["imports"] = check_imports()

    if args.all or args.tests:
        results["tests"] = run_unit_tests()

    if args.all or args.quality:
        results["quality"] = check_code_quality()

    if args.all or args.security:
        results["security"] = check_security()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = 0
    total = len(results)

    for check, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{check.upper():<15}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All checks passed! The code is ready for deployment.")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please review and fix the issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
