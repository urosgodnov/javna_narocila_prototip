#!/usr/bin/env python3
"""
Cleanup script for removing legacy form renderer code.
This script safely identifies and removes deprecated code from Form Renderer 1.x.

Usage:
    python scripts/cleanup_legacy_form_renderer.py --dry-run  # Check what would be removed
    python scripts/cleanup_legacy_form_renderer.py --execute  # Actually remove files
    python scripts/cleanup_legacy_form_renderer.py --check    # Check for remaining references
"""

import os
import re
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class LegacyCleanup:
    """Handles cleanup of legacy form renderer code."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.backup_dir = self.root_path / "backups" / f"legacy_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Files to be removed after 30-day period
        self.files_to_remove = [
            'ui/form_renderer.py',  # Main legacy file (keep for now with deprecation)
            'ui/form_renderer_old.py',
            'ui/form_renderer_backup.py',
            'ui/form_renderer_legacy.py',
            'utils/lot_context.py',
            'utils/legacy_validators.py',
            'utils/old_field_types.py',
            'tests/test_form_renderer_old.py',
            'tests/test_legacy_integration.py',
            'migrations/form_renderer_migration.py',
            'scripts/migrate_forms.py'
        ]
        
        # Patterns to search for and remove
        self.deprecated_patterns = [
            (r'lot_context\s*=', 'lot_context assignment'),
            (r'has_lots\s*:', 'has_lots conditional'),
            (r'mode\s*==\s*["\']general["\']', 'general mode check'),
            (r'mode\s*==\s*["\']lots["\']', 'lots mode check'),
            (r'_render_form_legacy', 'legacy render function'),
            (r'backward_compatibility', 'backward compatibility code'),
            (r'USE_NEW_FORM_RENDERER', 'feature flag'),
            (r'from ui\.form_renderer import(?! )', 'old form_renderer import'),
            (r'from utils\.lot_context import', 'lot_context import'),
            (r'get_current_lot_context', 'lot context function'),
            (r'get_lot_scoped_key', 'lot scoped key function')
        ]
        
        # Imports to clean
        self.deprecated_imports = [
            'from ui.form_renderer_old import',
            'from ui.form_renderer_backup import',
            'from ui.form_renderer_legacy import',
            'from utils.lot_context import',
            'from utils.legacy_validators import',
            'import form_renderer_legacy',
            'import lot_context'
        ]
        
        self.report = {
            'files_checked': 0,
            'files_with_issues': [],
            'patterns_found': {},
            'imports_found': [],
            'files_to_remove': [],
            'safe_to_proceed': True
        }
    
    def check_references(self, verbose: bool = True) -> Dict:
        """Check for remaining references to deprecated code."""
        print(f"{Colors.HEADER}Checking for deprecated patterns...{Colors.ENDC}")
        
        # Get Python files, excluding virtual environments and cache directories
        py_files = []
        for py_file in self.root_path.rglob('*.py'):
            # Skip virtual environments and cache directories
            if any(skip in str(py_file) for skip in [
                '.venv/', 'venv/', '__pycache__/', '.git/', 
                'node_modules/', 'dist/', 'build/', '.pytest_cache/'
            ]):
                continue
            py_files.append(py_file)
        
        self.report['files_checked'] = len(py_files)
        print(f"Checking {len(py_files)} Python files...")
        
        for py_file in py_files:
            # Skip this cleanup script
            if 'cleanup_legacy' in str(py_file):
                continue
            
            # Skip test files that are testing the new system
            if 'test_unified' in str(py_file) or 'test_form_controller' in str(py_file):
                continue
                
            # Skip documentation
            if '/docs/' in str(py_file):
                continue
            
            # Skip new implementation files
            if any(new_file in str(py_file) for new_file in [
                'form_controller.py', 'field_renderer.py', 'section_renderer.py',
                'lot_manager.py', 'form_context.py', 'form_renderer_compat.py'
            ]):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
            except Exception as e:
                if verbose:
                    print(f"{Colors.WARNING}Warning: Could not read {py_file}: {e}{Colors.ENDC}")
                continue
            
            file_issues = []
            
            # Check for deprecated patterns
            for pattern, description in self.deprecated_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    file_issues.append({
                        'type': 'pattern',
                        'description': description,
                        'line': line_num,
                        'text': match.group(0)
                    })
                    
                    if description not in self.report['patterns_found']:
                        self.report['patterns_found'][description] = []
                    self.report['patterns_found'][description].append({
                        'file': str(py_file),
                        'line': line_num
                    })
            
            # Check for deprecated imports
            for import_pattern in self.deprecated_imports:
                if import_pattern in content:
                    line_num = content.index(import_pattern)
                    line_num = content[:line_num].count('\n') + 1
                    file_issues.append({
                        'type': 'import',
                        'description': import_pattern,
                        'line': line_num
                    })
                    self.report['imports_found'].append({
                        'file': str(py_file),
                        'import': import_pattern,
                        'line': line_num
                    })
            
            if file_issues:
                self.report['files_with_issues'].append({
                    'file': str(py_file),
                    'issues': file_issues
                })
                
                if verbose:
                    print(f"\n{Colors.WARNING}Issues in {py_file}:{Colors.ENDC}")
                    for issue in file_issues:
                        print(f"  Line {issue['line']}: {issue['description']}")
        
        # Check for files that should be removed
        for file_path in self.files_to_remove:
            full_path = self.root_path / file_path
            if full_path.exists():
                self.report['files_to_remove'].append(str(full_path))
                if verbose:
                    print(f"{Colors.WARNING}File marked for removal: {file_path}{Colors.ENDC}")
        
        # Determine if safe to proceed
        critical_files = [f for f in self.report['files_with_issues'] 
                         if not any(skip in f['file'] for skip in ['test', 'backup', 'old', 'legacy'])]
        
        if critical_files:
            self.report['safe_to_proceed'] = False
            print(f"\n{Colors.FAIL}WARNING: Found {len(critical_files)} production files with deprecated patterns!{Colors.ENDC}")
        else:
            print(f"\n{Colors.OKGREEN}No critical issues found. Safe to proceed with cleanup.{Colors.ENDC}")
        
        return self.report
    
    def create_backup(self, files: List[str]) -> bool:
        """Create backup of files before removal."""
        print(f"\n{Colors.OKBLUE}Creating backup at {self.backup_dir}...{Colors.ENDC}")
        
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path in files:
                source = Path(file_path)
                if source.exists():
                    dest = self.backup_dir / source.name
                    shutil.copy2(source, dest)
                    print(f"  Backed up: {source.name}")
            
            # Save cleanup report
            report_file = self.backup_dir / "cleanup_report.txt"
            with open(report_file, 'w') as f:
                f.write(f"Cleanup Report - {datetime.now()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Files checked: {self.report['files_checked']}\n")
                f.write(f"Files with issues: {len(self.report['files_with_issues'])}\n")
                f.write(f"Files to remove: {len(self.report['files_to_remove'])}\n\n")
                
                if self.report['patterns_found']:
                    f.write("Deprecated patterns found:\n")
                    for pattern, locations in self.report['patterns_found'].items():
                        f.write(f"  {pattern}: {len(locations)} occurrences\n")
            
            print(f"{Colors.OKGREEN}Backup created successfully{Colors.ENDC}")
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}Failed to create backup: {e}{Colors.ENDC}")
            return False
    
    def remove_files(self, dry_run: bool = True) -> bool:
        """Remove deprecated files."""
        files_to_remove = []
        
        for file_path in self.files_to_remove:
            full_path = self.root_path / file_path
            if full_path.exists():
                files_to_remove.append(full_path)
        
        if not files_to_remove:
            print(f"{Colors.OKGREEN}No files to remove{Colors.ENDC}")
            return True
        
        print(f"\n{Colors.HEADER}Files to remove:{Colors.ENDC}")
        for file_path in files_to_remove:
            print(f"  - {file_path}")
        
        if dry_run:
            print(f"\n{Colors.WARNING}DRY RUN: No files were actually removed{Colors.ENDC}")
            return True
        
        # Create backup first
        if not self.create_backup([str(f) for f in files_to_remove]):
            print(f"{Colors.FAIL}Aborting: Failed to create backup{Colors.ENDC}")
            return False
        
        # Remove files
        print(f"\n{Colors.WARNING}Removing files...{Colors.ENDC}")
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"  {Colors.OKGREEN}Removed: {file_path}{Colors.ENDC}")
            except Exception as e:
                print(f"  {Colors.FAIL}Failed to remove {file_path}: {e}{Colors.ENDC}")
                return False
        
        return True
    
    def clean_imports(self, dry_run: bool = True) -> int:
        """Remove deprecated imports from all Python files."""
        print(f"\n{Colors.HEADER}Cleaning deprecated imports...{Colors.ENDC}")
        
        files_modified = 0
        
        for py_file in self.root_path.rglob('*.py'):
            # Skip cleanup script and new implementation
            if 'cleanup_legacy' in str(py_file):
                continue
            if any(new_file in str(py_file) for new_file in [
                'form_controller.py', 'field_renderer.py', 'section_renderer.py',
                'lot_manager.py', 'form_context.py'
            ]):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                original = content
                
                # Remove deprecated imports
                for import_pattern in self.deprecated_imports:
                    pattern = f'^.*{re.escape(import_pattern)}.*$'
                    content = re.sub(pattern, '', content, flags=re.MULTILINE)
                
                # Clean up multiple blank lines
                content = re.sub(r'\n\n\n+', '\n\n', content)
                
                if content != original:
                    if dry_run:
                        print(f"  Would clean imports in: {py_file}")
                    else:
                        py_file.write_text(content, encoding='utf-8')
                        print(f"  {Colors.OKGREEN}Cleaned imports in: {py_file}{Colors.ENDC}")
                    files_modified += 1
                    
            except Exception as e:
                print(f"  {Colors.WARNING}Could not process {py_file}: {e}{Colors.ENDC}")
        
        return files_modified
    
    def generate_summary(self) -> str:
        """Generate a summary of the cleanup operation."""
        summary = []
        summary.append(f"\n{Colors.HEADER}{'='*60}")
        summary.append("CLEANUP SUMMARY")
        summary.append(f"{'='*60}{Colors.ENDC}\n")
        
        summary.append(f"Files checked: {self.report['files_checked']}")
        summary.append(f"Files with issues: {len(self.report['files_with_issues'])}")
        summary.append(f"Files to remove: {len(self.report['files_to_remove'])}")
        
        if self.report['patterns_found']:
            summary.append(f"\n{Colors.WARNING}Deprecated patterns found:{Colors.ENDC}")
            for pattern, locations in self.report['patterns_found'].items():
                summary.append(f"  • {pattern}: {len(locations)} occurrences")
        
        if self.report['safe_to_proceed']:
            summary.append(f"\n{Colors.OKGREEN}✓ Safe to proceed with cleanup{Colors.ENDC}")
        else:
            summary.append(f"\n{Colors.FAIL}✗ Not safe to proceed - resolve issues first{Colors.ENDC}")
        
        summary.append(f"\n{Colors.OKCYAN}Backup location: {self.backup_dir}{Colors.ENDC}")
        
        return '\n'.join(summary)


def main():
    parser = argparse.ArgumentParser(description='Clean up legacy form renderer code')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without making changes')
    parser.add_argument('--execute', action='store_true',
                       help='Actually perform the cleanup')
    parser.add_argument('--check', action='store_true',
                       help='Only check for deprecated patterns')
    parser.add_argument('--force', action='store_true',
                       help='Force cleanup even if issues are found')
    parser.add_argument('--path', default='.',
                       help='Root path of the project (default: current directory)')
    
    args = parser.parse_args()
    
    if not (args.dry_run or args.execute or args.check):
        print(f"{Colors.FAIL}Error: Must specify --dry-run, --execute, or --check{Colors.ENDC}")
        parser.print_help()
        sys.exit(1)
    
    cleanup = LegacyCleanup(args.path)
    
    # Always check first
    print(f"{Colors.BOLD}Legacy Form Renderer Cleanup Tool{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Project root: {Path(args.path).absolute()}{Colors.ENDC}\n")
    
    report = cleanup.check_references(verbose=True)
    
    if args.check:
        print(cleanup.generate_summary())
        sys.exit(0 if report['safe_to_proceed'] else 1)
    
    # Check if safe to proceed
    if not report['safe_to_proceed'] and not args.force:
        print(f"\n{Colors.FAIL}Cannot proceed with cleanup - deprecated patterns found in production code{Colors.ENDC}")
        print(f"Use --force to override (not recommended)")
        sys.exit(1)
    
    if args.execute:
        print(f"\n{Colors.WARNING}{'='*60}")
        print("EXECUTING CLEANUP - THIS WILL MODIFY FILES")
        print(f"{'='*60}{Colors.ENDC}\n")
        
        response = input(f"{Colors.BOLD}Are you sure you want to proceed? (yes/no): {Colors.ENDC}")
        if response.lower() != 'yes':
            print(f"{Colors.WARNING}Cleanup cancelled{Colors.ENDC}")
            sys.exit(0)
        
        # Perform cleanup
        if cleanup.remove_files(dry_run=False):
            files_cleaned = cleanup.clean_imports(dry_run=False)
            print(f"\n{Colors.OKGREEN}Cleanup completed successfully!{Colors.ENDC}")
            print(f"Files removed: {len(report['files_to_remove'])}")
            print(f"Imports cleaned: {files_cleaned}")
        else:
            print(f"\n{Colors.FAIL}Cleanup failed - check errors above{Colors.ENDC}")
            sys.exit(1)
    
    elif args.dry_run:
        print(f"\n{Colors.WARNING}DRY RUN MODE - No changes will be made{Colors.ENDC}\n")
        cleanup.remove_files(dry_run=True)
        files_that_would_be_cleaned = cleanup.clean_imports(dry_run=True)
        print(f"\n{Colors.OKCYAN}Would clean imports in {files_that_would_be_cleaned} files{Colors.ENDC}")
    
    print(cleanup.generate_summary())


if __name__ == '__main__':
    main()