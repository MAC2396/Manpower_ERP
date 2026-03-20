import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY              = 'manpower-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
                                  BASE_DIR, 'manpower.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER           = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH      = 16 * 1024 * 1024
    # Available themes: blue, green, purple, dark, red
    APP_THEME               = 'blue'
    