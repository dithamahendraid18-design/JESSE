import sys
import os

# Add the current directory to sys.path to ensure imports work correctly
# This script should be located in the same directory as run.py
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    print(f"Starting migration in: {current_dir}")
    from run import app
    from flask_migrate import upgrade
    
    with app.app_context():
        print("Executing flask_migrate.upgrade()...")
        upgrade()
        print("✅ Migration successful!")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Check if flask_migrate and other dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
