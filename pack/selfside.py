from flask import render_template, request, abort, Blueprint, redirect, url_for, session
from plugin import timer


slef = Blueprint('self',__name__)


@slef.route('/')
def home():
    return render_template('self/about.html', date=timer())