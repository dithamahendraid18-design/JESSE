import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # Paths
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    
    # Business Logic / Pricing
    PRICING_PRO_MONTHLY = 49
    TOKEN_COST_PER_INTERACTION = 0.001
