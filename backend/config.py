import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    
    # Prefix postgresql:// if needed for SQLAlchemy 2.0+
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 1. & 4. SQLAlchemy engine options for DB stability (pool_pre_ping, pool_recycle, sslmode)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'sslmode': 'require'
        } if 'sqlite' not in SQLALCHEMY_DATABASE_URI else {}
    }

    # Flask-Mail (Gmail SMTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')       # your Gmail address
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')       # Gmail App Password
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
