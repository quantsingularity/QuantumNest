"""
Test runner for QuantumNest Capital backend
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(command: Any, description: Any) -> Any:
    """Run a command and return the result"""
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Running: {description}")
    logger.info(f"Command: {command}")
    logger.info(f"{'=' * 60}")
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=300
        )
        if result.stdout:
            logger.info("STDOUT:")
            logger.info(result.stdout)
        if result.stderr:
            logger.info("STDERR:")
            logger.info(result.stderr)
        logger.info(f"Return code: {result.returncode}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.info("ERROR: Command timed out after 5 minutes")
        return False
    except Exception as e:
        logger.info(f"ERROR: {str(e)}")
        return False


def check_syntax() -> Any:
    """Check Python syntax for all files"""
    logger.info("\n" + "=" * 80)
    logger.info("CHECKING PYTHON SYNTAX")
    logger.info("=" * 80)
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
            logger.info(f"✓ {file_path}")
        except subprocess.CalledProcessError as e:
            logger.info(f"✗ {file_path}: {e.stderr.decode()}")
            failed_files.append(str(file_path))
    if failed_files:
        logger.info(f"\nSyntax errors found in {len(failed_files)} files:")
        for file_path in failed_files:
            logger.info(f"  - {file_path}")
        return False
    else:
        logger.info(f"\n✓ All {len(python_files)} Python files have valid syntax")
        return True


def check_imports() -> Any:
    """Check if all imports can be resolved"""
    logger.info("\n" + "=" * 80)
    logger.info("CHECKING IMPORTS")
    logger.info("=" * 80)
    test_script = '\nimport sys\n\nfrom core.logging import get_logger\nlogger = get_logger(__name__)\nsys.path.insert(0, \'.\')\n\ntry:\n    # Test core imports\n    from app.core.config import get_settings\n    from app.core.logging import get_logger\n    from app.models.models import User, Account, Portfolio, Transaction\n    logger.info("✓ Core imports successful")\n    # Test auth imports\n    from app.auth.authentication import AdvancedAuthenticationSystem\n    from app.auth.authorization import RoleBasedAccessControl\n    logger.info("✓ Auth imports successful")\n    # Test service imports\n    from app.services.trading_service import TradingService\n    from app.services.market_data_service import MarketDataService\n    from app.services.risk_management_service import RiskManagementService\n    logger.info("✓ Service imports successful")\n    # Test AI imports\n    from app.ai.fraud_detection import AdvancedFraudDetectionSystem\n    from app.ai.financial_advisor import AIFinancialAdvisor\n    from app.ai.portfolio_optimization import PortfolioOptimizer\n    logger.info("✓ AI imports successful")\n    # Test utility imports\n    from app.utils.encryption import encryption_manager\n    logger.info("✓ Utility imports successful")\n    logger.info("\\n✓ All imports successful")\nexcept ImportError as e:\n    logger.info(f"✗ Import error: {e}")\n    sys.exit(1)\nexcept Exception as e:\n    logger.info(f"✗ Unexpected error: {e}")\n    sys.exit(1)\n'
    with open("test_imports.py", "w") as f:
        f.write(test_script)
    try:
        result = subprocess.run(
            [sys.executable, "test_imports.py"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        logger.info(result.stdout)
        if result.stderr:
            logger.info("STDERR:")
            logger.info(result.stderr)
        success = result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.info("✗ Import check timed out")
        success = False
    except Exception as e:
        logger.info(f"✗ Import check failed: {e}")
        success = False
    finally:
        if os.path.exists("test_imports.py"):
            os.remove("test_imports.py")
    return success


def run_unit_tests() -> Any:
    """Run unit tests"""
    if not os.path.exists("tests"):
        logger.info("No tests directory found, skipping unit tests")
        return True
    return run_command("python -m pytest tests/ -v --tb=short", "Unit Tests")


def check_code_quality() -> Any:
    """Check code quality with basic linting"""
    logger.info("\n" + "=" * 80)
    logger.info("CHECKING CODE QUALITY")
    logger.info("=" * 80)
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
        logger.info(f"\n{description}:")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            if result.stdout.strip():
                logger.info(result.stdout)
            if result.stderr.strip():
                logger.info(f"Error: {result.stderr}")
                all_passed = False
        except Exception as e:
            logger.info(f"Error running check: {e}")
            all_passed = False
    return all_passed


def check_security() -> Any:
    """Basic security checks"""
    logger.info("\n" + "=" * 80)
    logger.info("CHECKING SECURITY")
    logger.info("=" * 80)
    security_issues = []
    try:
        result = subprocess.run(
            "grep -r 'password.*=.*[\"\\']' app/ | grep -v 'password_hash' | grep -v 'hashed_password' || echo 'No hardcoded passwords found'",
            shell=True,
            capture_output=True,
            text=True,
        )
        if "No hardcoded passwords found" not in result.stdout:
            security_issues.append("Potential hardcoded passwords found")
            logger.info("⚠️  Potential hardcoded passwords:")
            logger.info(result.stdout)
        else:
            logger.info("✓ No hardcoded passwords found")
    except Exception as e:
        logger.info(f"Error checking for hardcoded passwords: {e}")
    try:
        result = subprocess.run(
            "grep -r 'execute.*%\\|query.*%\\|SELECT.*%' app/ || echo 'No SQL injection patterns found'",
            shell=True,
            capture_output=True,
            text=True,
        )
        if "No SQL injection patterns found" not in result.stdout:
            security_issues.append("Potential SQL injection patterns found")
            logger.info("⚠️  Potential SQL injection patterns:")
            logger.info(result.stdout)
        else:
            logger.info("✓ No SQL injection patterns found")
    except Exception as e:
        logger.info(f"Error checking for SQL injection: {e}")
    try:
        result = subprocess.run(
            "grep -r 'debug.*=.*True' app/ || echo 'No debug mode found'",
            shell=True,
            capture_output=True,
            text=True,
        )
        if "No debug mode found" not in result.stdout:
            security_issues.append("Debug mode enabled")
            logger.info("⚠️  Debug mode enabled:")
            logger.info(result.stdout)
        else:
            logger.info("✓ No debug mode enabled")
    except Exception as e:
        logger.info(f"Error checking for debug mode: {e}")
    if security_issues:
        logger.info(f"\n⚠️  {len(security_issues)} security issues found:")
        for issue in security_issues:
            logger.info(f"  - {issue}")
        return False
    else:
        logger.info("\n✓ No security issues found")
        return True


def main() -> Any:
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
    if not any([args.syntax, args.imports, args.tests, args.quality, args.security]):
        args.all = True
    logger.info("QuantumNest Capital Backend Test Runner")
    logger.info("=" * 80)
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
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    passed = 0
    total = len(results)
    for check, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{check.upper():<15}: {status}")
        if result:
            passed += 1
    logger.info(f"\nOverall: {passed}/{total} checks passed")
    if passed == total:
        logger.info("🎉 All checks passed! The code is ready for deployment.")
        sys.exit(0)
    else:
        logger.info("❌ Some checks failed. Please review and fix the issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
