from exten.model import Notification, User, db, func
from sqlalchemy import asc, desc
from flask import url_for, redirect
from flask_login import current_user

from funcs import roomid

def get_roomkey(user_id, other_id):
    roomId = {}

    if user_id.id != other_id.id:
        roomId = roomid(user1=user_id, user2=other_id)
    else:
        roomId = user_id
def save_notification(user1, user2, message):
    notice = Notification(user_id=user1.id, user2=user2.id, content = message)
    db.session.add(notice)
    db.session.commit()

def notify(user):
    receiver = Notification.query.filter_by(user2=user.id, read=False).all()
    return receiver

def notify_count(user):
    receiver = Notification.query.filter_by(user2=user.id, read=False).count()
    return receiver

def recent_notify(user):
    receiver = Notification.query.filter_by(user2=user.id, read=False).first()
    return receiver

def mark_read(post_id):
    receiver = Notification.query.filter_by(id=post_id).first()
    if receiver.read == True:
        pass
    elif receiver.read == False:
        receiver.read = True
        db.session.commit()
    else:
        pass



def restrict():
    user=User.query.get(current_user.id)
    if user.roles == 'Creator':
        pass
    else:
        return redirect(url_for('main.homee'))

def denyaccess(user):
    if user.roles != 'Artist':
        return redirect(url_for('home'))
    else:
        pass

