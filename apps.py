from flask import Flask, make_response, request, current_app,render_template, redirect, session, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, login_required, current_user
from sqlalchemy.orm import configure_mappers
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from sqlalchemy.exc import IntegrityError
from sqlalchemy import asc, or_
import os
from celery import Celery
from exten.model import *
import uuid
from flask_mail import Mail, Message
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from config import *
from plugin import *
from pack.twilio import tw
from pack.blog import blog
from pack.creator import bp
from pack.selfside import slef
from extension import *
from funcs import online, checkliker, search_hist, have_follow, last_seen, onlinetag, mutual_friends_list, \
    mutual_friends_count, is_friend, is_following, accept_follow, need_to_accept, me, resize_image, recent_message, \
    timer, content_date, mutual_friends_counts, mutual_friends_lists, roomkey, roomid, recent_messages

app = Flask(__name__)
apps = Celery(app.name, broker='redis://localhost:6379/0')
app.config.from_object(Config)
app.register_blueprint(bp, url_prefix='/creator')
app.register_blueprint(blog, url_prefix='/blog')
app.register_blueprint(tw, url_prefix='/connect')
app.register_blueprint(slef, url_prefix='/self')

app.permanent_session_lifetime = timedelta(minutes=25)
db.init_app(app)
mail.init_app(app)
socketio.init_app(app)
s = URLSafeTimedSerializer('Thisissecret')
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt.init_app(app)
limiter.init_app(app)




with app.app_context():
     configure_mappers()
     db.create_all()

####### End for database

os.makedirs(app.config['UPLOAD_FOLDER_IMAGE'], exist_ok=True)





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
    return render_template('dist/authentication/general/error-404.html', home=home), 404


@app.before_request
def before_request():
    session.permanent = True
##### end for functions ##



@app.route('/')
def home():
    if session.get('logged_in'):
        user=User.query.get(current_user.id)
        if user.roles == 'Artist':
            return redirect(url_for('main.homee'))
        else:
            return redirect(url_for('news', username=user.username))
    else:
        return render_template('user/login.html')

@app.route('/reset-password', methods=['POST', 'GET'])
@limiter.limit("3 per 30 days")
def reset_pass():
    if request.method == 'POST':
        email = request.form.get('email')
        exists = User.query.filter_by(email=email).first()
        if not exists:
            flash(f'Your email {email} does not exist in our record', 'cant')
            return redirect(url_for('back', backbtn=request.referrer))
        else:
            token = s.dumps(email, salt='reset-pass')
            cmsg = Message('Confirm Email', sender=app.config['SENDER'], recipients=[exists.email])
            veri_code = url_for('confirm_emails', token=token, _external=True)
            cmsg.html = render_template('email_verify.html', veri_code=veri_code)
            mail.send(cmsg)
            flash('A verification link have been sent to your email address', 'success')
            return redirect(url_for('back', backbtn=request.referrer))
    return render_template('reset_pass.html')

@app.route('/change-password/<username>', methods=['POST'])
def reset2(username):
    newpass = request.form.get('newpass')
    repeat = request.form.get('repeat')
    if newpass != repeat:
        flash('Password do not match', 'cant')
        return redirect(url_for('back', backbtn=request.referrer))
    else:
        hash_password = bcrypt.generate_password_hash(repeat).decode('utf-8')
        user = User.query.filter_by(username=username).first()
        if user:
            user.password = hash_password
            db.session.commit()
            flash('Password reset successful', 'success')
            return redirect(url_for('login'))
        else:
            flash('No profile Found', 'cant')
            return redirect(url_for('back', backbtn=request.referrer))



@app.route('/reset/<username>')
def reset1(username):
    other = User.query.filter_by(username=username).first()
    return render_template('reset2.html', other=other)

@app.route('/confirm_emails/<token>')
def confirm_emails(token):
    try:
        email = s.loads(token, salt='reset-pass', max_age=3600)
    except SignatureExpired:
        return '<h1>The token is expired</h1>'
    user = User.query.filter_by(email=email).first_or_404()

    flash('Your email has been verified!', 'success')
    return redirect(url_for('reset1', username=user.username))

@app.route('/newsfeed/<username>', methods=['GET'])
def news(username):
    if session.get('logged_in'):
        last_seen()
        user = User.query.get(current_user.id)
        current_user_id = current_user.id
        other = User.query.filter_by(username=username).first()
        restrict()
        one = Post.query.order_by(func.random()).first()
        oneuser = User.query.filter_by(id=one.user.id).first()
        acc = accept_follow(self=user, user_id=oneuser)
        searcho = search_hist(user_id=current_user.id)
        posts = Post.query.filter(Post.privacy =='Public').order_by(func.random()).all()
        dnd = Post.query.filter_by(user_id=user.id).order_by(func.random()).first()
        sugg = User.query.filter(User.id != current_user.id, ~User.followers.any(User.id == current_user.id)).order_by(func.random()).all()
        is_friend = User.query.filter(User.id != current_user.id, User.followers.any(User.id == current_user.id)).order_by(
            func.random()).all()

        query = db.session.query(Messages.sender_id, func.max(Messages.id).label('max_id')).filter(
            Messages.recipient_id == current_user_id).group_by(Messages.sender_id).subquery()
        recent_mess = Messages.query.join(query, query.c.max_id == Messages.id).limit(10).all()
        tag = {}
        notice = notify(user=user)
        notice_sender = {}
        for noti in notice:
            notice_sender[noti.id] = User.query.filter_by(id=noti.user_id).first()

        for recent in recent_mess:
            uuu = User.query.filter_by(username=recent.sender.username).first()
            hot = onlinetag(user_id=uuu)
            tag[recent.sender] = hot
        story = Story.query.order_by(asc(Story.user_id)).all()
        comm = Comment.query.filter_by(post_id=dnd.id).all()
        com = Comment.query.filter_by(post_id=one.id).all()
        exist = checkliker(post_id=dnd.id, user_id=user.id)
        ex = checkliker(post_id=one.id, user_id=user.id)
        likes = Like.query.filter_by(post_id=dnd.id, user_id=user.id).first()
        likess = Like.query.filter_by(post_id=one.id, user_id=user.id).first()
        like = Like.query.filter_by(post_id=dnd.id).all()
        liken = Like.query.filter_by(post_id=one.id).all()

        lc = len(like)
        lc1 = len(liken)
        comc =len(com)
        coms =len(comm)
        comment = {}
        liker = {}
        exs = {}
        lk = {}
        friend_of = {}
        is_online = {}
        foll = {}
        query = request.args.get('search', None)
        search = User.query.filter(User.username.ilike(f'%{query}%')).all()
        post_search = Post.query.filter(Post.content.ilike(f'%{query}%')).all()
        search_friends = {}
        for dats in search:
            search_friends[dats.id]= have_follow(self=user, user_id=dats)
        for they in is_friend:
            i_am = have_follow(self=user, user_id=they)
            friend_of[they.id] = i_am
            is_online[they.id] = onlinetag(user_id=they)
        for post in posts:
            l = Like.query.filter_by(post_id=post.id).order_by(asc(Like.when)).all()
            lj = Like.query.filter_by(post_id=post.id, user_id=user.id).first()
            c = Comment.query.filter_by(post_id=post.id).order_by(asc(Comment.when)).all()
            exists = checkliker(post_id=post.id, user_id=user.id)
            postusers = User.query.filter_by(id=post.user.id).first()
            foll[post.id] = accept_follow(self=user, user_id=postusers)

            lk[post.id] = lj
            exs[post.id] = exists
            comment[post.id] = c
            liker[post.id] = len(l)

        return render_template('main/feed.html', roomid=get_roomkey(user_id=user, other_id=other), count=notify_count(user=user),notice=notice, sn =notice_sender,recents=recent_mess, ss=search_friends,postss=post_search,search=searcho,tag=tag,is_online=is_online,each=friend_of,is_friend=is_friend,sugg=sugg,liken=liken, story=story,likess=likess, lc1=lc1,coms=coms,lk=lk,ex=ex,exs=exs,liker=liker,exist=exist,likes=likes ,lc=lc,posts=posts,comc=comc,comment=comment, one=one, dnd=dnd, com=com, comm=comm, user=user, other=other, acc = acc, foll=foll)
    else:
        return redirect(url_for('login'))


@app.route('/delete/<int:post_id>', methods=['POST'])
def delete(post_id):
    if session.get('logged_in'):
        histor= SearchHistory.query.filter_by(id=post_id).first()
        db.session.delete(histor)
        db.session.commit()
        return redirect(url_for('back', backbtn=request.referrer))
    else:
        return redirect(url_for('login'))

@app.route('/delete_r/<int:user_id>', methods=['POST'])
def delete_r(user_id):
    if session.get('logged_in'):
        SearchHistory.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return redirect(url_for('back', backbtn=request.referrer))
    else:
        return redirect(url_for('login'))
@app.route('/result/<username>', methods=['GET'])
def search_r(username):
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        query = request.args.get('search', '')
        search = User.query.filter(User.username.ilike(f'%{query}%')).all()
        for_post = Post.query.filter(Post.content.ilike(f'%{query}%')).all()
        search_friends ={}
        for dats in search:
            search_friends[dats.id]= have_follow(self=user, user_id=dats)

        return render_template('main/searchresult.html', user=user, other=user, dats=dats, search=search)
    else:
        return redirect(url_for('login'))
@app.route('/search', methods=['GET'])
def for_search():
    if session.get('logged_in'):
        query = request.args.get('search', '')

        for_user = User.query.filter(
            or_(
                User.username.ilike(f'%{query}%'),
                User.firstname.ilike(f'%{query}%'),
                User.lastname.ilike(f'%{query}%')
            )
        ).limit(2).all()
        for_post = Post.query.filter(Post.content.ilike(f'%{query}%')).all()
        user= User.query.get(current_user.id)
        exist = SearchHistory.query.filter_by(text=query).first()
        if query == '':
            foll = {}
            folls = {}
            isf = {}
            videos = {}
            imgs = {}
            lk = {}
            exs = {}
            comment = {}
            liker = {}
            imgss = {}
            videoss = {}
            mc = {}
            m = {}

            for post in for_post:
                m = mutual_friends_lists(me=current_user.id, other=post.user.id)
                l = Like.query.filter_by(post_id=post.id).order_by(asc(Like.when)).all()
                lj = Like.query.filter_by(post_id=post.id, user_id=user.id).first()
                c = Comment.query.filter_by(post_id=post.id).order_by(asc(Comment.when)).all()
                exists = checkliker(post_id=post.id, user_id=user.id)

                mc[post.id] = mutual_friends_counts(me=user.id, other=post.user.id) - 1

                lk[post.id] = lj
                folls[post.id] = have_follow(self=user, user_id=post.user)
                exs[post.id] = exists
                comment[post.id] = c
                liker[post.id] = len(l)
                imgss[post.id] = (db.session.query(func.count(Image.id)).join(Post, Post.id == Image.post_id).join(User,
                                                                                                                   User.id == Post.user_id).filter(
                    User.id == post.user.id).scalar())

                videoss[post.id] = (
                    db.session.query(func.count(Video.id)).join(Post, Post.id == Video.post_id).join(User,
                                                                                                     User.id == Post.user_id).filter(
                        User.id == post.user.id).scalar())

            for users in for_user:
                foll[users.id] = have_follow(self=user, user_id=users)
                # isf[users.id] = need_to_accept(self=user, user_id=users)
                isf[users.id] = is_friend(self=user.id, user_id=users.id)
                imgs[users.id] = (db.session.query(func.count(Image.id)).join(Post, Post.id == Image.post_id).join(User,
                                                                                                                   User.id == Post.user_id).filter(
                    User.id == users.id).scalar())

                videos[users.id] = (
                    db.session.query(func.count(Video.id)).join(Post, Post.id == Video.post_id).join(User,
                                                                                                     User.id == Post.user_id).filter(
                        User.id == users.id).scalar())

            return render_template('main/searchresult.html', m=m, mc=mc, comment=comment, folls=folls, vid=videoss,
                                   img=imgss, lk=lk, exs=exs, liker=liker, posti=videos, imgs=imgs, isf=isf, foll=foll,
                                   q=query, posts=for_post, search=search_hist(user_id=current_user.id),
                                   searchi=for_user, user=user, other=user, roomid=get_roomkey(user_id=user, other_id=user))
        elif exist:
            foll = {}
            folls = {}
            isf = {}
            videos = {}
            imgs = {}
            lk = {}
            exs = {}
            comment = {}
            liker = {}
            imgss = {}
            videoss = {}
            mc = {}
            m = {}

            for post in for_post:
                m = mutual_friends_lists(me=current_user.id, other=post.user.id)
                l = Like.query.filter_by(post_id=post.id).order_by(asc(Like.when)).all()
                lj = Like.query.filter_by(post_id=post.id, user_id=user.id).first()
                c = Comment.query.filter_by(post_id=post.id).order_by(asc(Comment.when)).all()
                exists = checkliker(post_id=post.id, user_id=user.id)

                mc[post.id] = mutual_friends_counts(me=user.id, other=post.user.id) - 1

                lk[post.id] = lj
                folls[post.id] = have_follow(self=user, user_id=post.user)
                exs[post.id] = exists
                comment[post.id] = c
                liker[post.id] = len(l)
                imgss[post.id] = (db.session.query(func.count(Image.id)).join(Post, Post.id == Image.post_id).join(User,
                                                                                                                   User.id == Post.user_id).filter(
                    User.id == post.user.id).scalar())

                videoss[post.id] = (
                    db.session.query(func.count(Video.id)).join(Post, Post.id == Video.post_id).join(User,
                                                                                                     User.id == Post.user_id).filter(
                        User.id == post.user.id).scalar())

            for users in for_user:
                foll[users.id] = have_follow(self=user, user_id=users)
                # isf[users.id] = need_to_accept(self=user, user_id=users)
                isf[users.id] = is_friend(self=user.id, user_id=users.id)
                imgs[users.id] = (db.session.query(func.count(Image.id)).join(Post, Post.id == Image.post_id).join(User,
                                                                                                                   User.id == Post.user_id).filter(
                    User.id == users.id).scalar())

                videos[users.id] = (
                    db.session.query(func.count(Video.id)).join(Post, Post.id == Video.post_id).join(User,
                                                                                                     User.id == Post.user_id).filter(
                        User.id == users.id).scalar())

            return render_template('main/searchresult.html', m=m, mc=mc, comment=comment, folls=folls, vid=videoss,
                                   img=imgss, lk=lk, exs=exs, liker=liker, posti=videos, imgs=imgs, isf=isf, foll=foll,
                                   q=query, posts=for_post, search=search_hist(user_id=current_user.id),
                                   searchi=for_user, user=user, other=user, roomid=get_roomkey(user_id=user, other_id=user))
        else:
            submit = SearchHistory(user_id=user.id, text=query)

            db.session.add(submit)
            db.session.commit()
            foll = {}
            folls = {}
            isf = {}
            videos = {}
            imgs = {}
            lk = {}
            exs = {}
            comment = {}
            liker = {}
            imgss = {}
            videoss = {}
            mc = {}
            m = {}

            for post in for_post:
                m = mutual_friends_lists(me=current_user.id, other=post.user.id)
                l = Like.query.filter_by(post_id=post.id).order_by(asc(Like.when)).all()
                lj = Like.query.filter_by(post_id=post.id, user_id=user.id).first()
                c = Comment.query.filter_by(post_id=post.id).order_by(asc(Comment.when)).all()
                exists = checkliker(post_id=post.id, user_id=user.id)

                mc[post.id] = mutual_friends_counts(me=user.id, other=post.user.id) - 1

                lk[post.id] = lj
                folls[post.id] = have_follow(self=user, user_id=post.user)
                exs[post.id] = exists
                comment[post.id] = c
                liker[post.id] = len(l)
                imgss[post.id] = (db.session.query(func.count(Image.id)).join(Post, Post.id == Image.post_id).join(User,
                                                                                                                   User.id == Post.user_id).filter(
                    User.id == post.user.id).scalar())

                videoss[post.id] = (
                    db.session.query(func.count(Video.id)).join(Post, Post.id == Video.post_id).join(User,
                                                                                                     User.id == Post.user_id).filter(
                        User.id == post.user.id).scalar())

            for users in for_user:
                foll[users.id] = have_follow(self=user, user_id=users)
                # isf[users.id] = need_to_accept(self=user, user_id=users)
                isf[users.id] = is_friend(self=user.id, user_id=users.id)
                imgs[users.id] = (db.session.query(func.count(Image.id)).join(Post, Post.id == Image.post_id).join(User,
                                                                                                                   User.id == Post.user_id).filter(
                    User.id == users.id).scalar())

                videos[users.id] = (
                    db.session.query(func.count(Video.id)).join(Post, Post.id == Video.post_id).join(User,
                                                                                                     User.id == Post.user_id).filter(
                        User.id == users.id).scalar())

            return render_template('main/searchresult.html', m=m, mc=mc, comment=comment, folls=folls, vid=videoss,
                                   img=imgss, lk=lk, exs=exs, liker=liker, posti=videos, imgs=imgs, isf=isf, foll=foll,
                                   q=query, posts=for_post, search=search_hist(user_id=current_user.id),
                                   searchi=for_user, user=user, other=user, roomid=get_roomkey(user_id=user, other_id=user))
    else:
        return redirect(url_for('login'))

@app.route('/remove_like/<int:post_id>/<int:user_id>', methods=['POST'])
def remove_like(post_id, user_id):
    if session.get('logged_in'):
        like = checkliker(post_id, user_id)
        if like:
            likes =Like.query.filter_by(user_id=user_id, post_id=post_id).first()
            db.session.delete(likes)
            db.session.commit()
            return redirect(url_for('back', backbtn=request.referrer))
        else:
            pass
    else:
        return redirect(url_for('login'))

@app.route('/like/<int:post_id>/<reaction>', methods=['POST'])
def add_like(post_id, reaction):
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        checkex =checkliker(post_id=post_id, user_id=user.id)
        if checkex:
            #likes = Like.query.filter_by(user_id=user.id, post_id=post_id).first()
            checkex.reaction = reaction
            db.session.commit()
            flash('Your reaction has been updated.', 'success')

        else:
            liker = Like(post_id=post_id, reaction=reaction, user_id=user.id)
            db.session.add(liker)
            db.session.commit()
            flash('Your reaction has been updated.', 'success')
        return redirect(url_for('back', backbtn=request.referrer))
    else:
        return redirect(url_for('login'))



@app.route('/back')
def back():
    if 'backbtn' in request.args:
        return redirect(request.args.get('backbtn'))
    else:
        return redirect(url_for('home'))

@app.route('/posts/<int:post_id>')
def posts_s(post_id):
    if session.get('logged_in'):
        last_seen()
        user = User.query.get(current_user.id)
        posts = Post.query.filter((Post.id == post_id)).all()
        pp = Post.query.filter_by(id=post_id).first()
        if_online = content_date(when_made=pp)
        lk = Like.query.filter_by(post_id=pp.id, user_id=user.id).first()
        exs = checkliker(post_id=pp.id, user_id=user.id)
        comment = Comment.query.filter_by(post_id=pp.id).order_by(asc(Comment.when)).all()
        liker = Like.query.filter_by(post_id=pp.id).order_by(asc(Like.when)).count()

        return render_template('main/postprev.html',comment=comment, liker=liker,lk=lk, exs=exs,roomid=get_roomkey(user_id=user, other_id=user),search=search_hist(user_id=current_user.id),other=user,backtn=request.referrer,post=posts, pp=pp, if_online=if_online, user=user)
    else:
        return redirect(url_for('login'))

@app.route('/add_story/<int:user_id>', methods=['POST'])
def add_story(user_id):
    if session.get('logged_in'):
        text = request.form.get('text', ' ')
        media = request.files.getlist('media')
        sub = Story(user_id=user_id, text=text)
        db.session.add(sub)
        db.session.commit()
        for file in media:
            filetype = file.content_type
            if filetype in ['image/jpg', 'image/png', 'image/jpeg']:
                image_name = secure_filename(file.filename)
                image_new = str(uuid.uuid4())
                image_exten = os.path.splitext(image_name)[1]
                image_new_name = image_new + image_exten
                path = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], image_new_name)
                file.save(path)
                submit = StoryImage( image=image_new_name, story_id=sub.id)
                db.session.add(submit)
            if filetype in ['video/mp4']:
                video_n = secure_filename(file.filename)
                video_new = str(uuid.uuid4())
                video_ext = os.path.splitext(video_n)[1]
                video_new_name = video_new + video_ext
                paths = os.path.join(app.config['UPLOAD_FOLDER_VIDEO'], video_new_name)
                file.save(paths)
                videos = StoryVideo(video=video_new_name, story_id=sub.id)
                db.session.add(videos)


        try:
            db.session.commit()
            flash('Done', 'success')
            return redirect(url_for('back', backtn=request.referrer))
        except Exception as e:
            db.session.rollback()
            db.session.commit()
            flash(f'Error occurred {(e)} ', 'danger')
            return redirect(url_for('back', backtn=request.referrer))

    else:
        return redirect(url_for('login'))


@app.route('/create', methods=['POST'])
def create():
    if session.get('logged_in'):
        user=User.query.get(current_user.id)
        content = request.form.get('content', ' ')
        feelings = request.form.get('feelings')
        media = request.files.getlist('media')
        privacy = request.form.get('privacy')
        post = Post( user_id=user.id,content=content, privacy=privacy,feelings=feelings)
        db.session.add(post)
        db.session.commit()
        for file in media:
            filetype = file.content_type
            if filetype in ['image/jpg', 'image/png', 'image/jpeg']:
                image_name = secure_filename(file.filename)
                new_name = str(uuid.uuid4())
                file_ext = os.path.splitext(image_name)[1]
                allof = new_name + file_ext
                #origin = os.path.join(app.config['UPLOAD_FOLDER_ORIGIN'], allof)
                path = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], allof)
                #resize_image(input_path=path, output_path=path, size=70)
                file.save(path)
                file_blob = path.encode('utf-8')
                submit = Image(post_id=post.id, file_info=allof, file_path=file_blob)
                db.session.add(submit)
            if filetype in ['video/mp4']:
                video_name = secure_filename(file.filename)
                video_new = str(uuid.uuid4())
                video_ext = os.path.splitext(video_name)[1]
                video_file = video_new + video_ext
                paths = os.path.join(app.config['UPLOAD_FOLDER_VIDEO'],video_file)
                file.save(paths)
                blob_vid = paths.encode('utf-8')
                sub = Video(post_id=post.id, file_path=blob_vid, file_info=video_file)
                db.session.add(sub)
        try:
            db.session.commit()
            flash('Successful', 'success')
            return redirect(url_for('back', backtn=request.referrer))
        except Exception as e:
            db.session.rollback()
            flash(f'Error occurred!{str(e)}', 'danger')
            return redirect(url_for('home'))

        #return redirect(url_for('profile', username=user.username))
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

                flash('Password did not match', 'error')
                return redirect(url_for('back', backbtn=request.referrer))

            else:
                hash_password = bcrypt.generate_password_hash(repeat).decode('utf-8')
                user.password = hash_password
                db.session.commit()
                flash('Password changed successfully', 'success')

                return redirect(url_for('back', backbtn=request.referrer))
        else:
            flash('Incorrect password', 'error')
            return redirect(url_for('back', backbtn=request.referrer))
    else:
        return redirect(url_for('login'))

@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if session.get('logged_in'):
        user =User.query.get(current_user.id)
        post= Post.query.get(post_id)
        text = request.form.get('comment',' ')
        files = request.files.get('pictures')
        file_type = files.content_type
        if text:
            submit = Comment(post_id=post_id, content=text, user_id=user.id)
            db.session.add(submit)
            flash('Comment added', 'success')
        if files:
            if file_type in ['image/jpg', 'image/png', 'image/jpeg']:
                filename = secure_filename(files.filename)
                file_new = str(uuid.uuid4())
                file_ext = os.path.splitext(filename)
                file_name = file_new + file_ext
                paths = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], file_name)
                files.save(paths)
                new_file = Comment(post_id=post_id, image=file_name, user_id=user.id)
                db.session.add(new_file)
            if file_type in ['video/mp4']:
                filenames = secure_filename(files.filename)
                file_news = str(uuid.uuid4())
                file_exts = os.path.splitext(filenames)
                file_now = file_news + file_exts
                path = os.path.join(app.config['UPLOAD_FOLDER_VIDEO'], file_now)
                files.save(path)
                new_fil = Comment(post_id=post_id, video=file_now, user_id=user.id)
                db.session.add(new_fil)
        try:
            db.session.commit()

            return redirect(url_for('back', backbtn=request.referrer))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('back', backbtn=request.referrer))
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
        marital = request.form.get('marital', user.marital)
        Bio = request.form.get('Bio', user.Bio)

        if firstname:
            user.firstname = firstname
        if Bio:
            user.Bio =Bio
        if marital:
            user.marital = marital
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

        return redirect(url_for('back', backbtn=request.referrer))
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
        last_seen()
        roomkey(user1=user, user2=other)
        current_user_id = user.id
        own_profile = (current_user.is_authenticated and other.username == current_user.username)
        mess = Messages.query.filter((Messages.sender_id == user.id) & (Messages.recipient_id == other.id) | (Messages.sender_id == other.id) & (Messages.recipient_id == user.id)).order_by(Messages.timestamp.asc()).all()
        query = db.session.query(Messages.sender_id, func.max(Messages.id).label('max_id')).filter(Messages.recipient_id == current_user_id).group_by(Messages.sender_id).subquery()
        recent_mess = Messages.query.join(query, query.c.max_id == Messages.id).all()
        onlines = online(user_id=other)
        online_color = onlinetag(user_id=other)
        notice = notify(user=user)
        roomId = {}

        if user.id != other.id:
            roomId = roomid(user1=user, user2=other)
        else:
            roomId = user
        notice_sender = {}
        for noti in notice:
            notice_sender[noti.id] = User.query.filter_by(id=noti.user_id).first()
        tag = {}
        for recent in recent_mess:
            check = onlinetag(user_id=recent.sender)
            tag[recent.sender] = check
        return render_template('main/messages.html', roomid=roomId,notice=notice, sn=notice_sender,search = search_hist(user_id=user.id),on=onlines, tag=tag,tags=online_color,recents= recent_mess,own_profile=own_profile,mess=mess, other=other,username=user, user=user, count=notify_count(user=user))
    else:
        return redirect(url_for('login'))

#for the room

@app.route('/mess_uplaod/<username>', methods=['POST'])
def mess_upload(username):
    if session.get('logged_in'):
        other = User.query.filter_by(username=username).first()
        user = me()
        media = request.files.getlist('media')
        if not media:
            pass
        else:
            for files in media:
                filetype = files.content_type
                if filetype in ['image/jpg', 'image/png', 'image/jpeg']:
                    fn = secure_filename(files.filename)
                    nnam = str(uuid.uuid4())
                    nex = os.path.splitext(fn)[1]
                    allo = nnam + nex
                    pathi = os.path.join(current_app.config['UPLOAD_FOLDER_IMAGE'], allo)
                    files.save(pathi)
                    sub = Messages(sender_id=user.id, recipient_id=other.id, image = allo)
                    db.session.add(sub)
                if filetype in ['video/mp4']:
                    fnv = secure_filename(files.filename)
                    nvn = str(uuid.uuid4())
                    nvex = os.path.splitext(fnv)[1]
                    allof = nvn + nvex
                    ptha = os.path.join(current_app.config['UPLOAD_FOLDER_VIDEO'], allof)
                    files.save(ptha)
                    vsub = Messages(sender_id=user.id, recipient_id=other.id, video = allof)
                    db.session.add(vsub)
            try:
                db.session.commit()
                return redirect(url_for('back', backbtn = request.referrer))
            except Exception as e:
                db.session.rollback()
                return redirect(url_for('back', backbtn = request.referrer))
    else:
        return redirect(url_for('login'))





@app.route('/chat/<username>')
def chat(username):
    if session.get('logged_in'):
        last_seen()
        other=User.query.filter_by(username=username).first()
        user= User.query.get(current_user.id)
        if other != user:
            return redirect(url_for('profile', username=user.username))
        else:
            current_user_id = current_user.id
            mess = Messages.query.filter(
                (Messages.sender_id == user.id) & (Messages.recipient_id == other.id) | (
                            Messages.sender_id == other.id) & (
                        Messages.recipient_id == user.id)).order_by(asc(Messages.timestamp)).all()
            query = db.session.query(Messages.sender_id, func.max(Messages.id).label('max_id')).filter(
                Messages.recipient_id == current_user_id).group_by(Messages.sender_id).subquery()
            recent_mess = Messages.query.join(query, query.c.max_id == Messages.id).limit(10).all()
            tag = {}
            notice = notify(user=user)
            notice_sender = {}
            for noti in notice:
                notice_sender[noti.id] = User.query.filter_by(id=noti.user_id).first()

            for recent in recent_mess:
                uuu=User.query.filter_by(username=recent.sender.username).first()
                hot = onlinetag(user_id=uuu)
                tag[recent.sender] = hot
            return render_template('chats.html', notice=notice, roomid=get_roomkey(user_id=user, other_id=other),sn = notice_sender,search = search_hist(user_id=user.id), tag=tag,recents=recent_mess, user=user, mess=mess, other=other, count=notify_count(user=user))
    else:
        return redirect(url_for('login'))






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
            if not user:
                flash(f'No record with your email {email} found', 'danger')
                return redirect(url_for('login'))

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
                    cmsg = Message('Confirm Email', sender=app.config['SENDER'], recipients=[email])
                    veri_code = url_for('confirm_email', token=token, _external=True)
                    cmsg.html = render_template('email_verify.html', veri_code=veri_code)
                    mail.send(cmsg)
                    flash('please confirm your email first', 'error')
                    return redirect(url_for('login'))
            else:
                flash(f'Incorrect password', 'danger')
                return redirect(url_for('login'))

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
        role = request.form.get('role')
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
            new_user = User(country=country, roles=role,username=username,firstname=firstname, lastname=lastname, email=email,DOB=DOB, gender=gender,  password=hashed_password, profile_photo='default.png', cover_photo='default.jpeg')
            db.session.add(new_user)
            db.session.commit()

            token = s.dumps(email, salt='email-confirm')
            cmsg = Message('Confirm Email', sender=app.config['SENDER'], recipients=[email])
            veri_code = url_for('confirm_email', token=token, _external=True)
            cmsg.html = render_template('email_verify.html', veri_code=veri_code)
            mail.send(cmsg)
            flash('Registration successfully, verify your account by clicking the link sent to your email.', 'success')

            return redirect(url_for('step', username=username))

    return render_template('user/register.html')


@app.route('/step1/<username>')
def step(username):
    user = User.query.filter_by(username=username).first()
    post = Post(content= f'{user.username} recently registered', privacy= 'Only me', feelings= 'Happy', user_id= user.id)
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('login'))

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
        restrict()
        if other != current_user:
            return redirect(url_for('home'))
        else:
            notice = notify(user=user)
            notice_sender = {}
            for noti in notice:
                notice_sender[noti.id] = User.query.filter_by(id=noti.user_id).first()
            return render_template('main/setting.html', recents=recent_messages(),roomid=get_roomkey(user_id=user, other_id=other),notice=notice, sn=notice_sender,other=other, user=user, search = search_hist(user_id=current_user.id), count=notify_count(user=user))
    else:
        return redirect(url_for('login'))

@app.route('/edit_user/<username>')
def edit_user(username):
    if session.get('logged_in'):
        last_seen()
        other = User.query.filter_by(username=username).first()
        user = User.query.get(current_user.id)
        own_profile = (current_user.is_authenticated and other.username == current_user.username)
        status = (datetime.now() - other.last_seen).total_seconds() < 120
        stat = (datetime.now() - user.last_seen).total_seconds() < 120
        posts = Post.query.filter_by(user_id=other.id).all()
        images = []
        albums = []
        lk = {}
        exs = {}
        comment = {}
        liker = {}
        for post in posts:
            l = Like.query.filter_by(post_id=post.id).order_by(asc(Like.when)).all()
            lj = Like.query.filter_by(post_id=post.id, user_id=user.id).first()
            c = Comment.query.filter_by(post_id=post.id).order_by(asc(Comment.when)).all()
            exists = checkliker(post_id=post.id, user_id=user.id)

            lk[post.id] = lj
            exs[post.id] = exists
            comment[post.id] = c
            liker[post.id] = len(l)
            post_images = Image.query.filter_by(post_id=post.id).order_by(func.random()).all()
            images.extend(post_images)
            for image in post_images:
                post_album = Album.query.filter_by(image_id=image.id).all()
                albums.extend(post_album)
        # image=Image.query.filter_by(post_id=posts.id).all()
        # album=Album.query.filter_by(image_id=image.id).all()

        return render_template('user/users.html', comment=comment, lk=lk, liker=liker, exs=exs, other=other,
                               stat=stat, own_profile=own_profile, user=user, posts=posts, images=images, albums=albums,
                               status=status)
    else:
        return redirect(url_for('login'))



@app.route('/profile/<username>')
def profile(username):
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        if user.roles == 'Artist':
            return redirect(url_for('main.homee'))
        else:
            restrict()
            last_seen()
            user = User.query.get(current_user.id)
            other = User.query.filter_by(username=username).first()
            follows = is_following(self=user, user_id=other)
            have_follows = have_follow(self=user, user_id=other)
            need_to = need_to_accept(self=user, user_id=other)
            accept_foll = accept_follow(self=user, user_id=other)
            own_profile = (current_user.is_authenticated and other.username == current_user.username)
            status = online(user_id=other)
            stat = onlinetag(user_id=other)
            posts = Post.query.filter_by(user_id=other.id).all()
            follower = other.followers.all()
            follow_count = other.followers.count()
            search = search_hist(user_id=current_user.id)
            notice = notify(user=user)
            notice_sender = {}
            for noti in notice:
                notice_sender[noti.id] = User.query.filter_by(id=noti.user_id).first()
            images = []
            albums = []
            lk = {}
            exs = {}
            comment = {}
            liker = {}

            for post in posts:
                l = Like.query.filter_by(post_id=post.id).order_by(asc(Like.when)).all()
                lj = Like.query.filter_by(post_id=post.id, user_id=user.id).first()
                c = Comment.query.filter_by(post_id=post.id).order_by(asc(Comment.when)).all()
                exists = checkliker(post_id=post.id, user_id=user.id)
                lk[post.id] = lj
                exs[post.id] = exists
                comment[post.id] = c
                liker[post.id] = len(l)
                post_images = Image.query.filter_by(post_id=post.id).order_by(func.random()).all()
                images.extend(post_images)
                for image in post_images:
                    post_album = Album.query.filter_by(image_id=image.id).all()
                    albums.extend(post_album)
            # image=Image.query.filter_by(post_id=posts.id).all()
            # album=Album.query.filter_by(image_id=image.id).all()

            return render_template('main/timeline.html', recents=recent_messages() ,backtn=request.referrer, notice=notice, sn=notice_sender,
                                   search=search, follower=follower, follow_count=follow_count, need=need_to,
                                   acc=accept_foll, have_follows=have_follows, follows=follows, comment=comment, lk=lk,
                                   liker=liker, exs=exs, other=other, stat=stat, own_profile=own_profile, user=user,
                                   posts=posts, images=images, albums=albums, status=status, roomid=get_roomkey(user_id=user, other_id=other), count=notify_count(user=user))
    else:
        return redirect(url_for('login'))



@app.route('/upload_c', methods=['POST'])
def upload_c():
    if session.get('logged_in'):
        to_where = request.form.get('sele')
        selected = request.form.get('Radiosim')
        pics = request.files.get('picts')
        user = User.query.get(current_user.id)
        if selected:
            if to_where == 'cover':
                user.cover_photo = selected
                db.session.commit()
                flash('cover photo updated', 'success')
                return redirect(url_for('back', backbtn=request.referrer))
            elif to_where == 'profile':
                user.profile_photo = selected
                db.session.commit()
                flash('Profile updated', 'success')
                return redirect(url_for('back', backbtn=request.referrer))
            else:
                user.cover_photo = selected
                user.profile_photo = selected
                db.session.commit()
                flash('Profile updated', 'success')
                return redirect(url_for('back', backbtn=request.referrer))
        if pics:
            file_name = secure_filename(pics.filename)
            new_init = str(uuid.uuid4())
            new_ex = os.path.splitext(file_name)[1]
            file_now = new_init + new_ex
            path = os.path.join(app.config['UPLOAD_FOLDER_IMAGE'], file_now)
            pics.save(path)
            if to_where == 'cover':
                user.cover_photo = file_now
                db.session.commit()
                flash('Profile updated', 'success')
                return redirect(url_for('back', backbtn=request.referrer))
            elif to_where == 'profile':
                user.profile_photo = file_now
                db.session.commit()
                flash('Profile updated', 'success')
                return redirect(url_for('back', backbtn=request.referrer))
            else:
                user.cover_photo = file_now
                user.profile_photo = file_now
                db.session.commit()
                flash('Profile and Cover updated', 'success')
                return redirect(url_for('back', backbtn=request.referrer))
        else:
            flash('No file selected! ', 'danger')
            return redirect(url_for('back', backbtn=request.referrer))

            # try:
            #     hh=''
            # except Exception as e:
            #     db.session.rollback()
            #     flash(f'Error occured {(e)}', 'danger')
            #     return redirect(url_for('profile', username=user.username))

        return redirect(url_for('back', backbtn=request.referrer))
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
                return redirect(url_for('back', backtn=request.referrer))
            else:
                flash('Something went wrong!', 'error')
                return redirect(url_for('back', backtn=request.referrer))

        else:
            flash('Something went wrong!', 'error')
            return redirect(url_for('back', backtn=request.referrer))
    else:
        return redirect(url_for('login'))


def gender(username):
    user = User.query.filter_by(username=username).first()
    return 'his' if user.gender == 'Male' else 'her'
@app.route('/profile/@<username>')
def spec(username):
    if session.get('logged_in'):
        return redirect(url_for('profile', username=username))
    else:
        return redirect(url_for('login'))
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


@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow(user_id):
    if session.get('logged_in'):

        user = User.query.get_or_404(user_id)
        user1 = User.query.get(current_user.id)
        if user == current_user:
            flash('You cannot follow yourself!', 'cant')
            return redirect(url_for('back', backbtn=request.referrer))
        if is_following(self=current_user, user_id=user):
            flash('You are already following', 'cant')
            return redirect(url_for('back', backbtn=request.referrer))
        else:
            current_user.follow(user)
            db.session.commit()
            save_notification(user1=user1, user2=user, message=f'{user1.lastname} {user1.firstname} started following you!')
            return redirect(url_for('back', backbtn=request.referrer))


    else:
        return redirect(url_for('login'))

@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow(user_id):
    if session.get('logged_in'):
        user = User.query.get_or_404(user_id)
        if user == current_user:
            flash('You cannot follow yourself!', 'cant')
            return redirect(url_for('back', backbtn=request.referrer))
        if not is_following(self=current_user, user_id=user):
            flash(f'you are not following {user.username}', 'cant')
            return redirect(url_for('back', backbtn=request.referrer))
        else:
            current_user.unfollow(user)
            db.session.commit()
            flash('You have stopped following {}.'.format(user.username), 'success')
            return redirect(url_for('back', backbtn=request.referrer))


    else:
        return redirect(url_for('login'))

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

@app.route('/mark/<int:post_id>')
def mark_notify(post_id):
    if session.get('logged_in'):
        mark_read(post_id=post_id)
        notice = Notification.query.filter_by(id=post_id).first()
        user = User.query.filter_by(id=notice.user_id).first()
        return redirect(url_for('profile', username=user.username))
    else:
        return redirect(url_for('login'))


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
@app.route('/download/song/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    if session.get('logged_in'):
        user=me()
        if user.roles == 'Artist':
            directory = current_app.config['UPLOAD_FOLDER_AUDIO']
            return send_from_directory(directory,filename, as_attachment=True)
        else:
            return redirect(url_for('home'))

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

###Socket Io section #####

user_session = {}
user_rooms = {}


@socketio.on('connect')
def connect():
    if current_user.is_authenticated:
        user_session[current_user.id] = request.sid
        print(f'User connected')

@socketio.on('disconnect')
def disconnect():
    user_session.pop(current_user.id, None)
    user = User.query.get(current_user.id)
    user_key.pop(user.key, None)
    print(f'User disconnected')

@socketio.on('mmessage')
def handle_user_message(data):
    message = data['message']
    room = data['room']
    recipient_id = data['recipient_id']
    sender_id = data['sender_id']
    recipient = User.query.get(recipient_id)
    sender = User.query.get(sender_id)
    if message == '':
        pass
    elif message.isspace():
        pass
    else:
        submit = Messages(sender_id=sender.id, recipient_id=recipient.id, body=message)
        db.session.add(submit)
        db.session.commit()
        emit('mmessage', {'message': message, 'room': room, 'recipient_id': recipient_id, 'sender_id': sender_id},
             to=room)
        print(f'{message}', room, recipient.username)
    # emit('mmessage', {'message': message, 'room': room, 'recipient_id': recipient_id, 'sender_id': sender_id}, to=room)
    # print(f'{message}', room, recipient_id)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', room=room)
    print(f'{username} has entered the room', room)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', room=room)

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


@socketio.on('show_media')
def show_media(data):
    recipient_id = data['recipient_id']
    other = User.query.get(recipient_id)
    sender_id = data['sender_id']
    room = data['room']
    user = User.query.get(sender_id)
    mess = Messages.query.filter(
        ((Messages.sender_id == user.id) & (Messages.recipient_id == other.id)) |
        ((Messages.sender_id == other.id) & (Messages.recipient_id == user.id))
    ).order_by(Messages.timestamp.desc()).first()
    if mess.image:
        emit('show_media', {'image': mess.image, 'recipient_id': recipient_id, 'sender_id': sender_id}, to=room)
    elif mess.video:
        emit('show_media', {'video': mess.image, 'recipient_id': recipient_id, 'sender_id': sender_id}, to=room)
    else:
        emit('show_media', {'mgs': 'Error Occured', 'recipient_id': recipient_id, 'sender_id': sender_id}, to=room)

user_key = {}

@socketio.on('notification')
def handle_notification():
    user = User.query.get(current_user.id)

    # Check if user is connected before querying for notifications
    room = get_recipient_sid(user_id=user.id)
    if not room or room not in user_session:
        return  # User is not online, no need to query for notifications

    # Get recent notifications (modify recent_notify if needed)
    notifications = recent_notify(user=user)

    if notifications:
        # Extract relevant information from notifications for message
        message_data = []
        for notification in notifications:
            # Add relevant data from notification object
            message_data.append({
                'message': notification.content,  # or other relevant fields
                'sender_id': notification.user2,  # sender information (optional)
                'notification_id': notification.id  # for further actions (optional)
            })
        emit('notification', {'messages': message_data}, room=room)
        print(f'{message_data}')


@socketio.on('call_not')
def oncall(data):
    receiver = data['receiver']
    caller = data['caller']
    recipient = User.query.get(receiver)
    print(recipient.username)

    # Ensure recipient exists
    if recipient:
        recipient_sid = get_recipient_sid(receiver)


        callerInfo = User.query.get(caller)

        # Check if the caller information is available
        if callerInfo:
            # Emit to the recipient's room
            emit('call_not', {'caller': callerInfo.username}, room=recipient_sid)
            emit('ring_tone', room=recipient_sid)
        else:
            print(f'Caller Info error')
    else:
        print(f'Recipient not found')


    # if room in user_key:
    #     emit('call_not', {'caller': callerInfo.username}, to=room, include_self=False)
    #     emit('ring_tone', {'room': room}, to=room, include_self=False)
    #     print(user_key)
###end socket io ###
def get_recipient_sid(user_id):
    return user_session.get(str(user_id))


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=80, use_reloader=False, allow_unsafe_werkzeug=True)
