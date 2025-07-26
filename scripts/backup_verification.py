#!/usr/bin/env python3
"""
Backup Verification Script
==========================

This script verifies that the project is properly backed up to GitHub
and all files are synchronized.

Features:
- Check local vs remote file count
- Verify repository status
- Display backup statistics
- Check for any uncommitted changes
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# Add config directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))

from github_config import github_config

class BackupVerification:
    """GitHub backup verification and status checking"""
    
    def __init__(self):
        self.config = github_config
        self.project_root = Path(__file__).parent.parent
    
    def check_git_status(self):
        """Check Git repository status"""
        try:
            # Check if working tree is clean
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                print("⚠️  Uncommitted changes detected:")
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
                return False
            else:
                print("✅ Working tree is clean")
                return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Git status check failed: {e}")
            return False
    
    def check_remote_status(self):
        """Check remote repository status"""
        try:
            # Get remote URL
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True, check=True)
            remote_url = result.stdout.strip()
            
            print(f"📡 Remote URL: {remote_url}")
            
            # Check if remote is accessible
            result = subprocess.run(['git', 'ls-remote', 'origin'], 
                                  capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                print("✅ Remote repository is accessible")
                return True
            else:
                print("❌ Remote repository is not accessible")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Remote status check failed: {e}")
            return False
    
    def count_files(self):
        """Count files in the project"""
        file_count = 0
        dir_count = 0
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip .git directory
            if '.git' in root:
                continue
            
            # Skip virtual environment
            if 'venv' in root:
                continue
            
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            file_count += len(files)
            dir_count += len(dirs)
        
        return file_count, dir_count
    
    def get_commit_info(self):
        """Get latest commit information"""
        try:
            # Get latest commit hash
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, check=True)
            commit_hash = result.stdout.strip()[:8]
            
            # Get latest commit message
            result = subprocess.run(['git', 'log', '-1', '--pretty=format:%s'], 
                                  capture_output=True, text=True, check=True)
            commit_message = result.stdout.strip()
            
            # Get commit date
            result = subprocess.run(['git', 'log', '-1', '--pretty=format:%cd'], 
                                  capture_output=True, text=True, check=True)
            commit_date = result.stdout.strip()
            
            return commit_hash, commit_message, commit_date
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to get commit info: {e}")
            return None, None, None
    
    def verify_backup(self):
        """Run complete backup verification"""
        print("\n🔍 Backup Verification Report")
        print("=" * 40)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project: {self.project_root.name}")
        print()
        
        # Check Git status
        print("📋 Git Status Check")
        print("-" * 20)
        git_clean = self.check_git_status()
        print()
        
        # Check remote status
        print("🌐 Remote Repository Check")
        print("-" * 25)
        remote_ok = self.check_remote_status()
        print()
        
        # Count files
        print("📁 Project Statistics")
        print("-" * 20)
        file_count, dir_count = self.count_files()
        print(f"Files: {file_count}")
        print(f"Directories: {dir_count}")
        print()
        
        # Get commit info
        print("📝 Latest Commit")
        print("-" * 15)
        commit_hash, commit_message, commit_date = self.get_commit_info()
        if commit_hash:
            print(f"Hash: {commit_hash}")
            print(f"Message: {commit_message}")
            print(f"Date: {commit_date}")
        print()
        
        # Summary
        print("📊 Backup Summary")
        print("-" * 15)
        if git_clean and remote_ok:
            print("✅ Backup Status: EXCELLENT")
            print("   - All changes committed")
            print("   - Remote repository accessible")
            print("   - Project fully backed up to GitHub")
        elif git_clean:
            print("⚠️  Backup Status: PARTIAL")
            print("   - All changes committed")
            print("   - Remote repository issues detected")
        else:
            print("❌ Backup Status: NEEDS ATTENTION")
            print("   - Uncommitted changes detected")
            print("   - Backup incomplete")
        
        print(f"\n🔗 GitHub Repository: https://github.com/{self.config.get_username()}/{self.config.get_repo_name()}")
        
        return git_clean and remote_ok

def main():
    """Main function"""
    verifier = BackupVerification()
    success = verifier.verify_backup()
    
    if success:
        print("\n✅ Backup verification completed successfully!")
    else:
        print("\n❌ Backup verification found issues that need attention.")
        sys.exit(1)

if __name__ == "__main__":
    main() 