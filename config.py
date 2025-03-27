import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'your_secret_key_here'  # Change this to a strong secret key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'quiz_master.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
