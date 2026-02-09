from flask import Blueprint

# Initialize Blueprint
bp = Blueprint('admin', __name__)

# Import views to register routes
from . import auth
from . import dashboard
from . import clients
from . import menu
from . import bot

# Note: Analytics routes are currently inside clients.py and dashboard.py or not strictly separated yet.
# If we had a separate analytics.py, we'd import it here.
