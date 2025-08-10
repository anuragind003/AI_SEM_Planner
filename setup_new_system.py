#!/usr/bin/env python3
"""
Setup script for the new multi-source keyword research system.
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def setup_new_system():
    """Set up the new multi-source keyword research system."""
    print("🚀 Setting up new multi-source keyword research system...")
    print()
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: It's recommended to run this in a virtual environment")
        print("   Create one with: python -m venv .venv")
        print("   Activate it with: .venv\\Scripts\\Activate.ps1 (Windows) or source .venv/bin/activate (Unix)")
        print()
    
    # Install new requirements
    if not run_command("pip install -r requirements.txt", "Installing new dependencies"):
        return False
    
    # Install spaCy English model
    if not run_command("python -m spacy download en_core_web_sm", "Installing spaCy English model"):
        return False
    
    # Install Playwright browsers
    if not run_command("playwright install chromium", "Installing Playwright browsers"):
        return False
    
    print()
    print("🎉 Setup completed successfully!")
    print()
    print("📋 Next steps:")
    print("   1. Test the system: python test_new_keyword_system.py")
    print("   2. Run the main pipeline: python -m sem_plan.cli --config config.yaml --out outputs")
    print()
    print("🔧 If you encounter issues:")
    print("   - Make sure all dependencies are installed: pip list")
    print("   - Check spaCy model: python -c 'import spacy; spacy.load(\"en_core_web_sm\")'")
    print("   - Verify Playwright: python -c 'from playwright.sync_api import sync_playwright'")
    
    return True


if __name__ == "__main__":
    success = setup_new_system()
    sys.exit(0 if success else 1)
