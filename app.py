from flask import Flask, make_response, request, render_template, redirect, session, url_for, flash
from flask_login import current_user, LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, send, join_room, leave_room, rooms
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship, joinedload, configure_mappers
from sqlalchemy import desc, asc,func,ForeignKey, Integer, Column, String, Date, VARCHAR, LargeBinary, or_, and_, DateTime
import os
from celery import Celery
from random import random
import string
from flask_mail import Mail, Message
from datetime import timedelta, datetime, timezone, date, time
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
#from werkzeug.security import generate_password_hash, check_password_hash
#from passlib.hash import bcrypt
from flask_bcrypt import Bcrypt
from config import *
from plugin import *



app = Flask(__name__)
#app.register_blueprint(creator, url_prefix='/creator')
apps = Celery(app.name, broker='redis://localhost:6379/0')
app.config.from_object(Config)
app.permanent_session_lifetime = timedelta(minutes=25)
db = SQLAlchemy(app)
mail = Mail(app)
s = URLSafeTimedSerializer('Thisissecret')
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt=Bcrypt(app)
socketio=SocketIO(app, cors_allowed_origins='*')

friends_association = db.Table('friends',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'))
)

followers = db.Table('followers', db.Column('follower_id', Integer, ForeignKey('user.id'), primary_key=True), Column('followed_id', Integer, ForeignKey('user.id'), primary_key=True))

blocked_users = db.Table('blocked_users',
    db.Column('blocker_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('blocked_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    firstname = db.Column(db.String(250), nullable=True)
    lastname = db.Column(db.String(250), nullable=True)
    DOB = Column(Date, nullable=True)
    gender=Column(String(10), nullable=False)
    home_town = db.Column(db.String(400), nullable=True)
    current_city = db.Column(db.String(500), nullable=True)
    country = db.Column(db.String(80), nullable=True)
    phone_number = db.Column(db.String(80), nullable=True)
    cover_photo = db.Column(VARCHAR(250), nullable=True, default='default.jpeg')
    profile_photo = db.Column(VARCHAR(250), nullable=True, default='default.png')
    member_since = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    password = Column(String(250), nullable=False)
    key = Column(String(50), nullable=True)
    confirmed = db.Column(db.Boolean, default=False)
    Bio = db.Column(db.String(2000), nullable=True)
    last_seen = db.Column(DateTime, onupdate=timer())

    # Relationships
    messages_sent = db.relationship('Messages', foreign_keys='Messages.sender_id', backref='sender', lazy='dynamic')
    messages_received = db.relationship('Messages', foreign_keys='Messages.recipient_id', backref='recipient',
                                        lazy='dynamic')

    def is_online(self):
        return (datetime.utcnow() - self.last_seen).total_seconds() < 300  # 5 minutes threshold

    blocked = db.relationship(
        'User', secondary=blocked_users,
        primaryjoin=(blocked_users.c.blocker_id == id),
        secondaryjoin=(blocked_users.c.blocked_id == id),
        backref=db.backref('blocked_by', lazy='dynamic'), lazy='dynamic')

    def block(self, user):
        if not self.has_blocked(user):
            self.blocked.append(user)

    def unblock(self, user):
        if self.has_blocked(user):
            self.blocked.remove(user)

    def has_blocked(self, user):
        return self.blocked.filter(blocked_users.c.blocked_id == user.id).count() > 0

    def blocked_users_list(self):
        return self.blocked.all()
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def mutual_friends(self, user):
        return self.followed.intersect(user.followed).all()
    friends = relationship('User', secondary=friends_association,
                           primaryjoin=(friends_association.c.user_id == id),
                           secondaryjoin=(friends_association.c.friend_id == id),
                           backref=db.backref('added_friends', lazy='dynamic'),
                           lazy='dynamic')

    def add_friend(self, friend):
        if not self.is_friend_with(friend):
            self.friends.append(friend)
            return self

    def remove_friend(self, friend):
        if self.is_friend_with(friend):
            self.friends.remove(friend)
            return self

    def is_friend_with(self, friend):
        #friend = User.query.filter_by(id = friend).first()
        return self.friends.filter(friends_association.c.friend_id == friend.id).count() > 0


# class Privacy(db.Model):
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey('User.id'))
#     user = relationship('User', backref='privacy')

class Story(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    text = Column(String(500))
    image = Column(String(150))
    video = Column(String(150))
    time =Column(DateTime, default=datetime.utcnow)
    expire = Column(DateTime, default=datetime.now(timezone.utc) + timedelta(days=1))



class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __init__(self, body, sender_id, recipient_id):
        self.body = body
        self.sender_id = sender_id
        self.recipient_id = recipient_id
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)


class Admin(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    username= Column(String(240), unique=True, nullable=False)
    email=Column(String(230), unique=True, nullable=False)
    password =Column(String(250), nullable=False)

class System(db.Model):
    id= Column(Integer, primary_key=True)
    sys_name=Column(String(80), nullable=False)
    sys_logo=Column(String(100), nullable=True)
    sys_tagline=Column(String(150), nullable=True)
    sys_icon=Column(String(150), nullable=True)

class Post(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    feelings = Column(String(50))
    content = Column(String(1500))
    privacy = Column(String(150))
    when = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user = relationship("User", back_populates="posts")


class Image(db.Model):
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('post.id'))
    file_info =Column(String(300))
    file_path = Column(LargeBinary(length=(2**32)-1))
    when = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    post = relationship("Post", back_populates="images")
    albums = relationship('Album', back_populates='image', lazy=True)


class Album(db.Model):
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey('image.id'))
    title=Column(String(150))
    description=Column(String(250))
    date=Column(String(80), nullable=False)
    image = relationship('Image', back_populates='albums')

class Video(db.Model):
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('post.id'))
    file_info = Column(String(300))
    file_path = Column(LargeBinary(length=(2**32)-1))
    when = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    post = relationship("Post", back_populates="videos")

class Audio(db.Model):
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('post.id'))
    file_path = Column(LargeBinary(length=(2**32)-1))
    when = Column(String(250))
    post = relationship('Post', back_populates='audios')

class Comment(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    post_id = Column(Integer, ForeignKey('post.id'))
    content = Column(String(1500))
    image = Column(String(150))
    video =Column(String(150))
    when = Column(db.DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    replies = relationship("CommentReply", backref='comment', lazy=True)

class CommentReply(db.Model):
    id = db.Column(Integer, primary_key=True)
    comment_id = Column(Integer, ForeignKey('comment.id'), nullable=False)
    content = Column(String(1500))
    image = Column(String(150))
    video = Column(String(150))
    time = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)



class Like(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    post_id = Column(Integer, ForeignKey('post.id'))
    when = Column(db.DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")

# Establish relationships
User.posts = relationship("Post", order_by=Post.id, back_populates="user")

Post.images = relationship("Image", order_by=Image.id, back_populates="post")
Post.videos = relationship("Video", order_by=Video.id, back_populates="post")
Post.audios = relationship('Audio', order_by=Audio.id, back_populates='post')

User.comments = relationship("Comment", order_by=Comment.id, back_populates="user")
User.likes = relationship("Like", order_by=Like.id, back_populates="user")

Post.comments = relationship("Comment", order_by=Comment.id, back_populates="post")
Post.likes = relationship("Like", order_by=Like.id, back_populates="post")

# with app.app_context():
#     configure_mappers()
#     db.create_all()



os.makedirs(app.config['UPLOAD_FOLDER_IMAGE'], exist_ok=True)


def get_messages():
    # Retrieve all messages from the database
    messages = Messages.query.all()
    income_messages = []

    # Loop through all messages
    for mes in messages:
        # Check if the message was sent by the current user
        if mes.sender_id == current_user.id:
            # If so, it's an outgoing message
            income_messages.append(mes)
        else:
            # Otherwise, it's an incoming message
            # Assuming 'recipient_id' is the correct field name and 'mes.user.username' is the sender's username
            if mes.recipient_id == current_user.id:
                income_messages.append(mes)

    return income_messages

def timefor(dday, dyear):
    now = time.hour or \
        time.minute or \
        time.second
    year = date.year or date.month or date.day
    if (datetime.utcnow() - dday).total_seconds() <= 86400:

        return now
    else:
        return year


def last_seen():
    try:
        user=User.query.get(current_user.id)
        if user:
            user.last_seen = timer()
            db.session.commit()
    except Exception as e:
        print("An error occurred while updating last seen:", e)
        db.session.rollback()



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def show():
    user = User.query.filter_by().first_or_404()
    return user

def timee():
    times =datetime.now()
    return times.year

@app.errorhandler(404)
def page_not(e):
    home=url_for('home')
    return render_template('user/404.html', home=home), 404


@app.before_request
def before_request():
    session.permanent = True



@app.route('/')
def home():
    if session.get('logged_in'):
        last_seen()
        user=User.query.get(current_user.id)
        one =Post.query.order_by(func.random()).first()
        posts=Post.query.order_by(func.random()).all()
        dnd= Post.query.filter_by(user_id=user.id).first()
        comment = Comment.query.filter_by(post_id=one.id).order_by(asc(Comment.when)).all()

        return render_template('user/index.html',dnd=dnd, comment=comment,user=user, usr=user, posts=posts, one=one)
    else:
        return render_template('user/login.html')

@app.route('/posts/<int:post_id>')
def posts(post_id):
    if session.get('logged_in'):
        last_seen()
        user = User.query.get(current_user.id)
        one = Post.query.filter_by(id=post_id).order_by(func.random()).first()
        posts = Post.query.order_by(func.random()).all()
        dnd = Post.query.filter_by(user_id=user.id).first()
        comment = Comment.query.filter_by(post_id=post_id).all()
        return render_template('user/index.html', one=one, posts=posts, comment=comment, dnd=dnd, user=user)
    else:
        return redirect(url_for('login'))

@app.route('/add_story', methods=['POST'])
def add_story():
    if session.get('logged_in'):
        image = request.files.get('photo', None)
        text = request.form.get('text', None)
        video = request.files.get('video', None)
        sub = Story(user_id= current_user.id, text=text, image = image, video=video)
        db.session.add(sub)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@app.route('/create', methods=['POST'])
def create():
    if session.get('logged_in'):
        user=User.query.get(current_user.id)
        content = request.form['content']
        feelings = request.form['feelings']
        image = request.files.getlist('image', None)
        privacy = request.form['privacy']
        post = Post( user_id=user.id,content=content, privacy=privacy,feelings=feelings)
        db.session.add(post)
        db.session.commit()
        for file in image:
            if file.filename:
                image_name = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], image_name)
                file.save(path)
                path_byte = path.encode('utf-8')
                submit = Image(post_id=post.id, file_path=path_byte, file_info=image_name)
                try:
                    db.session.add(submit)
                    db.session.flush()
                    album = Album(image_id=submit.id, title=f'{user.firstname} Photo Posts', date=timer())
                    db.session.add(album)
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    flash('An error occured', 'error')
                    return redirect(request.url)



        flash('Successful', 'success')
        return redirect(url_for('profile', username=user.username))
    else:
        return redirect(url_for('login'))

@app.route('/pass', methods=['POST', 'GET'])
def passchange():
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        current = request.form.get('pass')
        newpass = request.form.get('new')
        repeat = request.form.get('repeat')
        #main = bcrypt.check_password_hash(user.password, current)
        if bcrypt.check_password_hash(user.password, current):
            if newpass != repeat:
                msg = 'Password did not match'
                flash('Password did not match', 'error')
                return render_template('user/settings.html', user=user, msg=msg)

            else:
                hash_password = bcrypt.generate_password_hash(repeat).decode('utf-8')
                user.password = hash_password
                flash('Password changed successfully', 'success')
                msg ='Password changed successfully'
                return render_template('user/settings.html', msgi=msg, user=user)
        else:
            flash('Incorrect password', 'error')
            return render_template('user/settings.html', msg='Incorrect password', user=user)
    else:
        return redirect(url_for('login'))

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if session.get('logged_in'):
        user =User.query.get(current_user.id)
        post= Post.query.get(post_id)
        text = request.form.get('comment')
        if text:
            submit = Comment(post_id=post_id, content=text, user_id=user.id)
            db.session.add(submit)
            db.session.commit()
            flash('Comment added', 'success')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/sett', methods=['POST'])
def sett():
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        firstname = request.form.get('firstname', user.firstname)
        lastname = request.form.get('lastname', user.firstname)
        email = request.form.get('email', user.email)
        username = request.form.get('username', user.username)
        home_town = request.form.get('address', user.home_town)
        current_city = request.form.get('city', user.current_city)
        country = request.form.get('country', user.country)
        DOB = request.form.get('DOB', user.DOB)
        phone_number = request.form.get('phone', user.phone_number)
        gender = request.form.get('gender', user.gender)

        if firstname:
            user.firstname = firstname
        if lastname:
            user.lastname = lastname
        if email:
            user.email = email
        if username:
            user.username = username
        if home_town:
            user.home_town = home_town
        if current_city:
            user.current_city = current_city
        if DOB:
            user.DOB = DOB
        if country:
            user.country = country
        if gender:
            user.gender = gender
        if phone_number:
            user.phone_number = phone_number

        db.session.commit()

        return redirect(url_for('settings', username=user.username))
    else:
        return redirect(url_for('login'))

@app.route('/album_post', methods=['POST'])
def album_post():
    if session.get('logged_in'):
        album_photo =request.files.get('album_photo')
        album_title= request.form['album_title']
        user=User.query.get(current_user.id)
        post=Post(user_id=user.id, content=' ')
        db.session.add(post)
        db.session.commit()
        if album_photo:
            image_name = secure_filename(album_photo.filename)
            path= os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], image_name)
            album_photo.save(path)
            file_byte = path.encode('utf-8')
            image= Image(post_id=post.id, file_path=file_byte, file_info=image_name )
            try:
                db.session.add(image)
                db.session.flush()
                album = Album(image_id=image.id, title=album_title, date=timer())
                db.session.add(album)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                db.session.rollback()
                flash('An error occured', 'error')
                return redirect(request.url)
        flash('Successful', 'success')
        return redirect(url_for('profile', username=user.username))

    else:
        return redirect(url_for('login'))



@app.route('/messenger/<username>')
def messenger(username):
    if session.get('logged_in'):
        other = User.query.filter_by(username=username).first()
        user=User.query.get(current_user.id)
        mess = Messages.query.filter((Messages.sender_id == user.id) & (Messages.recipient_id == other.id) | (Messages.sender_id == other.id) & (Messages.recipient_id == user.id)).order_by(Messages.timestamp.desc()).all()
        return render_template('user/messanger.html', mess=mess, other=other,username=user, user=user)
    else:
        return redirect(url_for('login'))

#for the room

@socketio.on('private_message')
def handle_private_message(payload):
    recipient_id = payload['recipient_id']
    recipient = db.session.get(User, recipient_id)
    if recipient:
        message = Messages(sender_id=current_user.id, recipient_id=recipient.id, body=payload['message'])
        db.session.add(message)
        db.session.commit()
        emit('message', {'message': payload['message'], 'sender_id': current_user.id}, room=recipient.id)
        print(f'{payload['message']}', recipient.username)


@socketio.on('join')
@login_required
def on_join(data):
    room = str(data['recipient_id'])
    join_room(room)
    emit('room_notification', {'message': f'{current_user.username} has entered the room.'}, room=room)
    print(f'{current_user.username} has entered the room.')

@socketio.on('leave')
@login_required
def on_leave(data):
    room = str(data['recipient_id'])
    leave_room(room)
    emit('room_notification', {'message': f'{current_user.username} has left the room.'}, room=room)
    print(f'{current_user.username} has left the room.')


# end of the room



@app.route('/chat/<username>')
def chat(username):
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        other = User.query.filter_by(username=username).first()
        mess = Messages.query.filter(
            (Messages.sender_id == user.id) & (Messages.recipient_id == other.id) | (Messages.sender_id == other.id) & (
                        Messages.recipient_id == user.id)).order_by(asc(Messages.timestamp)).all()

        return render_template('chat.html', user=user,mess=mess, other=other)
    else:
        return redirect(url_for('login'))
@socketio.on('receive_message')
def receive_message(data):
    print(data)
    send(data)

@socketio.on('user_online')
def handle_user_online(json):
    user_id = json['user_id']
    user = User.query.get(user_id)
    user.last_seen = datetime.utcnow()
    db.session.commit()

    # Broadcast the user's online status
    emit('user_online', {'user_id': user_id}, broadcast=True)

@socketio.on('start_typing')
def handle_start_typing(json):
    emit('user_typing', {'user_id': json['sender_id'], 'typing': True}, room=json['recipient_id'])

@socketio.on('stop_typing')
def handle_stop_typing(json):
    emit('user_typing', {'user_id': json['sender_id'], 'typing': False}, room=json['recipient_id'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if session.get('logged_in'):
        return redirect(url_for('home'))
    else:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user= User.query.filter_by(email=email).first()
                #User.query.filter_by(email=username).first()

            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                if user.confirmed:
                    user.key = gene()
                    db.session.commit()
                    resp = make_response(redirect(url_for('home')))


                    resp.set_cookie('session_cookie', 'bvnefhg', httponly=True, secure=True)
                    session['logged_in'] = True
                    return resp
                else:
                    token = s.dumps(email, salt='email-confirm')
                    cmsg = Message('Confirm Email', sender='mailtrap@apptok.top', recipients=[email])
                    veri_code = url_for('confirm_email', token=token, _external=True)
                    cmsg.html = render_template('email_verify.html', veri_code=veri_code)
                    mail.send(cmsg)
                    flash('please confirm your email first', 'error')
                    return render_template('user/login.html', msg=msg)
            else:
                flash('Incorrect username/password!', 'error')
                return render_template('user/login.html', msg=msg)

        return render_template('user/login.html', msg=msg)


@app.route('/def')
def defa():
    veri_code = url_for('register')
    return render_template('email_verify.html', veri_code=veri_code)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('logged_in'):
        return redirect(url_for('home'))
    else:
        pass
    if request.method == 'POST':
        username = request.form['username']
        firstname=request.form['firstname']
        lastname=request.form['lastname']
        email = request.form['email']
        DOB = request.form['DOB']
        country = request.form['country']
        gender= request.form['gender']
        firstpass= request.form['firstpass']
        password = request.form['password']
        #role= request.form['role']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        exists = User.query.filter_by(email=email).first()
        exist = User.query.filter_by(username=username).first()
        if firstpass != password:
            flash('Password Mismatched', 'error')
            return render_template('user/register.html')
        if exists:
            flash('Email Already Exists', 'error')
            return render_template('user/register.html')
        if exist:
            flash('Username Already Exists', 'error')
            return render_template('user/register.html')
        else:
            # Create a new user and add to the database
            new_user = User(country=country,username=username,firstname=firstname, lastname=lastname, email=email,DOB=DOB, gender=gender,  password=hashed_password, profile_photo='default.png', cover_photo='default.jpeg')
            db.session.add(new_user)
            db.session.commit()

            token = s.dumps(email, salt='email-confirm')
            cmsg = Message('Confirm Email', sender='mailtrap@apptok.top', recipients=[email])
            veri_code = url_for('confirm_email', token=token, _external=True)
            cmsg.html = render_template('email_verify.html', veri_code=veri_code)
            mail.send(cmsg)
            flash('Registration successfully', 'success')

            return redirect(url_for('login'))

    return render_template('user/register.html')




@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return '<h1>The token is expired</h1>'
    user = User.query.filter_by(email=email).first_or_404()
    user.confirmed = True
    db.session.commit()
    flash('Your email has been verified!', 'success')
    return redirect(url_for('login'))


def are_friends(user1, user2):
    return user1 in user2.friends and user2 in user1 in user1.friends


@app.route('/settings/<username>')
def settings(username):
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        other = User.query.filter_by(username=username).first()
        return render_template('user/settings.html', other=other, user=user)
    else:
        return redirect(url_for('login'))

@app.route('/profile/<username>')
def profile(username):
    if session.get('logged_in'):
        last_seen()
        other=User.query.filter_by(username=username).first()
        user=User.query.get(current_user.id)
        own_profile=(current_user.is_authenticated and other.username == current_user.username)
        status = (datetime.now() - other.last_seen).total_seconds() < 120
        stat = (datetime.now() - user.last_seen).total_seconds() < 120
        posts=Post.query.filter_by(user_id=other.id).all()
        images = []
        albums = []
        for post in posts:
            post_images = Image.query.filter_by(post_id=post.id).order_by(func.random()).all()
            images.extend(post_images)
            for image in post_images:
                post_album = Album.query.filter_by(image_id=image.id).all()
                albums.extend(post_album)
        # image=Image.query.filter_by(post_id=posts.id).all()
        # album=Album.query.filter_by(image_id=image.id).all()

        return render_template('user/users.html', other=other, stat=stat,own_profile=own_profile, user=user, posts=posts, images=images, albums=albums, status=status)
    else:
        return redirect(url_for('login'))

@app.route('/user/hdhuyuiyihagehtywiacsvsbhysvwuwbwiwhwiodgdtwrwbnbnfdhhfhrfdrtffwggastuyjgjhajdghgjgdyfdytfahgamhayrywyg?hahjgagtywtquteuugaggagsghaghhsyryqeryqtuueuruququteutuqtutquetuettiqi/<int:user_id>')
def userz(user_id):
    if session.get('logged_in'):
        last_seen()
        othr=User.query.get_or_404(user_id)
        user=User.query.get(current_user.id)
        other=User.query.filter_by(id=user_id).first()
        #is_friend = current_user.is_friend_with(othr) or othr.is_friend_with(current_user)
        is_friend = current_user.is_following(othr)
        own_profile=(current_user.is_authenticated and other.username == current_user.username)
        status = (datetime.now() - other.last_seen).total_seconds() < 120
        stat = (datetime.now() - user.last_seen).total_seconds() < 120
        posts=Post.query.filter_by(user_id=other.id).all()
        images = []
        albums = []
        for post in posts:
            post_images = Image.query.filter_by(post_id=post.id).order_by(func.random()).all()
            images.extend(post_images)
            for image in post_images:
                post_album = Album.query.filter_by(image_id=image.id).all()
                albums.extend(post_album)
        # image=Image.query.filter_by(post_id=posts.id).all()
        # album=Album.query.filter_by(image_id=image.id).all()

        return render_template('user/profile.html', is_friend=is_friend,other=other, stat=stat,own_profile=own_profile, user=user, posts=posts, images=images, albums=albums, status=status)
    else:
        return redirect(url_for('login'))

@app.route('/upload_c', methods=['POST'])
def upload_c():
    if session.get('logged_in'):
        user=User.query.get(current_user.id)
        cover = request.files.get('cover')

        if cover:
            cover_name = secure_filename(cover.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], cover_name)
            cover.save(path)
            user.cover_photo = cover_name
            db.session.commit()
        return redirect(url_for('profile', username=user.username))
    else:
        return redirect(url_for('login'))



@app.route('/upload', methods=['POST'])
def upload():
    if session.get('logged_in'):

        photo1 = request.form.get('Radios', None)
        photo2 = request.form.get('Radios1', None)
        photo = request.files.getlist('photo', None)
       # photo1 = request.files.get(profile_photo)
        #photo2 = request.files.get(profiles)
        user=User.query.get(current_user.id)
        post_content = f"{user.lastname} {user.firstname} updated {gender(user.username)} profile picture"
        post = Post(user_id=user.id, content=post_content)

        if photo1:
            # photo_name = secure_filename(photo.filename)
            # path= os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], photo_name)
            # photo.save(path)
            image1 = Image(post_id=post.id, file_info=photo1)
            db.session.add(image1)
            user.profile_photo = photo1
            db.session.commit()

        if photo2:

            image2 = Image(post_id=post.id, file_info=photo2)
            db.session.add(image2)
            user.profile_photo = photo2
            db.session.commit()
        if photo:
            for file in photo:
                if file.filename:
                    photo_name2 = secure_filename(file.filename)
                    path2 = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], photo_name2)
                    file.save(path2)
                    image3 = Image(post_id=post.id, file_info=photo_name2)
                    db.session.add(image3)
                    user.profile_photo = photo_name2
                    db.session.commit()
                flash('Profile picture updated!', 'sucess')
                return redirect(url_for('profile', username=user.username))
            else:
                flash('Something went wrong!', 'error')
                return redirect(url_for('profile', username=user.username))

        else:
            flash('Something went wrong!', 'error')
            return redirect(url_for('profile', username=user.username))
    else:
        return redirect(url_for('login'))


def gender(username):
    user = User.query.filter_by(username=username).first()
    return 'his' if user.gender == 'Male' else 'her'

@app.route('/add_friend/<int:friend_id>', methods=['POST'])
def add_friend(friend_id):
    user = User.query.get_or_404(current_user.id)  # Assuming current_user is the logged-in user
    friend = User.query.get_or_404(friend_id)
    other = User.query.filter_by(username=friend_id)
    user.add_friend(friend)
    db.session.commit()
    flash('Added successfully', 'success')
    return redirect(url_for('user', user_id=friend.id))

@app.route('/remove_friend/<int:friend_id>', methods=['POST'])
def remove_friend(friend_id):
    user = User.query.get_or_404(current_user.id)
    #user = User.query.filter_by(id=friend_id).first()
    friend = User.query.get_or_404(friend_id)

    #other = User.query.filter_by(id=friend_id)
    user.remove_friend(friend)
    db.session.commit()
    flash('Removed successfully', 'success')
    return redirect(url_for('user', user_id=friend.id))


@app.route('/follow/<int:user_id>')
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', user_id=user.id))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following {}.'.format(user.username))
    return redirect(url_for('profile', usr=user.username))

@app.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', user_id=user.id))
    current_user.unfollow(user)
    db.session.commit()
    flash('You have stopped following {}.'.format(user.username))
    return redirect(url_for('profile', usr=user.username))

@app.route('/block/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_id):
    user_to_block = User.query.get_or_404(user_id)
    if user_to_block == current_user:
        flash('You cannot block yourself!')
        return redirect(url_for('home'))
    current_user.block(user_to_block)
    db.session.commit()
    flash('You have blocked {}.'.format(user_to_block.username))
    return redirect(url_for('profile', usr=user_to_block.username))

@app.route('/unblock/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_id):
    user_to_unblock = User.query.get_or_404(user_id)
    current_user.unblock(user_to_unblock)
    db.session.commit()
    flash('You have unblocked {}.'.format(user_to_unblock.username))
    return redirect(url_for('profile', usr=user_to_unblock.username))

# @app.route('/blocked_users')
# @login_required
# def list_blocked_users():
#     blocked_users = current_user.blocked_users_list()
#     return render_template('blocked_users.html', blocked_users=blocked_users)


@app.route('/profile/about/<username>')
def aboutme(username):
    if session.get('logged_in'):
        other = User.query.filter_by(username=username).first()
        user = User.query.get(current_user.id)
        own_profile = (current_user.is_authenticated and other.username == current_user.username)
        status = (datetime.now() - other.last_seen).total_seconds() < 120
        stat = (datetime.now() - user.last_seen).total_seconds() < 120
        return render_template('user/profile-about.html', user=user, username=user.username, other=other, stat=stat, status=status, own_profile=own_profile)
    else:
        return redirect(url_for('login'))

@app.route('/profile/friends/<username>')
def friends(username):
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        other = User.query.filter_by(username=username).first()
        return render_template('user/profile-friends.html', username=user.username, other=other)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    if session.get('logged_in'):
        session.pop('logged_in', None)
        resp = make_response(redirect(url_for('login')))
        resp.delete_cookie('session_cookie')
        return resp
    else:
        return redirect(url_for('login'))


@apps.task
def delete_story():
    current_time = datetime.utcnow()
    expired_one = Story.query.filter(Story.expire < current_time).all()
    for dele in expired_one:
        db.session.delete(dele)
    db.session.commit()



if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
