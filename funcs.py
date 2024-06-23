from exten.model import User, Song,Tape,SearchHistory, Picture, db, followers, Like, Vote, Messages, RoomKey
from flask_login import current_user
from sqlalchemy import asc, desc, func, or_
from plugin import timer, gener
from PIL import Image
from datetime import timedelta, datetime, date
from moviepy.editor import VideoFileClip
from pydub import AudioSegment

###### for functions #####

def me():
    return User.query.get(current_user.id)

def others(username):
    return User.query.filter_by(username=username).first()

def post(post_id):
    play = Song.query.filter_by(id=post_id).first()
    return play

def mutual_friends_count(me, other):
    mutual = db.session.query(func.count(followers.c.follower_id)) \
        .select_from(followers) \
        .join(followers.alias('f2'), followers.c.follower_id == followers.c.followed_id) \
        .filter(followers.c.followed_id == other, followers.c.follower_id == me) \
        .scalar()
    return mutual
def mutual_friends_counts(me, other):
    # Alias for self-join
    f_alias = followers.alias('f_alias')

    # Subquery to find 'other's followers
    other_followers = db.session.query(f_alias.c.follower_id).filter(f_alias.c.followed_id == other).subquery()

    # Count mutual followers
    mutual = db.session.query(func.count(followers.c.follower_id)) \
        .join(f_alias, followers.c.follower_id == f_alias.c.follower_id) \
        .filter(followers.c.followed_id == me, followers.c.follower_id.in_(other_followers)) \
        .scalar()

    return mutual


def mutual_friends_list(me, other):
    mutual = User.query.join(followers, followers.c.follower_id == User.id).filter(followers.c.followed_id == me, User.id.in_(db.session.query(followers.c.follower_id).filter(followers.c.followed_id == other))).all()
    return mutual

def mutual_friends_lists(me, other):
    mutual = User.query.join(followers, followers.c.follower_id == User.id).filter(followers.c.followed_id == me, User.id.in_(db.session.query(followers.c.follower_id).filter(followers.c.followed_id == other))).all()
    return mutual

def search_hist(user_id):
    filters = SearchHistory.query.filter_by(user_id=user_id).order_by(func.random()).limit(5).all()
    return filters


def checklike(post_id, user_id, reaction):
    exists = Like.query.filter_by(post_id=post_id, user_id=user_id, reaction=reaction).first()
    return exists is not None
def checkliked(post_id, reaction):
    exists = Like.query.filter_by(post_id=post_id, reaction=reaction).first()
    return exists
def checkliker(post_id, user_id):
    exists = Like.query.filter_by(post_id=post_id, user_id=user_id).first()
    return exists
def checkvote(post_id, user_id):
    exists = Vote.query.filter_by(tape_id=post_id, user_id=user_id).first()
    return exists
def have_follow(self, user_id):
    return user_id in self.followed


def my_friends(self, user_id):
    need = self.followed.filter(followers.c.followed_id == user_id).first()
    return need
def is_friend(user_id, self):
    need = db.session.query(followers).filter_by(follower_id=self, followed_id=user_id).first()
    if need:
        return need
    else:
        return None

def need_to_accept(self, user_id):
    need = user_id.followed.filter(
        followers.c.followed_id == self.id).count() > 0
    return need
def accept_follow(self, user_id):
    first = user_id in self.followed
    second = user_id.followed.filter(
        followers.c.followed_id == self.id).count() > 0
    if first:
        return f'Unfollow'
    elif second:
        return f'Accept Follow'
    else:
        return f'Follow'
def is_following(self, user_id):
    return self.followed.filter(
        followers.c.followed_id == user_id.id).count() > 0


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




def last_seen():
    try:
        user=User.query.get(current_user.id)
        if user:
            user.last_seen = timer()
            db.session.commit()
    except Exception as e:
        print("An error occurred while updating last seen:", e)
        db.session.rollback()

def onlinetag(user_id):
    if user_id.last_seen is None:
        return False
    else:
        current_time = datetime.now()
        time_diff = current_time - user_id.last_seen
        online_time = timedelta(minutes=7)
        if time_diff <= online_time:
            return True
        else:
            return None

def content_date(when_made):
    current_time = datetime.now()
    if when_made.when is None:
        return False
    else:
        time_diff = current_time - when_made.when
        the_when = time_diff.total_seconds()
        if the_when < 60:
            return f'{the_when} seconds ago'
        elif the_when <= 3600:
            minutes_t = int(the_when // 60)
            return f'{minutes_t} minutes ago'
        elif the_when <= 86400:
            hour_ago = int(the_when // 3600)
            return f'{hour_ago} hours ago'
        else:
            month = timedelta(days=31)
            if time_diff >= month:
                return f'Posted on {when_made.when.strftime("%Y/%m/%D")}'
            else:
                return f'Posted on {when_made.when.strftime("%m/%d")}'


def online(user_id):
    if user_id.last_seen is None:
        return False
    else:
        current_time = datetime.now()
        time_diff = current_time - user_id.last_seen
        online_time = timedelta(minutes=7)
        if time_diff <= online_time:
            return f'Online'
        else:
            offline_time = time_diff.total_seconds()
            if offline_time < 60:
                return f'Offline {int(offline_time)} seconds ago'
            elif offline_time < 3600:
                offline_minues = int(offline_time // 60)
                return f'Offline {int(offline_minues)} minutes ago'
            else:
                offline_hour = int(offline_time // 3600)
                if offline_hour <= 24:
                    return f'Offline {int(offline_hour)} hours ago'
                elif offline_hour > 25:
                    return user_id.last_seen.strftime('%A %B')





def user_user_message(user, other):
    mess = Messages.query.filter(
        (Messages.sender_id == user.id) & (Messages.recipient_id == other.id) | (
                Messages.sender_id == other.id) & (
                Messages.recipient_id == user.id)).order_by(asc(Messages.timestamp)).all()
    return mess

def recent_message(user):
    query = db.session.query(Messages.sender_id, func.max(Messages.id).label('max_id')).filter(
        Messages.recipient_id == user.id).group_by(Messages.sender_id).subquery()
    recent_mess = Messages.query.join(query, query.c.max_id == Messages.id).limit(10).all()
    return recent_mess

def total_s(user_id):
    music = Song.query.filter_by(user_id=user_id).count()
    return music
def total_v(user_id):
    video = Tape.query.filter_by(user_id=user_id).count()
    return video
def total_p(user_id):
    pic = Picture.query.filter_by(user_id=user_id).count()
    return pic

def resize_image(input_path, output_path, size):
    original = Image.open(input_path)
    width, height = original.size
    output = original.resize(size)
    output.save(output_path)

def video_resize(input_path, output_path, new_width):
    clip = VideoFileClip(input_path)
    resize_clip = clip.resize(width = new_width)
    resize_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    clip.close()
    resize_clip.close()

def roomkey(user1, user2):
    room = RoomKey.query.filter_by(user1_id=user1.id, user2_id=user2.id).first() \
           or RoomKey.query.filter_by(user2_id=user1.id, user1_id=user2.id).first()
    current_date = datetime.utcnow()

    if not room:
        keys = RoomKey(user1_id=user1.id, user2_id=user2.id, key=gener())
        db.session.add(keys)
        db.session.commit()
    else:
        time_diff = (current_date - room.when).days
        if time_diff > 1:
            room.key = gener()
            room.when = datetime.utcnow()
            db.session.commit()
        else:
            pass

def roomid(user1, user2):
    roome = RoomKey.query.filter_by(user1_id=user1.id, user2_id=user2.id).first() \
           or RoomKey.query.filter_by(user2_id=user1.id, user1_id=user2.id).first()
    return roome

def recent_messages():
    user = User.query.get(current_user.id)
    current_user_id = user.id
    query = db.session.query(Messages.sender_id, func.max(Messages.id).label('max_id')).filter(
        Messages.recipient_id == current_user_id).group_by(Messages.sender_id).subquery()
    recent_mess = Messages.query.join(query, query.c.max_id == Messages.id).limit(10).all()
    return recent_mess