import os
import sys

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'jesse_saas'))

from jesse_saas.config import Config

print(f"VERCEL ENV: {os.environ.get('VERCEL')}")
print(f"Config DB URI: {Config.SQLALCHEMY_DATABASE_URI}")
print(f"Base Dir: {os.path.abspath(os.path.dirname(os.path.join(os.getcwd(), 'jesse_saas', 'config.py')))}")
