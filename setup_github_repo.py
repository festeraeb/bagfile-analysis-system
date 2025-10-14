#!/usr/bin/env python3
"""
GitHub Repository Setup for BAG File Analysis System
Creates a private GitHub repository and initializes it with the current codebase.
"""

import os
import subprocess
import json
import requests
from pathlib import Path

class GitHubRepoSetup:
    def __init__(self, repo_name="bagfile-analysis-system", private=True):
        self.repo_name = repo_name
        self.private = private
        self.github_token = self._get_github_token()
        self.username = self._get_github_username()

    def _get_github_token(self):
        """Get GitHub token from environment or prompt user."""
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            print("GitHub token not found in environment variables.")
            print("Please set GITHUB_TOKEN environment variable or enter it below.")
            token = input("Enter your GitHub personal access token: ").strip()
        return token

    def _get_github_username(self):
        """Get GitHub username from git config or prompt user."""
        try:
            result = subprocess.run(['git', 'config', 'user.name'],
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            username = input("Enter your GitHub username: ").strip()
            return username

    def create_repository(self):
        """Create GitHub repository via API."""
        url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "name": self.repo_name,
            "private": self.private,
            "description": "Comprehensive BAG file analysis system for wreck detection, redaction breaking, and maritime data reconstruction",
            "homepage": "",
            "auto_init": False
        }

        print(f"Creating {'private' if self.private else 'public'} repository: {self.repo_name}")

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            repo_data = response.json()
            print(f"✓ Repository created successfully: {repo_data['html_url']}")
            return repo_data['clone_url']
        elif response.status_code == 422:
            print(f"Repository '{self.repo_name}' already exists.")
            # Try to get existing repo URL
            return f"https://github.com/{self.username}/{self.repo_name}.git"
        else:
            print(f"✗ Failed to create repository: {response.status_code}")
            print(response.text)
            return None

    def initialize_git_repo(self, clone_url):
        """Initialize local git repository and push to GitHub."""
        workspace_path = Path.cwd()

        # Check if already a git repo
        if (workspace_path / '.git').exists():
            print("Git repository already exists. Updating remote...")
            subprocess.run(['git', 'remote', 'set-url', 'origin', clone_url], check=True)
        else:
            print("Initializing git repository...")
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'remote', 'add', 'origin', clone_url], check=True)

        # Create .gitignore if it doesn't exist
        gitignore_path = workspace_path / '.gitignore'
        if not gitignore_path.exists():
            self._create_gitignore(gitignore_path)

        # Add all files
        print("Adding files to git...")
        subprocess.run(['git', 'add', '.'], check=True)

        # Initial commit
        print("Creating initial commit...")
        subprocess.run(['git', 'commit', '-m', 'Initial commit: BAG file analysis system'], check=True)

        # Push to GitHub
        print("Pushing to GitHub...")
        subprocess.run(['git', 'push', '-u', 'origin', 'master'], check=True)

        print("✓ Repository initialized and pushed to GitHub successfully!")

    def _create_gitignore(self, path):
        """Create a comprehensive .gitignore file."""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Data files
*.bag
*.tif
*.tiff
*.pdf
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Jupyter Notebook
.ipynb_checkpoints

# Node.js (if any)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Rust
target/
Cargo.lock
"""
        with open(path, 'w') as f:
            f.write(gitignore_content)
        print("✓ Created .gitignore file")

    def create_readme(self):
        """Create or update README.md with project information."""
        readme_path = Path.cwd() / 'README.md'

        if readme_path.exists():
            print("README.md already exists, skipping creation.")
            return

        readme_content = f"""# BAG File Analysis System

A comprehensive toolkit for maritime wreck detection, redaction breaking, and data reconstruction using NOAA BAG files.

## Features

- **BAG File Processing**: Advanced bathymetric data analysis with error handling
- **Wreck Detection**: Multi-mode scanning with ML-based anomaly detection
- **Redaction Breaking**: PDF redaction analysis and content recovery
- **Coordinate Estimation**: Location estimation for wrecks without coordinates
- **Geospatial Export**: KML, GeoJSON, and MBTiles export capabilities
- **Database Integration**: SQLite database with 4,901+ wreck records
- **GUI Interface**: Comprehensive tkinter-based analysis interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/{self.username}/{self.repo_name}.git
cd {self.repo_name}
```

2. Create conda environment:
```bash
conda create -n bag_analysis python=3.8
conda activate bag_analysis
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the comprehensive GUI:
```bash
python comprehensive_bag_gui.py
```

## Database

The system includes a SQLite database (`wrecks.db`) with:
- 4,901 wreck records
- 1,949 records with coordinates
- 597 records with research PDF links
- Coordinate estimation capabilities

## Tools Included

- `robust_bag_scanner.py` - BAG file scanning with error handling
- `multi_mode_scanner.py` - Multi-strategy wreck detection
- `advanced_redaction_breaker.py` - PDF redaction analysis
- `enhanced_wreck_scanner.py` - ML-based wreck detection
- `scrub_detection_engine.py` - Scrubbing pattern detection
- `estimate_locations.py` - Coordinate estimation
- `export_to_kml.py` - KML export
- `prepare_mbtiles.py` - GeoJSON export

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

Private repository - All rights reserved.
"""

        with open(readme_path, 'w') as f:
            f.write(readme_content)
        print("✓ Created comprehensive README.md")

    def create_requirements_txt(self):
        """Create requirements.txt file."""
        requirements_path = Path.cwd() / 'requirements.txt'

        if requirements_path.exists():
            print("requirements.txt already exists, skipping creation.")
            return

        requirements = """# Core dependencies
numpy>=1.21.0
pandas>=1.3.0
matplotlib>=3.4.0
pillow>=8.0.0
requests>=2.25.0
psutil>=5.8.0

# GIS and geospatial
rasterio>=1.2.0
geopandas>=0.9.0
shapely>=1.7.0

# PDF processing
PyPDF2>=1.26.0
pymupdf>=1.18.0
reportlab>=3.5.0

# Machine learning
scikit-learn>=0.24.0
opencv-python>=4.5.0
scipy>=1.7.0
scikit-image>=0.18.0

# Database
sqlite3

# GUI
tkinter

# Development
jupyter>=1.0.0
ipykernel>=5.5.0
"""

        with open(requirements_path, 'w') as f:
            f.write(requirements)
        print("✓ Created requirements.txt")

    def setup_repository(self):
        """Complete repository setup workflow."""
        print("Setting up GitHub repository for BAG File Analysis System...")
        print("=" * 60)

        # Create repository
        clone_url = self.create_repository()
        if not clone_url:
            return False

        # Create/update project files
        self.create_readme()
        self.create_requirements_txt()

        # Initialize git and push
        self.initialize_git_repo(clone_url)

        print("\n" + "=" * 60)
        print("Repository setup complete!")
        print(f"Repository URL: https://github.com/{self.username}/{self.repo_name}")
        print("You can now collaborate and version control your BAG analysis work.")

        return True

def main():
    setup = GitHubRepoSetup()
    success = setup.setup_repository()
    if success:
        print("\nNext steps:")
        print("1. Share the repository URL with collaborators")
        print("2. Set up branch protection rules if needed")
        print("3. Configure CI/CD pipelines for automated testing")
    else:
        print("Repository setup failed. Please check your GitHub token and try again.")

if __name__ == "__main__":
    main()