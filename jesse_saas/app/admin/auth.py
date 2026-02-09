from flask import render_template, request, redirect, url_for, session, flash, Blueprint
from config import Config

# bp line removed

def is_logged_in():
    return session.get('admin_logged_in')

def require_login():
    if request.endpoint == 'static': # Allow global static files
        return
        
    # We might need to adjust allowed_routes if the endpoint names change with blueprints
    # But if we register the blueprint correctly, endpoints will be 'admin.login', etc.
    # Note: Using 'admin.login' implies all these are under the 'admin' blueprint namespace.
    # If we split into multiple blueprints, this might become 'admin_auth.login'.
    # HOWEVER, the goal is to keep the 'admin' blueprint and just split the VIEWS.
    # So we should probably keep them all attached to the MAIN 'admin' blueprint object imported from . 
    # OR we follow the plan: "app/admin/__init__.py: Registry for the blueprint."
    # If we define `bp` in `__init__`, we can import it here.
    
    # Strategy: Define `bp` in `app/admin/__init__.py` and import it here to attach routes.
    # BUT circular imports are risky.
    # Better Strategy: Define routes here using a local `bp` or `route` helper, 
    # then in `__init__.py` import these modules.
    # Wait, if `__init__.py` creates the Blueprint, and we import it here:
    # from . import bp
    # @bp.route...
    # Then `__init__.py` also needs to import THIS file to register the routes. Circular import!
    
    # Standard Flask Pattern:
    # 1. __init__.py creates `bp = Blueprint('admin', __name__)`
    # 2. __init__.py imports content: `from . import auth, clients, ...` at the END.
    # 3. modules import `bp` from `.`: `from . import bp`
    
    # Let's assume we will update __init__.py to export `bp`.
    pass

# TEMPORARY CONTENT: I cannot rely on importing `bp` from `.` yet because `__init__.py` hasn't been updated to validly export it without the old routes.
# So I will write this file assuming `from . import bp` works, and then I will update `__init__.py` immediately after.

from . import bp

@bp.before_request
def check_login():
    if request.endpoint == 'static':
        return
    
    # The endpoint names might be 'admin.login' 
    allowed_routes = ['admin.login', 'admin.static']
    # Also check if the request endpoint starts with admin. and is not login
    if request.endpoint and request.endpoint.startswith('admin.') and request.endpoint not in allowed_routes and not is_logged_in():
        return redirect(url_for('admin.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Allow accessing login page even if logged in (to force re-login)
    pass

    if request.method == 'POST':
        password = request.form.get('password')
        admin_pass = Config.ADMIN_PASSWORD
        
        if password == admin_pass:
            session.clear() # Clear old session first
            session['admin_logged_in'] = True
            session.permanent = False # Browser session only (cleared on close)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid Password')
            
    return render_template('admin/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))
