#!/usr/bin/env python3
"""
Backend structure and configuration test
Tests code structure, imports, and configuration without requiring all dependencies
"""

import sys
import os
import ast
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def test_file_exists(filepath, description):
    """Test if a file exists"""
    if os.path.exists(filepath):
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} missing: {filepath}")
        return False

def test_file_syntax(filepath):
    """Test if a Python file has valid syntax"""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read(), filepath)
        return True
    except SyntaxError as e:
        print_error(f"Syntax error in {filepath}: {e}")
        return False
    except Exception as e:
        print_warning(f"Could not parse {filepath}: {e}")
        return False

def test_import_structure(filepath, expected_imports):
    """Test if file contains expected imports"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        missing = []
        for imp in expected_imports:
            if imp not in content:
                missing.append(imp)
        
        if missing:
            print_warning(f"{filepath} missing imports: {', '.join(missing)}")
            return False
        return True
    except Exception as e:
        print_warning(f"Could not check imports in {filepath}: {e}")
        return False

def test_directory_structure():
    """Test backend directory structure"""
    print_info("Testing directory structure...")
    print()
    
    backend_dir = Path(__file__).parent
    app_dir = backend_dir / "app"
    
    required_files = [
        (app_dir / "main.py", "Main application"),
        (app_dir / "config.py", "Configuration"),
        (app_dir / "database.py", "Database module"),
        (app_dir / "celery_app.py", "Celery app"),
        (app_dir / "api" / "auth.py", "Auth API"),
        (app_dir / "api" / "brands.py", "Brands API"),
        (app_dir / "api" / "campaigns.py", "Campaigns API"),
        (app_dir / "api" / "chat.py", "Chat API"),
        (app_dir / "tasks" / "video_generation.py", "Video generation task"),
        (backend_dir / "start.sh", "Start script"),
        (backend_dir / "start-worker.sh", "Worker start script"),
        (backend_dir / "requirements.txt", "Requirements file"),
        (backend_dir / "Procfile", "Procfile"),
    ]
    
    results = []
    for filepath, description in required_files:
        results.append(test_file_exists(str(filepath), description))
    
    print()
    return all(results)

def test_python_syntax():
    """Test Python syntax of key files"""
    print_info("Testing Python syntax...")
    print()
    
    backend_dir = Path(__file__).parent
    app_dir = backend_dir / "app"
    
    python_files = [
        app_dir / "main.py",
        app_dir / "config.py",
        app_dir / "database.py",
        app_dir / "celery_app.py",
        app_dir / "api" / "auth.py",
        app_dir / "api" / "brands.py",
        app_dir / "api" / "campaigns.py",
        app_dir / "tasks" / "video_generation.py",
    ]
    
    results = []
    for filepath in python_files:
        if filepath.exists():
            if test_file_syntax(str(filepath)):
                print_success(f"Syntax OK: {filepath.name}")
            else:
                results.append(False)
        else:
            print_warning(f"File not found: {filepath}")
            results.append(False)
    
    print()
    return all(results)

def test_imports():
    """Test import structure"""
    print_info("Testing import structure...")
    print()
    
    backend_dir = Path(__file__).parent
    app_dir = backend_dir / "app"
    
    import_tests = [
        (app_dir / "main.py", ["import logging", "from fastapi import"]),
        (app_dir / "celery_app.py", ["import logging", "from celery import", "from app.config"]),
        (app_dir / "database.py", ["import logging", "from sqlalchemy"]),
        (app_dir / "tasks" / "video_generation.py", ["import logging", "from app.celery_app"]),
        (app_dir / "api" / "campaigns.py", ["from app.tasks.video_generation", "from app.celery_app"]),
    ]
    
    results = []
    for filepath, expected in import_tests:
        if filepath.exists():
            if test_import_structure(str(filepath), expected):
                print_success(f"Imports OK: {filepath.name}")
                results.append(True)
            else:
                results.append(False)
        else:
            print_warning(f"File not found: {filepath}")
            results.append(False)
    
    print()
    return all(results)

def test_no_duplicate_directories():
    """Test that queue directory is removed"""
    print_info("Testing for removed duplicates...")
    print()
    
    backend_dir = Path(__file__).parent
    
    # Check queue directory is removed
    queue_dir = backend_dir / "queue"
    if queue_dir.exists():
        print_error(f"Queue directory still exists: {queue_dir}")
        return False
    else:
        print_success("Queue directory removed (consolidated to app/)")
    
    # Check railway.json is removed
    railway_json = backend_dir / "railway.json"
    if railway_json.exists():
        print_warning("railway.json still exists (should use railway.toml)")
    else:
        print_success("railway.json removed (using railway.toml)")
    
    print()
    return True

def test_startup_scripts():
    """Test startup scripts"""
    print_info("Testing startup scripts...")
    print()
    
    backend_dir = Path(__file__).parent
    
    # Test start.sh
    start_sh = backend_dir / "start.sh"
    if start_sh.exists():
        with open(start_sh) as f:
            content = f.read()
            if "app.celery_app" in content or "app.main" in content:
                print_success("start.sh uses correct app paths")
            else:
                print_warning("start.sh might have incorrect paths")
            
            if "queue.celery_app" in content:
                print_error("start.sh still references queue.celery_app (should be app.celery_app)")
                return False
    else:
        print_error("start.sh not found")
        return False
    
    # Test start-worker.sh
    worker_sh = backend_dir / "start-worker.sh"
    if worker_sh.exists():
        with open(worker_sh) as f:
            content = f.read()
            if "app.celery_app" in content:
                print_success("start-worker.sh uses app.celery_app")
            else:
                print_error("start-worker.sh should use app.celery_app")
                return False
            
            if "queue.celery_app" in content:
                print_error("start-worker.sh still references queue.celery_app")
                return False
    else:
        print_error("start-worker.sh not found")
        return False
    
    print()
    return True

def test_logging_implementation():
    """Test logging is implemented"""
    print_info("Testing logging implementation...")
    print()
    
    backend_dir = Path(__file__).parent
    app_dir = backend_dir / "app"
    
    files_to_check = [
        (app_dir / "main.py", ["import logging", "logger = logging.getLogger"]),
        (app_dir / "celery_app.py", ["import logging", "logger = logging.getLogger"]),
        (app_dir / "database.py", ["import logging", "logger = logging.getLogger"]),
        (app_dir / "tasks" / "video_generation.py", ["import logging", "logger = logging.getLogger"]),
        (app_dir / "api" / "auth.py", ["import logging", "logger = logging.getLogger"]),
        (app_dir / "api" / "campaigns.py", ["import logging", "logger = logging.getLogger"]),
    ]
    
    results = []
    for filepath, expected in files_to_check:
        if filepath.exists():
            if test_import_structure(str(filepath), expected):
                print_success(f"Logging implemented: {filepath.name}")
                results.append(True)
            else:
                print_warning(f"Logging might be missing in: {filepath.name}")
                results.append(False)
        else:
            results.append(False)
    
    print()
    return all(results)

def main():
    """Run all tests"""
    print("=" * 60)
    print("Backend Structure & Configuration Test")
    print("=" * 60)
    print()
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Python Syntax", test_python_syntax),
        ("Import Structure", test_imports),
        ("No Duplicate Directories", test_no_duplicate_directories),
        ("Startup Scripts", test_startup_scripts),
        ("Logging Implementation", test_logging_implementation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
            passed += 1
        else:
            print_error(f"{test_name}: FAILED")
            failed += 1
    
    print()
    print("=" * 60)
    if failed == 0:
        print_success(f"All tests passed! ({passed}/{len(results)})")
        return 0
    else:
        print_error(f"Some tests failed: {passed} passed, {failed} failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

