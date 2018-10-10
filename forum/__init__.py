from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# local import
#from instance.config import app_config

# initialize the db instance
db = SQLAlchemy()

# initialize bcrypt
bcrypt = Bcrypt()
login_manager = LoginManager()


#def create_app(config_name):
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/forum'
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.debug = True
#pp.config.from_object(app_config[config_name])
#app.config.from_pyfile('config.py')

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

# import blueprints here
from forum.views import views_bp

# import models
from forum import models      # noqa

app.register_blueprint(views_bp)

#return app
