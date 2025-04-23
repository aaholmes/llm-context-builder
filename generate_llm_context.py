#!/usr/bin/env python3
import os
import argparse
import fnmatch
import sys
from pathlib import Path

# --- Configuration ---
IGNORE_FILE_NAME = ".llmignore"
DEFAULT_OUTPUT_FILE = "llm_context.txt"
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024 # Max file size to include (e.g., 1MB) - adjust as needed

# --- Helper Functions ---

def load_ignore_patterns(root_dir):
    """Loads ignore patterns from .llmignore file in the root directory."""
    ignore_file_path = os.path.join(root_dir, IGNORE_FILE_NAME)
    patterns = []
    if os.path.exists(ignore_file_path):
        try:
            with open(ignore_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith('#'):
                        patterns.append(stripped_line)
            print(f"INFO: Loaded {len(patterns)} patterns from {ignore_file_path}")
        except Exception as e:
            print(f"WARNING: Could not read {ignore_file_path}: {e}", file=sys.stderr)
    else:
        print(f"INFO: {IGNORE_FILE_NAME} not found in {root_dir}. Including all found files (respecting defaults like .git).")
    # Standard ignores (can be customized)
    patterns.extend(['.git/*', '.svn/*', '__pycache__/*', '*.pyc', '*.pyo', '*.o', '*.so', '*.dll', '*.exe'])
    return patterns

def should_ignore(relative_path, ignore_patterns):
    """Checks if a relative path matches any ignore pattern."""
    # Normalize path separators for matching
    normalized_path = relative_path.replace(os.sep, '/')
    for pattern in ignore_patterns:
        if pattern.endswith('/'): # Match directory and contents
             # Check if path starts with the directory pattern or is the directory itself
             if normalized_path == pattern.rstrip('/') or normalized_path.startswith(pattern):
                return True
        elif fnmatch.fnmatch(normalized_path, pattern): # Match file or specific directory pattern
            return True
        elif fnmatch.fnmatch(os.path.basename(normalized_path), pattern): # Match filename part only
             return True
    return False

def generate_tree_string(root_dir, included_files):
    """Generates a string representation of the directory tree."""
    tree = {}
    for rel_path in included_files:
        parts = Path(rel_path).parts
        current_level = tree
        for i, part in enumerate(parts):
            if i == len(parts) - 1: # It's a file
                current_level.setdefault('__files__', []).append(part)
            else: # It's a directory
                current_level = current_level.setdefault(part, {})

    tree_lines = []

    def build_tree_lines(level, prefix=""):
        entries = sorted(level.keys())
        files = sorted(level.get('__files__', []))
        all_items = entries + files # Directories first, then files

        for i, item in enumerate(all_items):
            connector = "└── " if i == len(all_items) - 1 else "├── "
            tree_lines.append(f"{prefix}{connector}{item}")

            if item in level and item != '__files__': # It's a directory
                new_prefix = prefix + ("    " if i == len(all_items) - 1 else "│   ")
                build_tree_lines(level[item], new_prefix)

    # Add the root directory name
    tree_lines.append(f"{os.path.basename(os.path.abspath(root_dir))}/")
    build_tree_lines(tree) # Start building from the root structure

    return "\n".join(tree_lines)


def get_language_hint(filename):
    """Provides a markdown language hint based on file extension."""
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    # Add more mappings as needed
    mapping = {
        '.py': 'python', '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript',
        '.tsx': 'typescript', '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.cs': 'csharp',
        '.go': 'go', '.rs': 'rust', '.php': 'php', '.rb': 'ruby', '.swift': 'swift',
        '.kt': 'kotlin', '.scala': 'scala', '.html': 'html', '.css': 'css', '.scss': 'scss',
        '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown', '.sh': 'bash',
        '.xml': 'xml', '.sql': 'sql', '.dockerfile': 'dockerfile', 'dockerfile': 'dockerfile',
        '.toml': 'toml'
    }
    return mapping.get(ext, '') # Return empty string if no mapping found

# --- Main Script ---

def main():
    parser = argparse.ArgumentParser(
        description="Generate a single text file context for an LLM from a source code directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "directory",
        help="The root directory of the source code.",
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_FILE,
        help="The name of the output text file."
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=MAX_FILE_SIZE_BYTES,
        help="Maximum size for individual files in bytes to be included."
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompt before generating the file."
    )

    args = parser.parse_args()

    root_dir = args.directory
    output_file = args.output
    max_size = args.max_size

    if not os.path.isdir(root_dir):
        print(f"Error: Directory not found: {root_dir}", file=sys.stderr)
        sys.exit(1)

    # --- 1. Load Ignore Patterns ---
    ignore_patterns = load_ignore_patterns(root_dir)

    # --- 2. Scan Directory and Filter Files ---
    print(f"\nScanning directory: {os.path.abspath(root_dir)}")
    all_files_found = []
    included_files = []
    excluded_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # Get relative path for current directory
        rel_dir_path = os.path.relpath(dirpath, root_dir)
        if rel_dir_path == ".":
            rel_dir_path = "" # Use empty string for root

        # --- Filter directories ---
        # Modify dirnames in-place to prevent `os.walk` from traversing ignored directories
        original_dirnames = list(dirnames) # Copy because we modify dirnames
        dirnames[:] = [d for d in original_dirnames if not should_ignore(os.path.join(rel_dir_path, d) + '/', ignore_patterns)]

        # Store excluded directories relative path
        for d in original_dirnames:
             if d not in dirnames:
                 excluded_path = os.path.join(rel_dir_path, d)
                 excluded_files.append(f"{excluded_path}/ (Directory)")


        # --- Filter files ---
        for filename in filenames:
            rel_file_path = os.path.join(rel_dir_path, filename) if rel_dir_path else filename
            full_file_path = os.path.join(dirpath, filename)

            all_files_found.append(rel_file_path)

            # Check ignore patterns
            if should_ignore(rel_file_path, ignore_patterns):
                excluded_files.append(f"{rel_file_path} (Ignored by pattern)")
                continue

            # Check file size
            try:
                file_size = os.path.getsize(full_file_path)
                if file_size > max_size:
                    excluded_files.append(f"{rel_file_path} (Exceeds max size {max_size} bytes)")
                    continue
                if file_size == 0:
                     excluded_files.append(f"{rel_file_path} (Empty file)")
                     continue # Optionally skip empty files
            except OSError as e:
                excluded_files.append(f"{rel_file_path} (Error accessing: {e})")
                continue

            # Basic check for binary files (attempt to read a small chunk)
            is_likely_binary = False
            try:
                with open(full_file_path, 'rb') as f_test:
                    chunk = f_test.read(1024) # Read first 1KB
                    if b'\0' in chunk:
                        is_likely_binary = True
            except Exception as e:
                excluded_files.append(f"{rel_file_path} (Error reading for binary check: {e})")
                continue # Skip if we can't even read it

            if is_likely_binary:
                 excluded_files.append(f"{rel_file_path} (Skipped: Likely binary)")
                 continue

            included_files.append(rel_file_path)


    # --- 3. Display Files and Confirm ---
    print("-" * 60)
    print(f"Found {len(all_files_found)} total files/dirs.")
    print(f"Applying {len(ignore_patterns)} ignore patterns (including defaults).")
    print("-" * 60)

    print(f"\nFiles/Directories to be EXCLUDED ({len(excluded_files)}):")
    if not excluded_files:
        print("  (None)")
    else:
        excluded_files.sort()
        # Limit printing if too many
        display_limit = 20
        for i, f in enumerate(excluded_files):
            if i < display_limit:
                print(f"  - {f}")
            elif i == display_limit:
                print(f"  ... and {len(excluded_files) - display_limit} more.")
                break

    print(f"\nFiles to be INCLUDED ({len(included_files)}):")
    if not included_files:
        print("  (None)")
        print("\nNo files to include. Exiting.")
        sys.exit(0)
    else:
        included_files.sort()
        # Limit printing if too many
        display_limit = 30
        for i, f in enumerate(included_files):
            if i < display_limit:
                 print(f"  - {f}")
            elif i == display_limit:
                print(f"  ... and {len(included_files) - display_limit} more.")
                break

    print("-" * 60)
    print(f"Output will be written to: {os.path.abspath(output_file)}")
    print(f"\nTo exclude specific files/directories, create a '{IGNORE_FILE_NAME}' file")
    print(f"in '{os.path.abspath(root_dir)}' with one pattern per line (e.g., '*.log', 'dist/', 'config. Hjson').")
    print("-" * 60)

    if not args.yes:
        try:
            confirm = input("Proceed with generating the context file? (y/N): ")
            if confirm.lower() != 'y':
                print("Aborted by user.")
                sys.exit(0)
        except EOFError: # Handle piping or non-interactive environments gracefully
             print("\nNon-interactive environment detected or EOF. Aborting.")
             sys.exit(1)


    # --- 4. Generate Output File ---
    print(f"\nGenerating {output_file}...")
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            # --- Header ---
            outfile.write(f"# Project Context for: {os.path.abspath(root_dir)}\n")
            outfile.write(f"# Generated on: {__import__('datetime').datetime.now().isoformat()}\n\n")

            # --- Directory Structure ---
            outfile.write("=" * 80 + "\n")
            outfile.write("== Directory Structure ==\n")
            outfile.write("=" * 80 + "\n\n")
            tree_string = generate_tree_string(root_dir, included_files)
            outfile.write("```\n")
            outfile.write(tree_string)
            outfile.write("\n```\n\n")

            # --- File Contents ---
            outfile.write("=" * 80 + "\n")
            outfile.write("== File Contents ==\n")
            outfile.write("=" * 80 + "\n\n")

            for rel_path in included_files:
                full_path = os.path.join(root_dir, rel_path)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()

                        outfile.write(f"--- START FILE: {rel_path} ---\n")
                        lang_hint = get_language_hint(rel_path)
                        outfile.write(f"```{lang_hint}\n")
                        outfile.write(content.strip()) # Remove leading/trailing whitespace from content
                        outfile.write("\n```\n")
                        outfile.write(f"--- END FILE: {rel_path} ---\n\n")
                except Exception as e:
                    outfile.write(f"--- ERROR READING FILE: {rel_path} ---\n")
                    outfile.write(f"Error: {e}\n")
                    outfile.write(f"--- END ERROR: {rel_path} ---\n\n")
                    print(f"WARNING: Could not read file {rel_path}: {e}", file=sys.stderr)

        print(f"\nSuccessfully generated context file: {os.path.abspath(output_file)}")

    except IOError as e:
        print(f"\nError writing to output file {output_file}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred during file generation: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
