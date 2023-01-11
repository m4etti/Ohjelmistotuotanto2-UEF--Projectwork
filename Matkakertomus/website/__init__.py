from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager


db = SQLAlchemy()
DB_NAME = 'database.db'
UPLOAD_FOLDER = 'static/images'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '1234567890'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    db.init_app(app)
    
    
    from .views import views
    
    app.register_blueprint(views, url_prefix='/')
        
    from  .models import Matkaaja
    
    create_database(app)
        
    login_manager = LoginManager()
    login_manager.login_view = 'views.log_in'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return Matkaaja.query.get(int(id))
    
            
    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('database created')

