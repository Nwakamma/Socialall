import os
from exten.model import User, Messages
from flask import render_template, request, abort, Blueprint, redirect, url_for, session
from flask_login import current_user
from funcs import me, search_hist, roomid


tw = Blueprint('tw',__name__)


@tw.route('/')
def home():
    if session.get('logged_in'):
        return redirect(url_for('tw.index', username=me().username))
    else:
        return redirect(url_for('login'))



@tw.route('/video/<username>')
def index(username):
    if session.get('logged_in'):
        user = me()
        other = User.query.filter_by(username=username).first()
        roomId = {}

        if user.id != other.id:
            roomId = roomid(user1=user, user2=other)
        else:
            roomId = user

        return render_template('video/index.html', user=user, other=other, search=search_hist(user_id=user.id), roomId=roomId, roomid=roomId)
    else:
        return redirect(url_for('login'))

