#!/usr/bin/env python3
"""
Maintenance script for auto-commit project.
Performs code cleanup, optimization, and maintenance tasks.
"""

import argparse
import ast
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Set
import re


class CodeMaintainer:
    """Comprehensive code maintenance and cleanup."""
    
    def __init__(self) -> None:
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
        self.results: Dict[str, Any] = {}
    
    def find_unused_imports(self) -> Dict[str, Any]:
        """Find unused imports in Python files."""
        print("🔍 Finding unused imports...")
        
        unused_imports = []
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST
                tree = ast.parse(content)
                
                # Find all imports
                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])
                        for alias in node.names:
                            imports.add(alias.name)
                
                # Find used names
                used_names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        used_names.add(node.id)
                    elif isinstance(node, ast.Attribute):
                        if isinstance(node.value, ast.Name):
                            used_names.add(node.value.id)
                
                # Find unused imports
                for imp in imports:
                    if imp not in used_names and imp != "__future__":
                        unused_imports.append({
                            "file": str(py_file.relative_to(self.project_root)),
                            "import": imp
                        })
            
            except Exception as e:
                print(f"Warning: Could not analyze {py_file}: {e}")
        
        return {
            "unused_imports": len(unused_imports),
            "details": unused_imports
        }
    
    def clean_cache_files(self) -> Dict[str, Any]:
        """Clean up cache and temporary files."""
        print("🧹 Cleaning cache files...")
        
        cache_patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/.pytest_cache",
            "**/.mypy_cache",
            "**/htmlcov",
            "**/*.egg-info",
            "**/build",
            "**/dist"
        ]
        
        cleaned_files = []
        
        for pattern in cache_patterns:
            for path in self.project_root.glob(pattern):
                try:
                    if path.is_file():
                        path.unlink()
                        cleaned_files.append(str(path.relative_to(self.project_root)))
                    elif path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                        cleaned_files.append(str(path.relative_to(self.project_root)))
                except Exception as e:
                    print(f"Warning: Could not clean {path}: {e}")
        
        return {
            "cleaned_files": len(cleaned_files),
            "details": cleaned_files
        }
    
    def generate_maintenance_report(self) -> None:
        """Generate comprehensive maintenance report."""
        print(f"\n{'='*80}")
        print("CODE MAINTENANCE REPORT")
        print(f"{'='*80}")
        
        # Summary
        total_issues = 0
        for result in self.results.values():
            if isinstance(result, dict):
                total_issues += sum(v for k, v in result.items() 
                                  if isinstance(v, int) and k.endswith(('_imports', '_files')))
        
        print(f"Total maintenance items found: {total_issues}")
        
        # Detailed results
        print(f"\n{'='*80}")
        print("DETAILED RESULTS")
        print(f"{'='*80}")
        
        for check_name, result in self.results.items():
            print(f"\n{check_name.upper().replace('_', ' ')}:")
            
            if isinstance(result, dict) and "error" in result:
                print(f"  ⚠️  Error: {result['error']}")
                continue
            
            if check_name == "unused_imports":
                count = result.get("unused_imports", 0)
                if count == 0:
                    print("  ✅ No unused imports found")
                else:
                    print(f"  📋 {count} unused imports found")
            
            elif check_name == "cache_cleanup":
                count = result.get("cleaned_files", 0)
                print(f"  🧹 Cleaned {count} cache files")
        
        print(f"\n{'='*80}")
        if total_issues == 0:
            print("🎉 CODE MAINTENANCE EXCELLENT - No issues found!")
        else:
            print(f"✅ CODE MAINTENANCE COMPLETED - {total_issues} items processed")
        print(f"{'='*80}")
    
    def run_full_maintenance(self) -> bool:
        """Run complete maintenance check."""
        print("🔧 Starting comprehensive maintenance check...")
        
        # Run all maintenance checks
        self.results["unused_imports"] = self.find_unused_imports()
        self.results["cache_cleanup"] = self.clean_cache_files()
        
        # Generate report
        self.generate_maintenance_report()
        
        return True


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Code maintenance tool")
    parser.add_argument(
        "--check",
        choices=["imports", "clean", "all"],
        default="all",
        help="Maintenance check to run"
    )
    
    args = parser.parse_args()
    
    maintainer = CodeMaintainer()
    
    if args.check == "all":
        success = maintainer.run_full_maintenance()
    else:
        # Run specific check
        if args.check == "imports":
            result = maintainer.find_unused_imports()
        elif args.check == "clean":
            result = maintainer.clean_cache_files()
        
        maintainer.results[args.check] = result
        maintainer.generate_maintenance_report()
        success = True
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
