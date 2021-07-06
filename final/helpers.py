import os
import requests
import urllib.parse
import datetime

from flask import redirect, render_template, request, session
from functools import wraps


def currenttime():
    x = datetime.datetime.now()
    return(x.strftime("%x"))

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

# Python program to convert a list to string using join() function
def list_to_string(s):

    # initialize an empty string
    str1 = " "

    # return string
    return (str1.join(s))

# Python code to convert string to list

def string_to_list(string):
    li = list(string.split(" "))
    return li