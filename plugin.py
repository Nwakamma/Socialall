from flask_sqlalchemy import  SQLAlchemy
from datetime import datetime
import random
import string
from flask_limiter import Limiter
from flask_bcrypt import Bcrypt
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_socketio import SocketIO

db = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
socketio=SocketIO( cors_allowed_origins='*')

def file_allow(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def timer():
    tom = datetime.now()
    return tom



def gene():
    char = string.ascii_uppercase + string.digits
    tracker_no = ''.join(random.choices(char, k=6))
    return tracker_no

def gener():
    char = string.ascii_uppercase + string.digits
    tracker_no = ''.join(random.choices(char, k=8))
    return tracker_no