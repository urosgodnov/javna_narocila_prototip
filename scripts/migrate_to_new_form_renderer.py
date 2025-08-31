#!/usr/bin/env python3
"""
Migration script to update all files to use the new form renderer architecture.
Run this to complete Story 40.9: Direct System Replacement.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def find_files_to_migrate(root_dir: str) -> List[Path]:
    """Find all Python files that import from old form_renderer."""
    files_to_migrate = []
    root_path = Path(root_dir)
    
    # Patterns to search for
    patterns = [
        r'from ui\.form_renderer import',
        r'from form_renderer import',
    ]
    
    # Skip these directories
    skip_dirs = {'__pycache__', '.git', '.venv', 'venv', 'archive'}
    
    for py_file in root_path.rglob('*.py'):
        # Skip files in excluded directories
        if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
            continue
            
        # Skip the old form_renderer.py itself and migration script
        if py_file.name == 'form_renderer.py' and 'archive' not in str(py_file):
            continue
        if py_file.name == 'migrate_to_new_form_renderer.py':
            continue
            
        # Check if file contains old imports
        try:
            content = py_file.read_text(encoding='utf-8')
            for pattern in patterns:
                if re.search(pattern, content):
                    files_to_migrate.append(py_file)
                    break
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return files_to_migrate


def migrate_file(file_path: Path, dry_run: bool = True) -> Tuple[bool, str]:
    """
    Migrate a single file to use new form renderer.
    
    Args:
        file_path: Path to file to migrate
        dry_run: If True, don't actually modify the file
        
    Returns:
        Tuple of (success, message)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Replace imports
        replacements = [
            (r'from ui\.form_renderer import render_form',
             'from ui.form_renderer_compat import render_form'),
            (r'from form_renderer import render_form',
             'from ui.form_renderer_compat import render_form'),
            (r'import ui\.form_renderer',
             'import ui.form_renderer_compat as form_renderer'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Check if any changes were made
        if content != original_content:
            if not dry_run:
                # Create backup
                backup_path = file_path.with_suffix('.py.bak')
                file_path.rename(backup_path)
                
                # Write updated content
                file_path.write_text(content, encoding='utf-8')
                
                return True, f"Migrated (backup: {backup_path.name})"
            else:
                return True, "Would migrate (dry run)"
        else:
            return False, "No changes needed"
            
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Main migration function."""
    print("=" * 60)
    print("Form Renderer Migration Script")
    print("Story 40.9: Direct System Replacement")
    print("=" * 60)
    
    # Get current directory
    current_dir = Path(__file__).parent
    
    # Find files to migrate
    print("\nSearching for files to migrate...")
    files = find_files_to_migrate(current_dir)
    
    if not files:
        print("No files found that need migration.")
        return
    
    print(f"\nFound {len(files)} files to migrate:")
    for f in files:
        print(f"  - {f.relative_to(current_dir)}")
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    response = input("Do you want to proceed with migration? (y/n/dry): ").lower()
    
    if response == 'n':
        print("Migration cancelled.")
        return
    
    dry_run = response == 'dry'
    if dry_run:
        print("\nDRY RUN MODE - No files will be modified")
    
    print("\nMigrating files...")
    print("-" * 60)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for file_path in files:
        rel_path = file_path.relative_to(current_dir)
        success, message = migrate_file(file_path, dry_run)
        
        if success:
            print(f"[OK] {rel_path}: {message}")
            success_count += 1
        elif "No changes" in message:
            print(f"[-] {rel_path}: {message}")
            skip_count += 1
        else:
            print(f"[ERROR] {rel_path}: {message}")
            error_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary:")
    print(f"  Successfully migrated: {success_count}")
    print(f"  Skipped (no changes): {skip_count}")
    print(f"  Errors: {error_count}")
    
    if not dry_run and success_count > 0:
        print("\n[SUCCESS] Migration complete!")
        print("Note: Backup files (.py.bak) were created for all modified files.")
        print("\nNext steps:")
        print("1. Run tests to ensure everything works")
        print("2. Delete backup files once confirmed")
        print("3. Remove old ui/form_renderer.py")
    elif dry_run:
        print("\nThis was a dry run. Run without 'dry' option to apply changes.")


if __name__ == "__main__":
    main()