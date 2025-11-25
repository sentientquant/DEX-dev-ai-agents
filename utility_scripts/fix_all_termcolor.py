#!/usr/bin/env python3
"""Fix ALL termcolor imports in the entire project"""

import os
import re
import glob

TERMCOLOR_PATTERN = r'^from termcolor import (.+)$'
REPLACEMENT = '''# Make termcolor optional
try:
    from termcolor import \\1
except ImportError:
    def cprint(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        print(text)
    def colored(text, color=None, attrs=None):
        """Fallback if termcolor not available"""
        return text'''

def find_all_python_files():
    """Find all Python files in the project"""
    files = []
    for root, dirs, filenames in os.walk('.'):
        # Skip venv, .git, __pycache__
        dirs[:] = [d for d in dirs if d not in ['.git', 'venv', '__pycache__', 'node_modules']]
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(root, filename)
                files.append(filepath.replace('\\', '/'))
    return files

def has_termcolor_import(filepath):
    """Check if file has termcolor import"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return re.search(r'^from termcolor import', content, re.MULTILINE) is not None
    except:
        return False

def fix_file(filepath):
    """Fix termcolor import in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already fixed
        if 'try:\n    from termcolor import' in content:
            return 'already_fixed'

        # Replace the import
        new_content = re.sub(
            TERMCOLOR_PATTERN,
            REPLACEMENT,
            content,
            count=1,
            flags=re.MULTILINE
        )

        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return 'fixed'
        else:
            return 'no_import'
    except Exception as e:
        return f'error: {e}'

if __name__ == "__main__":
    print("="*80)
    print(" FIXING ALL TERMCOLOR IMPORTS IN PROJECT")
    print("="*80)

    # Find all Python files
    all_files = find_all_python_files()
    print(f"Found {len(all_files)} Python files")

    # Filter to only files with termcolor imports
    files_with_termcolor = [f for f in all_files if has_termcolor_import(f)]
    print(f"Files with termcolor imports: {len(files_with_termcolor)}")

    # Fix each file
    fixed = 0
    already_fixed = 0
    errors = 0

    for filepath in files_with_termcolor:
        result = fix_file(filepath)
        if result == 'fixed':
            print(f"[FIXED] {filepath}")
            fixed += 1
        elif result == 'already_fixed':
            already_fixed += 1
        elif result.startswith('error'):
            print(f"[ERROR] {filepath}: {result}")
            errors += 1

    print("\n" + "="*80)
    print(f" COMPLETE")
    print(f"   Fixed: {fixed}")
    print(f"   Already fixed: {already_fixed}")
    print(f"   Errors: {errors}")
    print(f"   Total: {len(files_with_termcolor)}")
    print("="*80)
