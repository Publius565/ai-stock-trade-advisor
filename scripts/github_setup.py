#!/usr/bin/env python3
"""
GitHub Repository Setup Script
==============================

This script handles the creation and configuration of the GitHub repository
for the AI-Driven Stock Trade Advisor project.

Features:
- Secure credential management
- Repository creation (private by default)
- Initial push with all project files
- Error handling and user feedback
"""

import os
import sys
import subprocess
import requests
import json
from pathlib import Path

# Add config directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))

from github_config import github_config

class GitHubSetup:
    """GitHub repository setup and management"""
    
    def __init__(self):
        self.config = github_config
        self.api_base = "https://api.github.com"
        self.session = requests.Session()
    
    def setup_authentication(self):
        """Set up GitHub API authentication"""
        token = self.config.get_token()
        if not token:
            print("❌ GitHub token not configured. Please run the configuration first.")
            return False
        
        self.session.headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        })
        return True
    
    def test_connection(self):
        """Test GitHub API connection"""
        try:
            response = self.session.get(f"{self.api_base}/user")
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Connected to GitHub as: {user_data['login']}")
                return True
            else:
                print(f"❌ GitHub API connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def create_repository(self):
        """Create the GitHub repository"""
        repo_name = self.config.get_repo_name()
        description = self.config.get_repo_description()
        
        # Check if repository already exists
        username = self.config.get_username()
        response = self.session.get(f"{self.api_base}/repos/{username}/{repo_name}")
        if response.status_code == 200:
            print(f"✅ Repository '{repo_name}' already exists")
            return True
        
        # Create new repository
        repo_data = {
            'name': repo_name,
            'description': description,
            'private': True,  # Private repository
            'auto_init': False,  # Don't initialize with README
            'gitignore_template': 'Python',
            'license_template': 'mit'
        }
        
        try:
            response = self.session.post(f"{self.api_base}/user/repos", json=repo_data)
            if response.status_code == 201:
                print(f"✅ Repository '{repo_name}' created successfully")
                return True
            else:
                print(f"❌ Failed to create repository: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating repository: {e}")
            return False
    
    def setup_git_remote(self):
        """Set up Git remote for the repository"""
        remote_url = self.config.get_remote_url()
        
        try:
            # Check if remote already exists
            result = subprocess.run(['git', 'remote', '-v'], 
                                  capture_output=True, text=True, check=True)
            if 'origin' in result.stdout:
                print("✅ Git remote 'origin' already configured")
                return True
            
            # Add remote
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url], 
                         check=True)
            print(f"✅ Git remote 'origin' added: {remote_url}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Git remote setup failed: {e}")
            return False
    
    def push_to_github(self):
        """Push all commits to GitHub"""
        try:
            # Push to GitHub
            subprocess.run(['git', 'push', '-u', 'origin', 'master'], 
                         check=True)
            print("✅ Successfully pushed to GitHub")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Push failed: {e}")
            return False
    
    def run_setup(self):
        """Run the complete GitHub setup process"""
        print("\n🚀 GitHub Repository Setup")
        print("=" * 40)
        
        # Step 1: Configure GitHub
        if not self.config.is_configured():
            print("\n📋 GitHub Configuration Required")
            print("-" * 30)
            self.config.display_config()
            return False
        
        # Step 2: Set up authentication
        print("\n🔐 Setting up authentication...")
        if not self.setup_authentication():
            return False
        
        # Step 3: Test connection
        print("\n🔍 Testing GitHub connection...")
        if not self.test_connection():
            return False
        
        # Step 4: Create repository
        print("\n📦 Creating repository...")
        if not self.create_repository():
            return False
        
        # Step 5: Set up Git remote
        print("\n🔗 Setting up Git remote...")
        if not self.setup_git_remote():
            return False
        
        # Step 6: Push to GitHub
        print("\n⬆️  Pushing to GitHub...")
        if not self.push_to_github():
            return False
        
        print("\n🎉 GitHub setup completed successfully!")
        print(f"Repository URL: https://github.com/{self.config.get_username()}/{self.config.get_repo_name()}")
        return True

def main():
    """Main function"""
    setup = GitHubSetup()
    success = setup.run_setup()
    
    if not success:
        print("\n❌ GitHub setup failed. Please check the configuration and try again.")
        sys.exit(1)
    
    print("\n✅ Setup complete! Your repository is now available on GitHub.")

if __name__ == "__main__":
    main() 