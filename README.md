# LLM Code Context Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python script to scan a source code directory, extract the directory structure and relevant file contents, and consolidate them into a single text file optimized for providing context to Large Language Models (LLMs).

## The Problem

Large Language Models are incredibly helpful for understanding, debugging, and refactoring code. However, they often lack the necessary context of the entire project structure and the interplay between different files. Manually copying and pasting dozens of files and explaining the directory layout is tedious and error-prone.

## The Solution

This tool automates the process of gathering codebase context. It walks through your project directory, respects ignore rules (similar to `.gitignore`), generates a visual directory tree, and concatenates the content of the included files into one context file. This file can then be easily pasted into an LLM prompt or used with APIs that accept large text inputs.

## Features

* **Recursive Directory Scanning:** Traverses the specified project directory.
* **`.llmignore` Support:** Uses a `.llmignore` file (similar syntax to `.gitignore`) in the project root to exclude specific files, directories, or patterns (e.g., `node_modules/`, `*.log`, `build/`).
* **Directory Tree Generation:** Creates a textual representation of the included directory structure.
* **File Content Concatenation:** Appends the content of all included files.
* **LLM-Friendly Formatting:** Uses clear delimiters and Markdown code blocks (with language hints based on file extension) for better LLM ingestion.
* **Configurable File Size Limit:** Excludes files larger than a specified size.
* **Binary File Detection:** Attempts to detect and skip binary files.
* **Pre-computation File Listing:** Shows which files will be included/excluded *before* generating the output, allowing you to adjust `.llmignore`.
* **Confirmation Step:** Prompts the user before generating the final file (can be skipped with `-y`).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/llm-code-context-generator.git](https://github.com/your-username/llm-code-context-generator.git)
    cd llm-code-context-generator
    ```
    *(Replace `your-username` with your actual GitHub username)*

2.  **Requirements:**
    * Python 3.6+ is recommended.
    * No external libraries are needed (uses standard Python modules like `os`, `argparse`, `fnmatch`, `pathlib`).

## Usage

```bash
python generate_llm_context.py <path/to/your/codebase> [options]
Arguments:directory: (Required) The root directory of the source code project you want to process.-o, --output: (Optional) The name for the generated context file. Defaults to llm_context.txt.--max-size: (Optional) Maximum size (in bytes) for individual files to be included. Defaults to 1MB (1048576 bytes).-y, --yes: (Optional) Skip the confirmation prompt before generating the file.Example:# Generate context from './my-project', output to 'project_context.txt'
python generate_llm_context.py ./my-project -o project_context.txt

# Generate context from '../another-repo' with default output name 'llm_context.txt'
python generate_llm_context.py ../another-repo

# Generate context, skipping confirmation
python generate_llm_context.py ./my-project -y

# Generate context, only including files smaller than 500KB
python generate_llm_context.py ./my-project --max-size 512000
Using .llmignore:Create a file named .llmignore in the root of the <path/to/your/codebase> directory. Add patterns (files, directories ending with /, or glob patterns like *.ext) one per line. Lines starting with # are ignored.Example .llmignore file:# Ignore dependency directories
node_modules/
vendor/
venv/
__pycache__/

# Ignore build artifacts
build/
dist/
*.o
*.pyc

# Ignore logs and local configs
*.log
*.env
local_settings.py

# Ignore specific large files or data
assets/large_image.jpg
data/big_dataset.csv

# Ignore hidden directories/files commonly used by tools
.git/
.vscode/
.idea/
.DS_Store
The script will automatically pick up and use this file if it exists. It also includes some default ignores (like .git/).Example Output Format (llm_context.txt)# Project Context for: /path/to/your/codebase
# Generated on: 2025-04-23T15:29:00.123456

================================================================================
== Directory Structure ==
================================================================================

\`\`\`
codebase/
├── src/
│   ├── main.py
│   └── utils/
│       └── helpers.py
├── tests/
│   └── test_main.py
└── README.md
\`\`\`

================================================================================
== File Contents ==
================================================================================

--- START FILE: README.md ---
\`\`\`markdown
# My Project

This is the README file.
\`\`\`
--- END FILE: README.md ---

--- START FILE: src/main.py ---
\`\`\`python
import utils.helpers

def run():
    print("Starting main application...")
    utils.helpers.do_something()
    print("Finished.")

if __name__ == "__main__":
    run()
\`\`\`
--- END FILE: src/main.py ---

--- START FILE: src/utils/helpers.py ---
\`\`\`python
def do_something():
    print("Helper function executed.")
\`\`\`
--- END FILE: src/utils/helpers.py ---

--- START FILE: tests/test_main.py ---
\`\`\`python
# Basic test structure
import unittest
# from src.main import run # Example import

class TestMain(unittest.TestCase):
    def test_placeholder(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
\`\`\`
--- END FILE: tests/test_main.py ---

## Use Cases

*   **Debugging:** Provide the LLM with the relevant files and structure to help identify bugs.
*   **Code Explanation:** Ask the LLM to explain specific parts of the code in the context of the whole project.
*   **Refactoring:** Get suggestions from the LLM on how to refactor parts of the codebase.
*   **Onboarding:** Help new team members understand the project structure and key files quickly.
*   **Documentation:** Ask the LLM to help generate documentation stubs based on the code.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue for bugs, feature requests, or improvements.
