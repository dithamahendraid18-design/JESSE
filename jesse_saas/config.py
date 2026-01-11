import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    # Database: Prefer specific Vercel URL, then generic DATABASE_URL
    # Fallback to SQLite. On Vercel, must use /tmp (writable) instead of root (read-only)
    _db_url = os.environ.get('POSTGRES_URL_NON_POOLING') or os.environ.get('DATABASE_URL')
    
    if _db_url and _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    if not _db_url:
        if os.environ.get('VERCEL'):
             # Vercel Runtime: Use /tmp
             print("⚠️  WARNING: Running on Vercel without DATABASE_URL. Using ephemeral SQLite in /tmp. DATA WILL BE LOST.")
             _db_url = 'sqlite:////tmp/site.db'
        else:
             # Local Dev: Use project folder
             print("ℹ️  Running locally. Using local site.db.")
             _db_url = 'sqlite:///' + os.path.join(basedir, 'site.db')
    else:
        print(f"✅  Database configured from environment: {_db_url.split('@')[-1] if '@' in _db_url else 'External DB'}")

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # Paths
    # Paths
    if os.environ.get('VERCEL'):
        UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
    else:
        UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    
    # Business Logic / Pricing
    PRICING_PRO_MONTHLY = 49
    TOKEN_COST_PER_INTERACTION = 0.001
