import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    # Database: Prefer specific Vercel URL, then generic DATABASE_URL, then sqlite fallback
    # Also fix 'postgres://' legacy prefix for SQLAlchemy
    _db_url = os.environ.get('POSTGRES_URL_NON_POOLING') or os.environ.get('DATABASE_URL')
    if _db_url and _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url or 'sqlite:///' + os.path.join(basedir, 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # Paths
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    
    # Business Logic / Pricing
    PRICING_PRO_MONTHLY = 49
    TOKEN_COST_PER_INTERACTION = 0.001
