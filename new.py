#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File Reader for Django Project (Backend + Frontend)
====================================================
This script reads all files from a Django project directory and its 
frontend subdirectories, then compiles them into a single organized 
text file with clear section headers and file paths.

Usage:
    python read_project_files.py

Configuration:
    Set PROJECT_ROOT to your Django project's root directory.
    Set OUTPUT_FILE to the desired output file name.
    Set EXCLUDED_DIRS to folders you want to skip.

Author: FaceTrack Team
Date: 2026-07-24
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
import fnmatch


# ============================================================
# CONFIGURATION - Modify these variables as needed
# ============================================================

# Set this to your Django project's root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Output file name
OUTPUT_FILE = "django_project_full_dump.txt"

# Directories to exclude from scanning
EXCLUDED_DIRS = [
    '.git',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    'venv',
    'env',
    'virtualenv',
    'node_modules',
    '.idea',
    '.vscode',
    '.DS_Store',
    'dist',
    'build',
    '*.egg-info',
    'logs',
    'media',
    'staticfiles',
    'static',
    'media_root',
    'geoface_attendance/__pycache__',
    'accounts/__pycache__',
    'attendance/__pycache__',
]

# File extensions to include (None for all)
# Example: INCLUDE_EXTENSIONS = ['.py', '.html', '.css', '.js', '.json', '.txt', '.md']
INCLUDE_EXTENSIONS = None  # Include all files

# File extensions to explicitly exclude
EXCLUDE_EXTENSIONS = [
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
    '.exe', '.msi', '.bin', '.dat', '.db', '.sqlite3',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
    '.mp3', '.mp4', '.avi', '.mov', '.mkv',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.log', '.lock', '.pid',
]

# Maximum file size to read (in bytes) - skip very large files
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Headers to show for each file section
SECTION_HEADER_TEMPLATE = """
============================================================
📁 FILE: {file_path}
📏 Size: {size_kb} KB
🕐 Last Modified: {modified_time}
============================================================
"""

# ============================================================
# END OF CONFIGURATION
# ============================================================


def get_file_info(file_path):
    """Get file size and last modified time."""
    try:
        stat = os.stat(file_path)
        size_kb = stat.st_size // 1024 if stat.st_size > 1024 else 1
        modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        return size_kb, modified
    except (OSError, FileNotFoundError):
        return 0, "Unknown"


def should_include_file(file_path, root_dir):
    """
    Determine if a file should be included in the dump.
    
    Args:
        file_path: Full path to the file
        root_dir: Project root directory
    
    Returns:
        bool: True if file should be included, False otherwise
    """
    file_name = os.path.basename(file_path)
    rel_path = os.path.relpath(file_path, root_dir)
    
    # Skip hidden files (except .gitignore, .env, etc.)
    if file_name.startswith('.') and file_name not in ['.env', '.gitignore', '.env.example']:
        return False
    
    # Check excluded directories
    for excluded in EXCLUDED_DIRS:
        if rel_path.startswith(excluded) or f'/{excluded}/' in rel_path or f'\\{excluded}\\' in rel_path:
            return False
    
    # Check file extension
    _, ext = os.path.splitext(file_name)
    ext = ext.lower()
    
    if EXCLUDE_EXTENSIONS and ext in EXCLUDE_EXTENSIONS:
        return False
    
    if INCLUDE_EXTENSIONS is not None and ext not in INCLUDE_EXTENSIONS:
        return False
    
    # Check file size
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            return False
    except (OSError, FileNotFoundError):
        return False
    
    return True


def scan_project(root_dir):
    """
    Scan the project directory and return a list of file paths.
    
    Args:
        root_dir: Project root directory
    
    Returns:
        list: Sorted list of file paths
    """
    all_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove excluded directories from the walk
        for excluded in EXCLUDED_DIRS:
            if excluded in dirnames:
                dirnames.remove(excluded)
        
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if should_include_file(file_path, root_dir):
                all_files.append(file_path)
    
    return sorted(all_files)


def read_file_content(file_path):
    """
    Read file content with proper encoding detection.
    
    Args:
        file_path: Path to the file
    
    Returns:
        tuple: (content, error_message)
    """
    encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                return content, None
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return None, str(e)
    
    # If no encoding works, try reading as binary and decode with 'replace'
    try:
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='replace')
            return content, "Used fallback encoding (replace mode)"
    except Exception as e:
        return None, str(e)


def generate_project_tree(root_dir, all_files):
    """
    Generate a directory tree structure of the project.
    
    Args:
        root_dir: Project root directory
        all_files: List of all file paths
    
    Returns:
        str: Directory tree representation
    """
    tree_lines = []
    tree_lines.append("📂 Project Structure")
    tree_lines.append("=" * 60)
    
    # Create a tree structure
    tree = {}
    base_path = os.path.abspath(root_dir)
    
    for file_path in all_files:
        rel_path = os.path.relpath(file_path, base_path)
        parts = rel_path.split(os.sep)
        
        current = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                # File
                current[part] = None
            else:
                # Directory
                if part not in current:
                    current[part] = {}
                current = current[part]
    
    def render_tree(node, prefix="", is_last=True):
        lines = []
        items = list(node.items())
        
        for i, (name, child) in enumerate(items):
            is_item_last = (i == len(items) - 1)
            connector = "└── " if is_item_last else "├── "
            lines.append(f"{prefix}{connector}{name}")
            
            if child is not None:  # Directory
                extension = "    " if is_item_last else "│   "
                lines.extend(render_tree(child, prefix + extension, is_item_last))
        
        return lines
    
    tree_lines.extend(render_tree(tree))
    return "\n".join(tree_lines)


def write_project_dump(root_dir, output_file):
    """
    Write the entire project dump to the output file.
    
    Args:
        root_dir: Project root directory
        output_file: Output file path
    """
    print(f"🔍 Scanning project: {root_dir}")
    
    if not os.path.exists(root_dir):
        print(f"❌ Error: Directory '{root_dir}' does not exist.")
        return False
    
    all_files = scan_project(root_dir)
    
    if not all_files:
        print("❌ No files found to include.")
        return False
    
    print(f"📊 Found {len(all_files)} files to include.")
    
    project_name = os.path.basename(root_dir)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"📝 Writing to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as out:
        # Write header
        out.write("=" * 80 + "\n")
        out.write(f"DJANGO PROJECT FULL DUMP - {project_name}\n")
        out.write("=" * 80 + "\n\n")
        out.write(f"📅 Generated: {current_time}\n")
        out.write(f"📂 Project Root: {root_dir}\n")
        out.write(f"📄 Total Files: {len(all_files)}\n\n")
        
        # Write project structure tree
        out.write(generate_project_tree(root_dir, all_files))
        out.write("\n\n" + "=" * 80 + "\n\n")
        
        # Write file details
        out.write("=" * 80 + "\n")
        out.write("📂 FILE CONTENTS\n")
        out.write("=" * 80 + "\n\n")
        
        for i, file_path in enumerate(all_files, 1):
            rel_path = os.path.relpath(file_path, root_dir)
            size_kb, modified = get_file_info(file_path)
            
            # Write section header
            out.write(f"\n\n")
            out.write("=" * 80 + "\n")
            out.write(f"[{i}/{len(all_files)}] 📁 {rel_path}\n")
            out.write(f"📏 Size: {size_kb} KB | 🕐 Modified: {modified}\n")
            out.write("-" * 80 + "\n")
            
            # Read and write content
            content, error = read_file_content(file_path)
            
            if error and not content:
                out.write(f"⚠️ ERROR: Could not read file - {error}\n")
            elif error:
                out.write(f"ℹ️ NOTE: {error}\n")
                out.write("=" * 60 + "\n")
                out.write(content)
                out.write("\n")
            else:
                # Determine if content should be treated as binary
                if content and any(ord(c) < 32 for c in content[:1000]) and not content.strip():
                    out.write("⚠️ Binary file - content not shown\n")
                else:
                    out.write(content)
                    if not content.endswith('\n'):
                        out.write('\n')
        
        out.write("\n\n" + "=" * 80 + "\n")
        out.write(f"📊 DUMP COMPLETE - {len(all_files)} files processed\n")
        out.write("=" * 80 + "\n")
    
    print(f"✅ Success! Dump saved to: {output_file}")
    print(f"📊 Total files processed: {len(all_files)}")
    print(f"📁 Output size: {os.path.getsize(output_file) // 1024} KB")
    return True


def main():
    """Main execution function."""
    print("\n" + "=" * 60)
    print("🚀 Django Project File Reader")
    print("=" * 60 + "\n")
    
    # Use the current directory as root if PROJECT_ROOT is not set
    root_dir = PROJECT_ROOT
    
    if not root_dir or root_dir == ".":
        root_dir = os.getcwd()
    
    # Check if manage.py exists (Django project indicator)
    manage_py = os.path.join(root_dir, 'manage.py')
    if not os.path.exists(manage_py):
        print(f"⚠️ Warning: '{manage_py}' not found.")
        print("   Make sure PROJECT_ROOT points to your Django project root.\n")
        proceed = input("Continue anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            print("❌ Aborted.")
            return
    
    output_file = OUTPUT_FILE
    
    # Ask user if they want to change output file
    print(f"📁 Output file: {output_file}")
    change = input("Change output file name? (y/n): ").strip().lower()
    if change == 'y':
        output_file = input("Enter output file name: ").strip()
        if not output_file:
            output_file = OUTPUT_FILE
    
    print("\n" + "-" * 60)
    success = write_project_dump(root_dir, output_file)
    
    if success:
        print("\n" + "-" * 60)
        print("✅ Complete! You can now share or review the dump file.")
        print(f"📄 File: {output_file}")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)