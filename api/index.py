import os
import sys

# Vercel entry point
# Add the compiled code directory to sys.path
# Note: Vercel places code in /var/task usually, so we ensure root is in path

current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to get to project root
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Also add jesse_saas specifically if needed, but project_root + relative imports should work
# if app code is in jesse_saas package

from jesse_saas.app import create_app

app = create_app()

# Vercel requires the variable 'app' to be available
