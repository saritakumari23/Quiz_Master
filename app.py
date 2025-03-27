from flask import Flask
from config import Config
from models import db
from routes import main
from flask_login import LoginManager 
from flask_migrate import Migrate  # Optional: For database migrations
from werkzeug.security import generate_password_hash
from datetime import datetime
# Initialize Flask extensions
login_manager = LoginManager()
login_manager.login_view = "main.login"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)
    migrate = Migrate(app, db)  # Optional: Flask-Migrate for DB migrations

    # Initialize Flask-Login
    login_manager.init_app(app)

    # Register blueprints
    app.register_blueprint(main)

    # Import admin_routes inside function to avoid circular imports
    from admin_routes import admin
    app.register_blueprint(admin)

    return app

# Define user loader function
from models import User  # Import User model

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_admin():
    admin_email = "admin@gmail.com"
    existing_admin = User.query.filter_by(email=admin_email).first()

    if not existing_admin:
        # Convert date string to Python `date` object
        dob_str = "01-01-2004"  # Example date string
        dob_obj = datetime.strptime(dob_str, "%d-%m-%Y").date()  # Convert to date
        
        admin = User(
            full_name="Admin",
            email=admin_email,
            password=generate_password_hash("admin123", method='pbkdf2:sha256'),
            qualification="BS",
            dob=dob_obj,  # Use the date object instead of a string
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin user created!")


# Call the function when the app starts

  

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        create_admin()  # Ensure tables are created
    app.run(debug=True)
