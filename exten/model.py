from sqlalchemy import Column, DateTime, func,ForeignKey, Integer, String, VARCHAR, Boolean, LargeBinary, Date, TEXT
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from plugin import timer, db
from datetime import datetime, timezone, timedelta


friends_association = db.Table('friends',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('timestamp', DateTime, default=datetime.utcnow),
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id'))
)

followers = db.Table('followers', db.Column('follower_id', Integer, ForeignKey('user.id'), primary_key=True), Column('timestamp', DateTime, default=datetime.utcnow), Column('followed_id', Integer, ForeignKey('user.id'), primary_key=True))

blocked_users = db.Table('blocked_users',
    db.Column('blocker_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('blocked_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

######Database clases#####

class User(UserMixin, db.Model):
    id = Column(Integer, primary_key=True)
    vote = Column(Integer, default=0)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    firstname = db.Column(db.String(250), nullable=True)
    lastname = db.Column(db.String(250), nullable=True)
    DOB = Column(Date, nullable=True)
    gender=Column(String(10), nullable=False)
    marital = Column(String(100))
    occupation = Column(String(350))
    school = Column(String(350))
    college = Column(String(350))
    points = Column(Integer, default=0)
    home_town = db.Column(db.String(400), nullable=True)
    current_city = db.Column(db.String(500), nullable=True)
    country = db.Column(db.String(80), nullable=True)
    roles = Column(String(50))
    phone_number = db.Column(db.String(80), nullable=True)
    cover_photo = db.Column(VARCHAR(250), nullable=True, default='default.jpeg')
    profile_photo = db.Column(VARCHAR(250), nullable=True, default='default.jpg')
    member_since = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    password = Column(String(250), nullable=False)
    key = Column(String(50), nullable=True)
    confirmed = db.Column(db.Boolean, default=False)
    approve = db.Column(db.Boolean, default=False)
    Bio = db.Column(db.String(2000), nullable=True)
    last_seen = db.Column(DateTime, onupdate=timer())

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            # Include other fields that you want to serialize
        }

    # Relationships
    storys = db.relationship('Story', back_populates='user', overlaps="posts")
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


class Tape(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    video = Column(String(250))
    image = Column(String(250))
    content = Column(String(500))
    when = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", backref="tapes", lazy='select')

class Picture(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    content = Column(String(500))
    image = Column(String(250))
    when = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", backref="pictures", lazy='select')



class Song(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    gallery = Column(String(250))
    music = Column(String(350))
    content = Column(String(500))
    when = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", backref="songs", lazy='select')

class Category(db.Model):
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, ForeignKey('song.id'))
    text = Column(String(200))
    song = relationship('Song', backref='categories', lazy='select')

class Playlist(db.Model):
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, ForeignKey('song.id'))
    text = Column(String(500))
    song = relationship('Song', backref='playlists', lazy='select')

class Bookmark(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=True)
    tape_id = Column(Integer, ForeignKey('tape.id'), nullable=True)
    song_id = Column(Integer, ForeignKey('song.id'), nullable=True)
    picture_id = Column(Integer, ForeignKey('picture.id'), nullable=True)
    user = relationship('User', backref='bookmarks', lazy='select')
    post = relationship('Post', backref='bookmarked_by', lazy='select')
    tape = relationship('Tape', backref='bookmarked_by', lazy='select')
    song = relationship('Song', backref='bookmarked_by', lazy='select')
    picture = relationship('Picture', backref='bookmarked_by', lazy='select')




class Story(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    text = Column(String(500))
    time =Column(DateTime, default=datetime.utcnow)
    expire = Column(DateTime, default=datetime.now(timezone.utc) + timedelta(days=1))
    user = relationship("User", back_populates="storys")

class StoryImage(db.Model):
    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey('story.id'))
    image = Column(String(150))
    time =Column(DateTime, default=datetime.utcnow)
    expire = Column(DateTime, default=datetime.now(timezone.utc) + timedelta(days=1))
    story = relationship('Story', back_populates='story_images')

class StoryVideo(db.Model):
    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey('story.id'))
    video = Column(String(150))
    time =Column(DateTime, default=datetime.utcnow)
    expire = Column(DateTime, default=datetime.now(timezone.utc) + timedelta(days=1))
    story = relationship('Story', back_populates='story_videos')



class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    image = db.Column(String(200))
    video = db.Column(String(300))
    gif = db.Column(String(200))
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

class Season(db.Model):
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    content = Column(String(250), nullable=False)
    cover = Column(String(250))
    user = relationship('User', backref='user-season', lazy='select')


class Contest(db.Model):
    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey('season.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    season = relationship('Season', backref='part-season', lazy='select')
    user = relationship('User', backref='part-user', lazy='select')

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

class SongsNotification(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    song_id = Column(Integer, ForeignKey('song.id'))
    content = Column(String(250), nullable=False)
    read = Column(Boolean, default=False)
    user = relationship('User', backref='notice', lazy='select')
    song = relationship('Song', backref='songnotify', lazy='select')

class Notification(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user2 = Column(Integer, ForeignKey('user.id'))
    content = Column(String(250), nullable=False)
    read = Column(Boolean, default=False)
    when = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', backref='notify1', foreign_keys=[user_id])
    user2_id = relationship('User', foreign_keys=[user2], backref='notify2')

class TapeNotification(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    song_id = Column(Integer, ForeignKey('tape.id'))
    content = Column(String(250), nullable=False)
    read = Column(Boolean, default=False)
    user = relationship('User', backref='tape_notify', lazy='select')
    tape = relationship('Tape', backref='tape_notifys', lazy='select')

class PictureNotification(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    picture_id = Column(Integer, ForeignKey('picture.id'))
    content = Column(String(250), nullable=False)
    read = Column(Boolean, default=False)
    user = relationship('User', backref='picture_notify', lazy='select')
    picture = relationship('Picture', backref='picture_notifys', lazy='select')

class PostNotification(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    post_id = Column(Integer, ForeignKey('post.id'))
    content = Column(String(250), nullable=False)
    read = Column(Boolean, default=False)
    user = relationship('User', backref='p_notify', lazy='select')
    post = relationship('Post', backref='p_notifys', lazy='select')

class MessageNotification(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    message_id = Column(Integer, ForeignKey('messages.id'))
    content = Column(String(250), nullable=False)
    read = Column(Boolean, default=False)
    user = relationship('User', backref='m_notify', lazy='select')
    message = relationship('Messages', backref='m_notifys', lazy='select')

class CommentNotification(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    comment_id = Column(Integer, ForeignKey('comment.id'))
    content = Column(String(250), nullable=False)
    read = Column(Boolean, default=False)
    user = relationship('User', backref='c_cnotify', lazy='select')
    comment = relationship('Comment', backref='c_notifys', lazy='select')

class Comment(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    post_id = Column(Integer, ForeignKey('post.id'))
    tape_id = Column(Integer, ForeignKey('tape.id'))
    song_id = Column(Integer, ForeignKey('song.id'))
    blog_id = Column(Integer, ForeignKey('blog_post.id'))
    picture_id = Column(Integer, ForeignKey('picture.id'))
    content = Column(String(1500))
    image = Column(String(150))
    video =Column(String(150))
    when = Column(db.DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    tape = relationship("Tape", backref="commentst")
    song = relationship("Song", backref="commentss")
    picture = relationship("Picture", backref="commentsp")
    blog = relationship("BlogPost", backref="blogsc")

class CommentReply(db.Model):
    id = db.Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    comment_id = Column(Integer, ForeignKey('comment.id'), nullable=False)
    content = Column(String(1500))
    image = Column(String(150))
    video = Column(String(150))
    time = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    user = relationship('User', backref='comment_replies', lazy='select')
    comment = relationship('Comment', backref='comment_reply', lazy='select')



class Like(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    post_id = Column(Integer, ForeignKey('post.id'))
    reaction = Column(String(50), nullable=False)
    when = Column(db.DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")

class TapeLike(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    tape_id = Column(Integer, ForeignKey('tape.id'))
    reaction = Column(String(50), nullable=False)
    when = Column(db.DateTime, default=datetime.utcnow)
    user = relationship("User", backref="user", lazy='select', uselist=True)
    tape = relationship("Tape", backref="tape", lazy='select')

class SongLike(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    tape_id = Column(Integer, ForeignKey('song.id'))
    reaction = Column(String(50), nullable=False)
    when = Column(db.DateTime, default=datetime.utcnow)
    user = relationship("User", backref="userr", lazy='select')
    song = relationship("Song", backref="songe", lazy='select')

class PictureLike(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    post_id = Column(Integer, ForeignKey('picture.id'))
    reaction = Column(String(50), nullable=False)
    when = Column(db.DateTime, default=datetime.utcnow)
    user = relationship("User", backref="userp", lazy='select')
    picture = relationship("Picture", backref="picturep", lazy='select')

class Vote(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'),nullable=False)
    song_id = Column(Integer, ForeignKey('song.id'))
    tape_id = Column(Integer, ForeignKey('tape.id'))
    picture_id = Column(Integer, ForeignKey('picture.id'))
    reaction = Column(String(100))
    user = relationship('User', backref='voteuser', lazy='select')
    song = relationship('Song', backref='votesong', lazy='select')
    picture = relationship('Picture', backref='votepicture', lazy='select')

class RoomKey(db.Model):
    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer, ForeignKey('user.id'))
    user2_id = Column(Integer, ForeignKey('user.id'))
    key = Column(String(200))
    when = Column(DateTime, default=datetime.utcnow)
    user1 = relationship('User', foreign_keys=[user1_id], backref='roomkeys1')
    user2 = relationship('User', foreign_keys=[user2_id], backref='roomkeys2')

class SearchHistory(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    text = Column(String(500))
    user = relationship("User", back_populates="search_historys")

class BlogPost(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    title = Column(String(250), nullable=False)
    summary = Column(String(250), nullable=False)
    body = Column(TEXT, nullable=False)
    thumb = Column(String(100))
    category = Column(String(100))
    tag = Column(String(100))
    when = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', backref='blogposts', foreign_keys=[user_id])

class BlogComment(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    email = Column(String(200))
    message = Column(String(250))
    when = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'))
    blog_id = Column(Integer, ForeignKey('blog_post.id'))
    user = relationship('User', foreign_keys=[user_id], backref='blogcomments')
    blog = relationship('BlogPost', foreign_keys=[blog_id], backref='blogidcomment')

class BlogReply(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    email = Column(String(200))
    message = Column(String(250))
    when = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'))
    blog_id = Column(Integer, ForeignKey('blog_post.id'))
    comment_id = Column(Integer, ForeignKey('blog_comment.id'))
    user = relationship('User', foreign_keys=[user_id], backref='blogcommentsreply')
    blog = relationship('BlogPost', foreign_keys=[blog_id], backref='blogidcommentreply')
    comment = relationship('BlogComment', foreign_keys=[comment_id], backref='blogreply')

class BlogImage(db.Model):
    id = Column(Integer, primary_key=True)
    blog_id = Column(Integer, ForeignKey('blog_post.id'))
    image = Column(String(300), nullable=False)
    blog = relationship('BlogPost', backref='blog_images', lazy='select')

class BlogVideo(db.Model):
    id = Column(Integer, primary_key=True)
    blog_id = Column(Integer, ForeignKey('blog_post.id'))
    video = Column(String(300), nullable=False)
    blog = relationship('BlogPost', backref='blog_videos', lazy='select')

class BlogLike(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    blog_id = Column(Integer, ForeignKey('blog_post.id'))
    reaction = Column(String(50), nullable=False)
    when = Column(db.DateTime, default=datetime.utcnow)
    user = relationship("User", backref="userlike", lazy='select', uselist=True)
    tape = relationship("BlogPost", backref="blogslike", lazy='select')
class BlogCategory(db.Model):
    id = Column(Integer, primary_key=True)
    text = Column(String(700))
    icon = Column(String(700))


class Categories(db.Model):
    id = Column(Integer, primary_key=True)
    text = Column(String(700))


class Tag(db.Model):
    id = Column(Integer, primary_key=True)
    text = Column(String(700))


# Establish relationships
User.posts = relationship("Post", order_by=Post.id, back_populates="user")
# User.tapes = relationship("Tape", order_by=Post.id, back_populates="user")
# User.songs = relationship("Song", order_by=Post.id, back_populates="user")
# User.pictures = relationship("Picture", order_by=Post.id, back_populates="user")
User.search_historys = relationship("SearchHistory", order_by=SearchHistory.id, back_populates="user")


Post.images = relationship("Image", order_by=Image.id, back_populates="post")
Post.videos = relationship("Video", order_by=Video.id, back_populates="post")
Post.audios = relationship('Audio', order_by=Audio.id, back_populates='post')
Story.story_images = relationship('StoryImage', order_by=StoryImage.id, back_populates='story')
Story.story_videos = relationship('StoryVideo', order_by=StoryVideo.id, back_populates='story')

User.comments = relationship("Comment", order_by=Comment.id, back_populates="user")
User.likes = relationship("Like", order_by=Like.id, back_populates="user")


Post.comments = relationship("Comment", order_by=Comment.id, back_populates="post")

Post.likes = relationship("Like", order_by=Like.id, back_populates="post")
