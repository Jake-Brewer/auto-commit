#!/usr/bin/env python3
"""
Security audit script for auto-commit project.
Performs comprehensive security checks and generates reports.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any
import re


class SecurityAuditor:
    """Comprehensive security auditing for the project."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.results = {}
    
    def run_bandit_scan(self) -> Dict[str, Any]:
        """Run Bandit security scanner."""
        print("🔍 Running Bandit security scan...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "bandit",
                "-r", str(self.src_dir),
                "-f", "json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                bandit_results = json.loads(result.stdout) if result.stdout else {}
                issues = bandit_results.get("results", [])
                
                return {
                    "status": "success",
                    "issues_found": len(issues),
                    "high_severity": len([i for i in issues if i.get("issue_severity") == "HIGH"]),
                    "medium_severity": len([i for i in issues if i.get("issue_severity") == "MEDIUM"]),
                    "low_severity": len([i for i in issues if i.get("issue_severity") == "LOW"]),
                    "details": issues
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def run_safety_check(self) -> Dict[str, Any]:
        """Check for known security vulnerabilities in dependencies."""
        print("🔍 Checking dependencies for known vulnerabilities...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "safety", "check", "--json"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "vulnerabilities_found": 0,
                    "details": []
                }
            else:
                # Safety returns non-zero when vulnerabilities are found
                try:
                    safety_results = json.loads(result.stdout) if result.stdout else []
                    return {
                        "status": "vulnerabilities_found",
                        "vulnerabilities_found": len(safety_results),
                        "details": safety_results
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "error": result.stderr or result.stdout
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def check_hardcoded_secrets(self) -> Dict[str, Any]:
        """Check for potentially hardcoded secrets."""
        print("🔍 Scanning for hardcoded secrets...")
        
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']{20,}["\']', "API key"),
            (r'secret\s*=\s*["\'][^"\']{16,}["\']', "Secret key"),
            (r'token\s*=\s*["\'][^"\']{20,}["\']', "Access token"),
            (r'["\'][A-Za-z0-9]{32,}["\']', "Long string (potential key)"),
            (r'-----BEGIN\s+[A-Z\s]+PRIVATE KEY-----', "Private key"),
        ]
        
        findings = []
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, description in secret_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Skip test files and comments
                            if not line.strip().startswith('#') and 'test' not in str(py_file).lower():
                                findings.append({
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "line": line_num,
                                    "description": description,
                                    "content": line.strip()[:100]
                                })
            except Exception as e:
                print(f"Warning: Could not scan {py_file}: {e}")
        
        return {
            "status": "success",
            "potential_secrets": len(findings),
            "details": findings
        }
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """Check for overly permissive file permissions."""
        print("🔍 Checking file permissions...")
        
        findings = []
        
        # Check Python files
        for py_file in self.src_dir.rglob("*.py"):
            try:
                stat = py_file.stat()
                mode = oct(stat.st_mode)[-3:]
                
                # Check if file is world-writable (dangerous)
                if mode.endswith('6') or mode.endswith('7'):
                    findings.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "permissions": mode,
                        "issue": "World-writable file"
                    })
            except Exception as e:
                print(f"Warning: Could not check permissions for {py_file}: {e}")
        
        # Check config files
        config_files = [
            self.project_root / "config.yml",
            self.project_root / ".env",
            self.project_root / "secrets.yml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    stat = config_file.stat()
                    mode = oct(stat.st_mode)[-3:]
                    
                    # Config files should not be world-readable
                    if mode[2] in ['4', '5', '6', '7']:
                        findings.append({
                            "file": str(config_file.relative_to(self.project_root)),
                            "permissions": mode,
                            "issue": "Config file is world-readable"
                        })
                except Exception as e:
                    print(f"Warning: Could not check permissions for {config_file}: {e}")
        
        return {
            "status": "success",
            "permission_issues": len(findings),
            "details": findings
        }
    
    def check_imports(self) -> Dict[str, Any]:
        """Check for potentially dangerous imports."""
        print("🔍 Checking for dangerous imports...")
        
        dangerous_imports = [
            ("eval", "Dynamic code execution"),
            ("exec", "Dynamic code execution"),
            ("subprocess.call", "Command execution without shell=False"),
            ("os.system", "Shell command execution"),
            ("pickle.loads", "Unsafe deserialization"),
            ("yaml.load", "Unsafe YAML loading (use safe_load)"),
            ("__import__", "Dynamic import"),
        ]
        
        findings = []
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for dangerous_func, description in dangerous_imports:
                        if dangerous_func in line and not line.strip().startswith('#'):
                            findings.append({
                                "file": str(py_file.relative_to(self.project_root)),
                                "line": line_num,
                                "function": dangerous_func,
                                "description": description,
                                "content": line.strip()
                            })
            except Exception as e:
                print(f"Warning: Could not scan {py_file}: {e}")
        
        return {
            "status": "success",
            "dangerous_imports": len(findings),
            "details": findings
        }
    
    def generate_security_report(self) -> None:
        """Generate comprehensive security report."""
        print(f"\n{'='*80}")
        print("SECURITY AUDIT REPORT")
        print(f"{'='*80}")
        
        # Summary
        total_issues = 0
        critical_issues = 0
        
        for check_name, result in self.results.items():
            if result.get("status") == "success":
                issues = (
                    result.get("issues_found", 0) +
                    result.get("vulnerabilities_found", 0) +
                    result.get("potential_secrets", 0) +
                    result.get("permission_issues", 0) +
                    result.get("dangerous_imports", 0)
                )
                total_issues += issues
                
                # Count critical issues
                if check_name == "bandit":
                    critical_issues += result.get("high_severity", 0)
                elif check_name == "safety":
                    critical_issues += result.get("vulnerabilities_found", 0)
                elif check_name == "secrets":
                    critical_issues += result.get("potential_secrets", 0)
        
        print(f"Total security issues found: {total_issues}")
        print(f"Critical issues: {critical_issues}")
        
        # Detailed results
        print(f"\n{'='*80}")
        print("DETAILED RESULTS")
        print(f"{'='*80}")
        
        for check_name, result in self.results.items():
            print(f"\n{check_name.upper()} SCAN:")
            
            if result.get("status") == "error":
                print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
                continue
            
            if check_name == "bandit":
                issues = result.get("issues_found", 0)
                if issues == 0:
                    print("  ✅ No security issues found")
                else:
                    print(f"  ⚠️  {issues} issues found:")
                    print(f"    - High severity: {result.get('high_severity', 0)}")
                    print(f"    - Medium severity: {result.get('medium_severity', 0)}")
                    print(f"    - Low severity: {result.get('low_severity', 0)}")
            
            elif check_name == "safety":
                vulns = result.get("vulnerabilities_found", 0)
                if vulns == 0:
                    print("  ✅ No known vulnerabilities in dependencies")
                else:
                    print(f"  ❌ {vulns} vulnerabilities found in dependencies")
            
            elif check_name == "secrets":
                secrets = result.get("potential_secrets", 0)
                if secrets == 0:
                    print("  ✅ No potential secrets found")
                else:
                    print(f"  ⚠️  {secrets} potential secrets found")
            
            elif check_name == "permissions":
                perms = result.get("permission_issues", 0)
                if perms == 0:
                    print("  ✅ No permission issues found")
                else:
                    print(f"  ⚠️  {perms} permission issues found")
            
            elif check_name == "imports":
                imports = result.get("dangerous_imports", 0)
                if imports == 0:
                    print("  ✅ No dangerous imports found")
                else:
                    print(f"  ⚠️  {imports} potentially dangerous imports found")
        
        # Recommendations
        print(f"\n{'='*80}")
        print("SECURITY RECOMMENDATIONS")
        print(f"{'='*80}")
        
        recommendations = [
            "🔒 Keep dependencies updated regularly",
            "🔑 Never commit secrets or API keys to version control",
            "🛡️  Use environment variables for sensitive configuration",
            "📝 Review code for security issues before committing",
            "🔍 Run security scans as part of CI/CD pipeline",
            "🚫 Avoid using eval(), exec(), and os.system()",
            "📋 Use yaml.safe_load() instead of yaml.load()",
            "🔐 Set appropriate file permissions on config files",
            "🎯 Follow principle of least privilege",
            "📊 Monitor security advisories for used packages"
        ]
        
        for rec in recommendations:
            print(f"  {rec}")
        
        print(f"\n{'='*80}")
        if critical_issues == 0 and total_issues == 0:
            print("🎉 SECURITY AUDIT PASSED - No critical issues found!")
        elif critical_issues == 0:
            print(f"⚠️  SECURITY AUDIT WARNING - {total_issues} non-critical issues found")
        else:
            print(f"❌ SECURITY AUDIT FAILED - {critical_issues} critical issues found")
        print(f"{'='*80}")
    
    def run_full_audit(self) -> bool:
        """Run complete security audit."""
        print("🔐 Starting comprehensive security audit...")
        
        # Run all security checks
        self.results["bandit"] = self.run_bandit_scan()
        self.results["safety"] = self.run_safety_check()
        self.results["secrets"] = self.check_hardcoded_secrets()
        self.results["permissions"] = self.check_file_permissions()
        self.results["imports"] = self.check_imports()
        
        # Generate report
        self.generate_security_report()
        
        # Return success if no critical issues
        critical_issues = 0
        for result in self.results.values():
            if result.get("status") == "vulnerabilities_found":
                critical_issues += result.get("vulnerabilities_found", 0)
            elif "high_severity" in result:
                critical_issues += result.get("high_severity", 0)
            elif "potential_secrets" in result:
                critical_issues += result.get("potential_secrets", 0)
        
        return critical_issues == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Security audit tool")
    parser.add_argument(
        "--check",
        choices=["bandit", "safety", "secrets", "permissions", "imports", "all"],
        default="all",
        help="Security check to run"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    auditor = SecurityAuditor()
    
    if args.check == "all":
        success = auditor.run_full_audit()
    else:
        # Run specific check
        if args.check == "bandit":
            result = auditor.run_bandit_scan()
        elif args.check == "safety":
            result = auditor.run_safety_check()
        elif args.check == "secrets":
            result = auditor.check_hardcoded_secrets()
        elif args.check == "permissions":
            result = auditor.check_file_permissions()
        elif args.check == "imports":
            result = auditor.check_imports()
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            auditor.results[args.check] = result
            auditor.generate_security_report()
        
        success = result.get("status") != "error"
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 