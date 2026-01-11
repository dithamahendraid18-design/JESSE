import os
import sys

# Vercel entry point
# Add the compiled code directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Add project root
sys.path.append(project_root)

# Add 'jesse_saas' directory specifically so we can import 'app' directly
jesse_saas_dir = os.path.join(project_root, 'jesse_saas')
sys.path.append(jesse_saas_dir)

from app import create_app

app = create_app()
