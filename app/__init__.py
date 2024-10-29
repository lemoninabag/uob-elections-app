import os
from flask import Flask
from .main.routes import main_bp
from .auth.routes import auth_bp
from .register.routes import register_bp
from .vote.routes import vote_bp
from dotenv import load_dotenv
from app.session_manager import active_sessions


app = Flask(__name__, template_folder='templates')

def create_app():
    active_sessions.clear()
    app = Flask(__name__, template_folder="templates")
    app.secret_key = os.getenv('FLASK_SECRET_KEY')  
    app.config['DEBUG'] = True

    
    load_dotenv() 

    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(register_bp, url_prefix='/register')
    app.register_blueprint(vote_bp, url_prefix='/vote')

    return app
