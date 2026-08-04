#!/usr/bin/env python3
"""
Build Validation Test Suite

This script validates that the project can be successfully built and deployed.
It runs as part of the GitHub Actions CI/CD pipeline.
"""

import sys
import ast
import os
from pathlib import Path


def validate_python_syntax(file_path):
    """Validate Python syntax of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ast.parse(f.read(), filename=file_path)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def validate_all_python_files():
    """Validate all Python files in the project."""
    errors = []
    files_checked = 0

    # Files to validate
    python_files = [
        'app.py',
        'src/config.py',
        'src/models.py',
        'src/agent_engine.py',
    ]

    print("=" * 60)
    print("Python Syntax Validation")
    print("=" * 60)

    for file_path in python_files:
        if not os.path.exists(file_path):
            print(f"⚠ SKIP  {file_path} (file not found)")
            continue

        files_checked += 1
        is_valid, error = validate_python_syntax(file_path)

        if is_valid:
            print(f"✓ PASS  {file_path}")
        else:
            print(f"✗ FAIL  {file_path}")
            errors.append((file_path, error))

    print("")
    print(f"Files checked: {files_checked}")

    return errors


def validate_imports():
    """Validate that critical modules can be imported."""
    errors = []

    print("=" * 60)
    print("Import Validation")
    print("=" * 60)

    modules_to_test = [
        ('streamlit', 'streamlit'),
        ('langchain', 'langchain'),
        ('app', './app.py'),
    ]

    for module_name, display_name in modules_to_test:
        try:
            if module_name == 'app':
                # For local modules, just check the file exists
                if os.path.exists(display_name):
                    with open(display_name, 'r') as f:
                        compile(f.read(), display_name, 'exec')
                    print(f"✓ PASS  {display_name} (can be compiled)")
                else:
                    print(f"✗ FAIL  {display_name} (file not found)")
                    errors.append((module_name, f"{display_name} not found"))
            else:
                __import__(module_name)
                print(f"✓ PASS  {module_name} (import successful)")
        except Exception as e:
            print(f"✗ FAIL  {module_name}")
            errors.append((module_name, str(e)))

    print("")
    return errors


def validate_dependencies():
    """Validate that all dependencies are available."""
    errors = []

    print("=" * 60)
    print("Dependency Validation")
    print("=" * 60)

    required_packages = [
        'streamlit',
        'langchain',
        'langchain_core',
        'langchain_google_genai',
        'google.generativeai',
        'langgraph',
        'pydantic',
        'dotenv',
        'requests',
        'pytest',
    ]

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ PASS  {package}")
        except ImportError as e:
            print(f"✗ FAIL  {package}")
            errors.append((package, str(e)))

    print("")
    return errors


def validate_project_structure():
    """Validate that the project structure is correct."""
    errors = []

    print("=" * 60)
    print("Project Structure Validation")
    print("=" * 60)

    required_files = [
        'app.py',
        'requirements.txt',
        'README.md',
        '.github/workflows/deploy.yml',
    ]

    required_dirs = [
        'src',
        'pages',
        '.github/workflows',
    ]

    for file_path in required_files:
        if os.path.isfile(file_path):
            print(f"✓ PASS  {file_path}")
        else:
            print(f"✗ FAIL  {file_path} (missing)")
            errors.append((file_path, "File not found"))

    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✓ PASS  {dir_path}/")
        else:
            print(f"✗ FAIL  {dir_path}/ (missing)")
            errors.append((dir_path, "Directory not found"))

    print("")
    return errors


def validate_configuration():
    """Validate configuration files."""
    errors = []

    print("=" * 60)
    print("Configuration Validation")
    print("=" * 60)

    # Check if pyproject.toml exists and is valid
    if os.path.exists('pyproject.toml'):
        try:
            with open('pyproject.toml', 'r') as f:
                content = f.read()
                if '[project]' in content or '[build-system]' in content:
                    print("✓ PASS  pyproject.toml (valid structure)")
                else:
                    print("⚠ WARN  pyproject.toml (missing standard sections)")
        except Exception as e:
            print(f"✗ FAIL  pyproject.toml ({e})")
            errors.append(('pyproject.toml', str(e)))
    else:
        print("⚠ WARN  pyproject.toml (not found, optional)")

    # Check langgraph.json if it exists
    if os.path.exists('langgraph.json'):
        try:
            import json
            with open('langgraph.json', 'r') as f:
                json.load(f)
            print("✓ PASS  langgraph.json (valid JSON)")
        except Exception as e:
            print(f"⚠ WARN  langgraph.json ({e})")
    else:
        print("⚠ SKIP  langgraph.json (not found, optional)")

    print("")
    return errors


def main():
    """Run all validation tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + " GitHub Actions CI/CD Build Validation ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print("")

    all_errors = []

    # Run all validation steps
    all_errors.extend(validate_project_structure())
    all_errors.extend(validate_python_syntax('app.py'))
    all_errors.extend(validate_dependencies())
    all_errors.extend(validate_imports())
    all_errors.extend(validate_configuration())

    # Summary
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)

    if all_errors:
        print(f"\n✗ FAILED: {len(all_errors)} error(s) found\n")
        for item, error in all_errors:
            print(f"  • {item}: {error}")
        return 1
    else:
        print("\n✓ SUCCESS: All validations passed!\n")
        return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
