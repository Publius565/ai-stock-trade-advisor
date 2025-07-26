"""
GitHub Configuration and Credential Management
=============================================

This module handles GitHub repository configuration and credential storage
for the AI-Driven Stock Trade Advisor project.

Security Notes:
- Credentials are stored in environment variables or secure credential manager
- Never commit actual credentials to version control
- Use GitHub Personal Access Tokens for authentication
"""

import os
import getpass
from pathlib import Path
from typing import Optional, Dict, Any
import json

class GitHubConfig:
    """Secure GitHub configuration management"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "github_settings.json"
        self.credentials_file = self.config_dir / ".github_credentials"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Load existing configuration
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load GitHub settings from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}
    
    def _save_settings(self):
        """Save GitHub settings to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def get_repo_name(self) -> str:
        """Get the GitHub repository name"""
        return self.settings.get('repo_name', 'ai-stock-trade-advisor')
    
    def get_repo_description(self) -> str:
        """Get the GitHub repository description"""
        return self.settings.get('repo_description', 
                                'AI-Driven Stock Trade Advisor - Local desktop application for personalized trading recommendations')
    
    def get_username(self) -> Optional[str]:
        """Get GitHub username from environment or prompt"""
        # Try environment variable first
        username = os.getenv('GITHUB_USERNAME')
        if username:
            return username
        
        # Try stored settings
        username = self.settings.get('username')
        if username:
            return username
        
        # Prompt user
        username = input("Enter your GitHub username: ").strip()
        if username:
            self.settings['username'] = username
            self._save_settings()
            return username
        
        return None
    
    def get_token(self) -> Optional[str]:
        """Get GitHub Personal Access Token securely"""
        # Try environment variable first
        token = os.getenv('GITHUB_TOKEN')
        if token:
            return token
        
        # Try stored credentials (encrypted in production)
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'r') as f:
                    stored_token = f.read().strip()
                if stored_token:
                    return stored_token
            except FileNotFoundError:
                pass
        
        # Prompt user for token
        print("\nGitHub Personal Access Token Required")
        print("=====================================")
        print("To create a token:")
        print("1. Go to GitHub.com → Settings → Developer settings → Personal access tokens")
        print("2. Click 'Generate new token' → 'Generate new token (classic)'")
        print("3. Select scopes: 'repo' (full control of private repositories)")
        print("4. Copy the generated token")
        print()
        
        token = getpass.getpass("Enter your GitHub Personal Access Token: ").strip()
        if token:
            # Store token securely (in production, this should be encrypted)
            with open(self.credentials_file, 'w') as f:
                f.write(token)
            # Set file permissions to user-only (Unix-like systems)
            try:
                os.chmod(self.credentials_file, 0o600)
            except OSError:
                pass  # Windows doesn't support chmod
            return token
        
        return None
    
    def get_remote_url(self) -> str:
        """Generate the GitHub remote URL"""
        username = self.get_username()
        repo_name = self.get_repo_name()
        return f"https://github.com/{username}/{repo_name}.git"
    
    def is_configured(self) -> bool:
        """Check if GitHub is properly configured"""
        return bool(self.get_username() and self.get_token())
    
    def display_config(self):
        """Display current configuration (without sensitive data)"""
        print("\nGitHub Configuration")
        print("====================")
        print(f"Username: {self.get_username() or 'Not set'}")
        print(f"Repository: {self.get_repo_name()}")
        print(f"Description: {self.get_repo_description()}")
        print(f"Token: {'Configured' if self.get_token() else 'Not set'}")
        print(f"Remote URL: {self.get_remote_url()}")
        print()

# Global instance
github_config = GitHubConfig() 