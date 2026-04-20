import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY              = 'manpower-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
                                  BASE_DIR, 'manpower.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER           = os.path.join(
                                  BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH      = 16 * 1024 * 1024

    # Performance settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping'    : True,
        'pool_recycle'     : 300,
        'connect_args'     : {
            'timeout'      : 30,
            'check_same_thread': False
        }
    }
    # Session
    SESSION_COOKIE_SECURE    = False
    SESSION_COOKIE_HTTPONLY  = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours