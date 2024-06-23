from flask import Flask, redirect, Blueprint, render_template, url_for, flash,session, request, current_app
from werkzeug.utils import secure_filename
import os
from flask_bcrypt import Bcrypt
import uuid
from exten.model import *
from funcs import *
from plugin import bcrypt, limiter
from extension import *

bp = Blueprint('main', __name__, static_folder='static')


@bp.errorhandler(429)
def limit(e):
    user = me()
    flash(f'You have exceeded your upload limit','cant')
    return redirect(url_for('main.profile', username=user.username))

@bp.route('/')
def homee():
    if session.get('logged_in'):
        if me().roles not in ['Admin','Artist']:
            return redirect(url_for('home'))
        else:
            user = User.query.get(current_user.id)
            music = Song.query.filter_by(user_id=user.id).count()
            video = Tape.query.filter_by(user_id=me().id).count()
            pic = Picture.query.filter_by(user_id=me().id).count()
            total = int(video + pic + music)
            return render_template('dist/account/overview.html', user=user, proj=total)
    else:
        return redirect(url_for('login'))

@bp.route('/back')
def back():
    if 'backbtn' in request.args:
        return redirect(request.args.get('backbtn'))
    else:
        return redirect(url_for('main.homee'))

@bp.route('/project')
def project():
    if session.get('logged_in'):
        if me().roles not in ['Admin','Artist']:
            return redirect(url_for('home'))
        else:
            sn = Song.query.filter_by(user_id=me().id).first()
            if sn is None:
                return redirect(url_for('main.account'))
            else:
                music = Song.query.filter_by(user_id=me().id).count()
                video = Tape.query.filter_by(user_id=me().id).count()
                pic = Picture.query.filter_by(user_id=me().id).count()
                total = int(total_p(user_id=me().id) + total_s(user_id=me().id) + total_v(user_id=me().id))
                song = Song.query.filter_by(user_id=me().id).first()

                return render_template('dist/pages/user-profile/documents.html', song=song, video=video, pic=pic,
                                       proj=total, total=total, user=me(), music=music)
    else:
        return redirect(url_for('login'))

@bp.route('/followers/<username>')
def follow_link(username):
    if session.get('logged_in'):
        user = me()
        other = others(username=username)
        is_friend = User.query.filter(User.id != current_user.id,
                                      User.followers.any(User.id == current_user.id)).order_by(
            func.random()).all()

        have = {}
        for they in is_friend:
            have[they.id] = have_follow(self=user, user_id=they)
        return render_template('dist/pages/user-profile/followers.html', have=have,user=user, other=other, is_friend=is_friend)
    else:
        return redirect(url_for('login'))

@bp.route('/beats')
def beats():
    if session.get('logged_in'):
        if me().roles not in ['Admin','Artist']:
            return redirect(url_for('home'))
        else:
            songs = Song.query.order_by(func.random()).all()
            so = Song.query.order_by(func.random()).all()
            song = Song.query.order_by(func.random()).first()
            songz = Song.query.order_by(func.random()).first()
            return render_template('songs.html', user=me(), song=song, so=so, songs=songs, songz=songz)
    else:
        return redirect('login')

@bp.route('/my-medias')
def account():
    if session.get('logged_in'):
        if me().roles not in ['Admin','Artist']:
            return redirect(url_for('home'))
        else:
            music = Song.query.filter_by(user_id=me().id).count()
            song = Song.query.filter_by(user_id=me().id).all()
            return render_template('dist/apps/file-manager/folders.html', user=me(), music=music, songs=song)
    else:
        return redirect(url_for('login'))

@bp.route('/songs/<int:post_id>')
def songs_play(post_id):
    if session.get('logged_in'):
        song = post(post_id=post_id)
        songs=Song.query.limit(4).all()
        so =Song.query.limit(4).all()
        return render_template('dist/dashboards/podcast.html', user=me(), song=song, songs=songs, so=so)
    else:
        return redirect(url_for('login'))

@bp.route('/upload', methods=['POST'])
@limiter.limit("20 per 120 days")
def upload():
    if session.get('logged_in'):
       if me().roles =='Admin':
           user = me()
           content = request.form.get('title')
           gallery = request.files.get('gallery')
           song = request.files.get('audio')

           imag_name = secure_filename(song.filename)
           new_nam = str(uuid.uuid4())
           new_exts = os.path.splitext(imag_name)[1]
           news = new_nam + new_exts
           paths = os.path.join(current_app.config['UPLOAD_FOLDER_AUDIO'], news)
           song.save(paths)
           image_name = secure_filename(gallery.filename)
           new_na = str(uuid.uuid4())
           new_ext = os.path.splitext(image_name)[1]
           new = new_na + new_ext
           path = os.path.join(current_app.config['UPLOAD_FOLDER_IMAGE'], new)
           gallery.save(path)
           submit = Song(content=content, gallery=new, music=news, user_id=user.id)
           db.session.add(submit)
           db.session.commit()

           return redirect(url_for('main.back', backbtn=request.referrer))
       else:
           flash(f'You do not have the necessary permission to upload beat.')
           return redirect(url_for('main.back', backbtn=request.referrer))
    else:
        return redirect(url_for('login'))

@bp.route('/settings')
def settings():
    if session.get('logged_in'):
        if me().roles not in ['Admin','Artist']:
            return redirect(url_for('home'))
        else:
            music = Song.query.filter_by(user_id=me().id).count()
            video = Tape.query.filter_by(user_id=me().id).count()
            pic = Picture.query.filter_by(user_id=me().id).count()
            total = int(total_p(user_id=me().id) + total_s(user_id=me().id) + total_v(user_id=me().id))
            song = Song.query.filter_by(user_id=me().id).first()
            return render_template('dist/account/settings.html', user=me(), proj=total)
    else:
        return redirect(url_for('login'))

@bp.route('/sett', methods=['POST'])
def sett():
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        firstname = request.form.get('firstname', user.firstname)
        lastname = request.form.get('lastname', user.firstname)

        username = request.form.get('username', user.username)
        home_town = request.form.get('address', user.home_town)
        current_city = request.form.get('city', user.current_city)
        country = request.form.get('country', user.country)
        DOB = request.form.get('DOB', user.DOB)
        phone_number = request.form.get('phone', user.phone_number)
        gender = request.form.get('gender', user.gender)
        roles = request.form.get('roles', user.roles)
        marital = request.form.get('marital', user.marital)
        Bio = request.form.get('Bio', user.Bio)
        profile_photo = request.files.get('avatar')

        if firstname:
            user.firstname = firstname
        if roles:
            user.roles = roles
        if profile_photo:
            file_name = secure_filename(profile_photo.filename)
            new_n = str(uuid.uuid4())
            new_ext = os.path.splitext(file_name)[1]
            file_new = new_n + new_ext
            path = os.path.join(current_app.config['UPLOAD_FOLDER_IMAGE'], file_new)
            profile_photo.save(path)
            user.profile_photo = file_new
        if Bio:
            user.Bio =Bio
        if marital:
            user.marital = marital
        if lastname:
            user.lastname = lastname
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
        flash(f'Done', 'success')
        return redirect(url_for('main.back', backbtn=request.referrer))
    else:
        return redirect(url_for('login'))

@bp.route('/new_email', methods=['POST'])
@limiter.limit("1 per 40 days")
def update_email():
    if session.get('logged_in'):
        current_email = request.form.get('emailaddress')
        confirm_pass = request.form.get('confirmemailpassword')
        user= me()
        passw = bcrypt.check_password_hash(user.password, confirm_pass)
        if passw:
            user.email = current_email
            db.session.commit()
            flash('Updated successfully', 'success')
            return redirect(url_for('main.back', backbtn=request.referrer))
        else:
            flash('Incorrect password', 'error')
            return redirect(url_for('main.back', backbtn=request.referrer))

    else:
        return redirect(url_for('login'))

@bp.route('/change-pass', methods=['POST'])
@limiter.limit("4 per 7 days")
def change_pass():
    if session.get('logged_in'):
        user = me()
        passw = request.form.get('newpassword')
        curr = request.form.get('currentpassword')
        repeat = request.form.get('confirmpassword')
        mypass = bcrypt.check_password_hash(user.password, curr)
        if mypass:
            if passw == repeat:
                user.password = repeat
                db.session.commit()
                flash(f'Done', 'success')
                return redirect(url_for('main.back', backbtn = request.referrer))
            else:
                flash(f'Password did not match', 'error')
                return redirect(url_for('main.back', backbtn=request.referrer))
        else:
            flash(f'Incorrect password', 'danger')
            return redirect(url_for('main.back', backbtn=request.referrer))
    else:
        return redirect(url_for('login'))

@bp.route('/profile/<username>')
def profile(username):
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        other = User.query.filter_by(username=username).first()
        if user.roles in ['Admin','Artist']:
            last_seen()

            follows = is_following(self=user, user_id=other)
            have_follows = have_follow(self=user, user_id=other)
            need_to = need_to_accept(self=user, user_id=other)
            accept_foll = accept_follow(self=user, user_id=other)
            own_profile = (current_user.is_authenticated and other.username == current_user.username)
            status = online(user_id=other)
            stat = onlinetag(user_id=other)
            posts = Post.query.filter_by(user_id=other.id, privacy='Public').all() or Tape.query.filter_by(user_id=other.id).all()
            follower = other.followers.all()
            follow_count = other.followers.count()
            search = search_hist(user_id=current_user.id)
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


            return render_template('main/profile.html',recents=recent_messages(), backtn=request.referrer, search=search, follower=follower,
                                   follow_count=follow_count, need=need_to, acc=accept_foll, have_follows=have_follows,
                                   follows=follows, comment=comment, lk=lk, liker=liker, exs=exs, other=other,
                                   stat=stat, own_profile=own_profile, user=user, posts=posts, images=images,
                                   albums=albums, status=status, roomid=get_roomkey(user_id=user, other_id=other), count=notify_count(user=user))

        else:
            return redirect(url_for('profile', username=other.username))
    else:
        return redirect(url_for('login'))

@bp.route('/videos')
def videos():
    if session.get('logged_in'):
        vid = Tape.query.all()
        user = User.query.get(current_user.id)
        other = user
        return render_template('main/video.html', recents=recent_messages(), count=notify_count(user=user), user=me(),roomid=get_roomkey(user_id=user, other_id=other), vid=vid, search = search_hist(user_id=current_user.id))
    else:
        return redirect(url_for('login'))

@bp.route('/video-watch/<int:post_id>')
def watch(post_id):
    if session.get('logged_in'):
        vid = Tape.query.filter_by(id=post_id).first()
        tape = Tape.query.order_by(func.random()).all()
        user = me()
        other = user
        upvote = Vote.query.filter_by(tape_id=post_id, reaction='thumbs-up').all()
        downvote = Vote.query.filter_by(tape_id=post_id, reaction='thumbs-down').all()
        search = search_hist(user_id=current_user.id)
        c = Comment.query.filter_by(tape_id=vid.id).order_by(asc(Comment.when)).all()
        return render_template('main/video-watch.html',recents=recent_messages(), count=notify_count(user=user), roomid=get_roomkey(user_id=user, other_id=other),tape=tape,c=c,vote=len(upvote),dv=len(downvote),search=search, vid=vid, user=user)
    else:
        return redirect(url_for('login'))

@bp.route('/add-comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        content = request.form.get('comment')
        if content == '':
            return redirect(url_for('main.back', backbtn = request.referrer))
        else:
            submit = Comment(tape_id = post_id, content=content, user_id = user.id)
            db.session.add(submit)
            db.session.commit()
            return redirect(url_for('main.back', backbtn=request.referrer))
    else:
        return redirect(url_for('login'))

@bp.route('/create', methods=['POST'])
@limiter.limit("1 per 120 days")
def create():
    if session.get('logged_in'):
        user = me()
        if user.roles in ['Admin','Artist']:
            video = request.files.getlist('media')
            image = request.files.get('image')
            content = request.form.get('content')
            im_na = secure_filename(image.filename)
            new_vi = str(uuid.uuid4())
            ext_im = os.path.splitext(im_na)[1]
            joiner_im = new_vi + ext_im
            path2 = os.path.join(current_app.config['UPLOAD_FOLDER_IMAGE'], joiner_im)
            image.save(path2)
            for files in video:
                filetype = files.content_type
                if filetype in ['video/mp4']:
                    vid_na = secure_filename(files.filename)
                    new_vii = str(uuid.uuid4())
                    ext_v = os.path.splitext(vid_na)[1]
                    joiner_v = new_vii + ext_v
                    path1 = os.path.join(current_app.config['UPLOAD_FOLDER_VIDEO'], joiner_v)
                    files.save(path1)
                    submit = Tape(user_id=user.id, image = joiner_im, video=joiner_v, content=content)
                    db.session.add(submit)
            try:
                db.session.commit()
                flash(f'Done', 'success')
                return redirect(url_for('main.back', backbtn=request.referrer))
            except Exception as e:
                db.session.rollback()
                flash(f'Error occurred','error')
                return redirect(url_for('main.back', backbtn=request.referrer))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@bp.route('/like/<int:post_id>/<reaction>', methods=['POST'])
def add_like(post_id, reaction):
    if session.get('logged_in'):
        user = User.query.get(current_user.id)
        checkex =checkvote(post_id=post_id, user_id=user.id)
        if checkex:
            #likes = Like.query.filter_by(user_id=user.id, post_id=post_id).first()
            checkex.reaction = reaction
            db.session.commit()
            flash('Your reaction has been updated.', 'success')

        else:
            liker = Vote(tape_id=post_id, reaction=reaction, user_id=user.id)
            db.session.add(liker)
            db.session.commit()
            flash('Your reaction has been updated.', 'success')
        return redirect(url_for('main.back', backbtn=request.referrer))
    else:
        return redirect(url_for('login'))
