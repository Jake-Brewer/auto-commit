#!/usr/bin/env python3
"""
Comprehensive test runner for auto-commit project.
Provides different test categories and detailed reporting.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any


class TestRunner:
    """Test runner with multiple test categories and reporting."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
        self.results = {}
    
    def run_command(self, cmd: List[str], description: str) -> Dict[str, Any]:
        """Run a command and capture results."""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            duration = time.time() - start_time
            
            print(f"Exit code: {result.returncode}")
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration,
                "description": description
            }
        except Exception as e:
            duration = time.time() - start_time
            print(f"Error running command: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": duration,
                "description": description
            }
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "-v",
            "-m", "not integration",
            "--tb=short"
        ]
        return self.run_command(cmd, "Unit Tests")
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "-v",
            "-m", "integration",
            "--tb=short"
        ]
        return self.run_command(cmd, "Integration Tests")
    
    def run_coverage_tests(self) -> Dict[str, Any]:
        """Run tests with coverage reporting."""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=80"
        ]
        return self.run_command(cmd, "Coverage Tests")
    
    def run_linting(self) -> Dict[str, Any]:
        """Run code linting."""
        cmd = [
            sys.executable, "-m", "flake8",
            str(self.src_dir),
            str(self.tests_dir)
        ]
        return self.run_command(cmd, "Linting (flake8)")
    
    def run_type_checking(self) -> Dict[str, Any]:
        """Run type checking."""
        cmd = [
            sys.executable, "-m", "mypy",
            str(self.src_dir)
        ]
        return self.run_command(cmd, "Type Checking (mypy)")
    
    def run_formatting_check(self) -> Dict[str, Any]:
        """Check code formatting."""
        black_cmd = [
            sys.executable, "-m", "black",
            "--check",
            str(self.src_dir),
            str(self.tests_dir)
        ]
        black_result = self.run_command(black_cmd, "Formatting Check (black)")
        
        isort_cmd = [
            sys.executable, "-m", "isort",
            "--check-only",
            str(self.src_dir),
            str(self.tests_dir)
        ]
        isort_result = self.run_command(isort_cmd, "Import Sorting Check (isort)")
        
        return {
            "success": black_result["success"] and isort_result["success"],
            "black": black_result,
            "isort": isort_result,
            "description": "Code Formatting Checks"
        }
    
    def run_security_checks(self) -> Dict[str, Any]:
        """Run security checks."""
        bandit_cmd = [
            sys.executable, "-m", "bandit",
            "-r", str(self.src_dir)
        ]
        bandit_result = self.run_command(bandit_cmd, "Security Check (bandit)")
        
        try:
            safety_cmd = [sys.executable, "-m", "safety", "check"]
            safety_result = self.run_command(safety_cmd, "Dependency Security (safety)")
        except Exception:
            safety_result = {
                "success": True,
                "description": "Dependency Security (safety) - skipped"
            }
        
        return {
            "success": bandit_result["success"] and safety_result["success"],
            "bandit": bandit_result,
            "safety": safety_result,
            "description": "Security Checks"
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.tests_dir),
            "--benchmark-only",
            "-v"
        ]
        return self.run_command(cmd, "Performance Benchmarks")
    
    def generate_report(self) -> None:
        """Generate comprehensive test report."""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE TEST REPORT")
        print(f"{'='*80}")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r.get("success", False))
        failed_tests = total_tests - passed_tests
        
        print(f"Total test categories: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n{'='*80}")
        print("DETAILED RESULTS")
        print(f"{'='*80}")
        
        for category, result in self.results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            duration = result.get("duration", 0)
            print(f"{status} {category:<30} ({duration:.2f}s)")
            
            if not result.get("success", False) and result.get("stderr"):
                print(f"    Error: {result['stderr'][:100]}...")
        
        # Generate HTML report if coverage was run
        coverage_html = self.project_root / "htmlcov" / "index.html"
        if coverage_html.exists():
            print(f"\n📊 Coverage report: file://{coverage_html.absolute()}")
        
        print(f"\n{'='*80}")
        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print(f"⚠️  {failed_tests} TEST CATEGORIES FAILED")
        print(f"{'='*80}")
    
    def run_all_tests(self) -> bool:
        """Run all test categories."""
        print("🚀 Starting comprehensive test suite...")
        
        # Core tests
        self.results["unit_tests"] = self.run_unit_tests()
        self.results["integration_tests"] = self.run_integration_tests()
        self.results["coverage"] = self.run_coverage_tests()
        
        # Code quality
        self.results["linting"] = self.run_linting()
        self.results["type_checking"] = self.run_type_checking()
        self.results["formatting"] = self.run_formatting_check()
        
        # Security
        self.results["security"] = self.run_security_checks()
        
        # Performance (optional)
        try:
            self.results["performance"] = self.run_performance_tests()
        except Exception:
            print("⚠️  Performance tests skipped (pytest-benchmark not available)")
        
        self.generate_report()
        
        # Return overall success
        return all(r.get("success", False) for r in self.results.values())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Comprehensive test runner")
    parser.add_argument(
        "--category",
        choices=[
            "unit", "integration", "coverage", "lint", "type", 
            "format", "security", "performance", "all"
        ],
        default="all",
        help="Test category to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.category == "all":
        success = runner.run_all_tests()
    elif args.category == "unit":
        result = runner.run_unit_tests()
        success = result["success"]
    elif args.category == "integration":
        result = runner.run_integration_tests()
        success = result["success"]
    elif args.category == "coverage":
        result = runner.run_coverage_tests()
        success = result["success"]
    elif args.category == "lint":
        result = runner.run_linting()
        success = result["success"]
    elif args.category == "type":
        result = runner.run_type_checking()
        success = result["success"]
    elif args.category == "format":
        result = runner.run_formatting_check()
        success = result["success"]
    elif args.category == "security":
        result = runner.run_security_checks()
        success = result["success"]
    elif args.category == "performance":
        result = runner.run_performance_tests()
        success = result["success"]
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 