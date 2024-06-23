


class Config():
    DEBUG=True
    SECRET_KEY="43658yweghgbtutgeerghdfghstwfgvwfh"
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://usbrkkoplvegqwrs:sfRCmVxVidEpYibk6FI0@bleybyeph70hyr5wq99h-mysql.services.clever-cloud.com:3306/bleybyeph70hyr5wq99h'
    MAIL_SERVER= 'live.smtp.mailtrap.io'
    MAIL_PORT = 587
    MAIL_USERNAME ='api'
    MAIL_PASSWORD = '4f0a67bc24b190908b975086a66daf35'
    MAIL_USE_TLS =True
    MAIL_USE_SSL = False
    SENDER = 'mailtrap@apptok.top'
    UPLOAD_FOLDER_CIMAGE = 'static/user/cover'
    UPLOAD_FOLDER_PIMAGE='static/user/profile'
    UPLOAD_FOLDER_AUDIO = 'static/user/audios/'
    UPLOAD_FOLDER_ORIGIN ='static/debris'
    UPLOAD_FOLDER_IMAGE = 'static/user/imgs/'
    BLOG_FOLDER_IMAGE = 'static/blog/imgs/'
    BLOG_FOLDER_VIDEO = 'static/blog/videos/'
    UPLOAD_FOLDER_VIDEO = 'static/user/videos/'
    UPLOAD_FOLDER_ADMIN ='static/admin/sys_files/'
    MAX_CONTENT_LENGTH = 250 * 1024 * 1024
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND ='redis://localhost:6379/0'
    CELERY_TIMEZONE = 'UTC'
    ENABLE_DEBUG = True
    PUSHER_APP_ID ='1818315'
    PUSHER_KEY ='7ac754dd309e12be067c'
    PUSHER_SECRET = '094344802b4bf7e7cddb'
    PUSHER_CLUSTER ='eu'
    AGORA_APP_ID ='91228496c69244bf8c681264e4b7b8c2'
    AGORA_APP_CERTIFICATE ='1c9cd58d34694ddf8af5275eb895bef4'
