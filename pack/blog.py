from flask import Flask, Blueprint, render_template, session,current_app, flash,redirect, url_for, request, make_response
from flask_socketio import emit, join_room, leave_room, send
from exten.model import *
from werkzeug.utils import secure_filename
import os
import uuid
from funcs import me, total_p, total_v, total_s, roomid
from flask_login import login_user, current_user
from sqlalchemy import asc, func, desc
from plugin import *





blog = Blueprint('blog', __name__, static_folder='static')

@blog.context_processor
def context_processor():
    def is_logg():
        return current_user.is_authenticated
    return dict(is_logg=is_logg)

@blog.route('/')
def home():
    post = BlogPost.query.order_by(asc(func.random())).all()
    trend = BlogPost.query.order_by(func.random()).limit(4).all()
    cate = BlogCategory.query.all()
    catt = BlogCategory.query.order_by(func.random()).limit(4).all()
    tags = Tag.query.all()
    busi = BlogPost.query.filter_by(category='Business').all()
    tech = BlogPost.query.filter_by(category='Technology').all()
    sports = BlogPost.query.filter_by(category='Sports').all()
    edu = BlogPost.query.filter_by(category='Education').all()
    return render_template('blog/index.html',  posts=post, trending=trend, catt=catt, sports=sports, edu=edu,tech=tech,busi=busi,date=timer(), cate=cate, tags=tags)

@blog.route('/categories/<category>')
def categ(category):
    categ = BlogPost.query.filter_by(category=category).all()
    trend = BlogPost.query.order_by(func.random()).limit(4).all()
    tags = Tag.query.all()
    catt = BlogCategory.query.order_by(func.random()).limit(4).all()
    cate = BlogCategory.query.all()
    return render_template('blog/category.html',  catt=catt,cate=cate, categ=categ, trending=trend,tags=tags, date=timer(), category=category)
    # if not categ:
    #     return redirect(url_for('blog.home'))
    # else:
    #     tags = Tag.query.all()
    #     cate = BlogCategory.query.all()
    #     return render_template('blog/category.html', cate=cate, categ=categ, tags=tags)

@blog.route('/post/<int:post_id>')
def single(post_id):
    post = BlogPost.query.filter_by(id=post_id).first()
    posts = BlogPost.query.all()
    trend = BlogPost.query.order_by(func.random()).limit(4).all()
    tags = Tag.query.all()
    comment = BlogComment.query.filter_by(blog_id=post.id).all()
    replay = {}
    for c in comment:
        replay[c.id] = BlogReply.query.filter_by(comment_id=c.id).all()
    catt = BlogCategory.query.order_by(func.random()).limit(4).all()
    cate = BlogCategory.query.all()
    return render_template('blog/single.html',  replay=replay, comment=comment,posts=posts,post=post, trend=trend, tags=tags, catt=catt, cate=cate, date=timer())

@blog.route('/create')
def create_blog():
    if session.get('logged_in'):
        category = BlogCategory.query.all()
        tag = Tag.query.all()
        music = Song.query.filter_by(user_id=me().id).count()
        video = Tape.query.filter_by(user_id=me().id).count()
        pic = Picture.query.filter_by(user_id=me().id).count()
        total = int(total_p(user_id=me().id) + total_s(user_id=me().id) + total_v(user_id=me().id))
        song = Song.query.filter_by(user_id=me().id).first()
        return render_template('blog/create.html',  category=category, tag=tag, user=me(), proj=total)
    else:
        return redirect(url_for('blog.home'))


@blog.route('/back')
def back():
    if 'backbtn' in request.args:
        return redirect(request.args.get('backbtn'))
    else:
        return redirect(url_for('blog.home'))


@blog.route('add_category', methods=['POST'])
def add_cat():
    cat = request.form.get('cat')
    icon = request.files.get('imgscate')
    nn = secure_filename(icon.filename)
    nna = str(uuid.uuid4())
    nnex = os.path.splitext(nn)[1]
    nname = nna + nnex
    path = os.path.join(current_app.config['BLOG_FOLDER_IMAGE'], nname)
    icon.save(path)
    sub = BlogCategory(text=cat, icon = nname)
    db.session.add(sub)
    db.session.commit()
    return redirect(url_for('blog.back', backbtn=request.referrer))

@blog.route('add_tag', methods=['POST'])
def add_tag():
    tags = request.form['tagz']
    sub = Tag(text=tags)
    db.session.add(sub)
    db.session.commit()
    return redirect(url_for('blog.back', backbtn=request.referrer))


@blog.route('/add_post', methods=['POST'])
def create():
    if session.get('logged_in'):
        user=User.query.get(current_user.id)
        title = request.form.get('title')
        summary = request.form.get('summary')
        body = request.form.get('body')
        category = request.form.get('category')
        tag = request.form.get('tag')
        thumb = request.files.get('media')
        media = request.files.getlist('media')
        ftype = thumb.content_type
        allof = {}
        tagg = {}
        if 'image' in ftype:
            tn = secure_filename(thumb.filename)
            rn = str(uuid.uuid4())
            rx = os.path.splitext(tn)[1]
            allof = rn + rx
            pathz = os.path.join(current_app.config['BLOG_FOLDER_IMAGE'], allof)
            thumb.save(pathz)
        if tag:
            for tagz in tag:
                tagg = tagz
        post = BlogPost(user_id=user.id, title=title, summary=summary, body=body, category=category, tag=tagg, thumb = allof)
        db.session.add(post)
        db.session.commit()
        for file in media:
            filetype = file.content_type
            if filetype in ['image/jpg', 'image/png', 'image/jpeg']:
                image_name = secure_filename(file.filename)
                new_name = str(uuid.uuid4())
                file_ext = os.path.splitext(image_name)[1]
                allof = new_name + file_ext
                path = os.path.join(current_app.config['BLOG_FOLDER_IMAGE'], allof)
                file.save(path)
                submit = BlogImage(blog_id=post.id, image=allof)
                db.session.add(submit)
            if filetype in ['video/mp4']:
                video_name = secure_filename(file.filename)
                video_new = str(uuid.uuid4())
                video_ext = os.path.splitext(video_name)[1]
                video_file = video_new + video_ext
                paths = os.path.join(current_app.config['BLOG_FOLDER_VIDEO'],video_file)
                file.save(paths)
                sub = BlogVideo(blog_id=post.id, video=video_file)
                db.session.add(sub)
        try:
            db.session.flush()
            db.session.commit()
            flash('Successful', 'success')
            return redirect(url_for('blog.back', backtn=request.referrer))
        except Exception as e:
            db.session.rollback()
            flash(f'Error occurred!{str(e)}', 'danger')
            return redirect(url_for('blog.back', backtn=request.referrer))

        #return redirect(url_for('profile', username=user.username))
    else:
        return redirect(url_for('login'))

@blog.route('/add-comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    names = request.form.get('name')
    emails = request.form.get('email')
    messages = request.form.get('message')
    if current_user.is_authenticated:
        user = me()
        nall = user.lastname + user.firstname
        sub = BlogComment(user_id=me().id, blog_id=post_id, name=nall, message=messages, email = user.email)
        db.session.add(sub)
        db.session.commit()
        return redirect(url_for('blog.back', backbtn = request.referrer))
    else:
        submit = BlogComment(name=names, email=emails, message=messages, blog_id=post_id)
        db.session.add(submit)
        db.session.commit()
        return redirect(url_for('blog.back', backbtn=request.referrer))

@blog.route('/add-reply/<int:post_id>/<int:comment_id>', methods=['POST'])
def add_reply(post_id, comment_id):
    if session.get('logged_in'):
        messages = request.form.get('message')
        user = me()
        nall = user.lastname + user.firstname
        sub = BlogReply(user_id=me().id, comment_id=comment_id, blog_id=post_id, name=nall, message=messages,
                        email=user.email)
        db.session.add(sub)
        db.session.commit()
        return redirect(url_for('blog.back', backbtn=request.referrer))
    else:
        flash(f'You are not logged in','cant')
        return redirect(url_for('blog.back', backbtn=request.referrer))


@blog.route('/chat/<username>')
def chat(username):
    if session.get('logged_in'):
        other = User.query.filter_by(username=username).first()
        user = User.query.get(current_user.id)
        roomId = {}

        if user.id != other.id:
            roomId = roomid(user1=user, user2=other)
        else:
            roomId = user
        return render_template('blog/chat.html', user=user, other=other, roomId=roomId)
    else:
        return redirect(url_for('login'))

# user_session = {}
# user_rooms = {}
#
# @socketio.on('connect')
# def connect():
#     if current_user.is_authenticated:
#         user_session[current_user.id] = request.sid
#         print(f'User connected')
#
# @socketio.on('disconnect')
# def disconnect():
#     user_session.pop(current_user.id, None)
#     print(f'User disconnected')
#
#
# @socketio.on('message')
# def handle_send_message(data):
#     receiver_id = data['receiver_id']
#     message = data['message']
#     room = data['room']
#     sender_id = data['sender_id']
#     emit('message', {'message': message, 'receiver_id': receiver_id, 'room': room, 'sender_id': sender_id}, to=room)
#
#     print(f'{message}', room, receiver_id)
#
#
# @socketio.on('join')
# def on_join(data):
#     username = data['username']
#     room = data['room']
#     join_room(room)
#     send(username + ' has entered the room.', room=room)
#     print(f'{username} has entered the room', room)
#
#
# @socketio.on('leave')
# def on_leave(data):
#     username = data['username']
#     room = data['room']
#     leave_room(room)
#     send(username + ' has left the room.', room=room)

