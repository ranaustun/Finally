# from login to another page
# defines a collection of views.templates,static files and other elements that can be applied to application
from flask import Blueprint, render_template
from flask_login import login_user,login_required,logout_user,current_user

views = Blueprint('views', __name__)


@views.route('/')  # this function will run whenever we go to the slash route
@login_required
def home():
    return render_template("home.html")
