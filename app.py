import os
from flask import *
import pyrebase
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
from places import get_recommended_locations, api_key

app = Flask(__name__)
app.config['STYLE_FOLDER'] = os.path.join('static', 'style')
app.config['SECRET_KEY'] = SECRET_KEY = os.environ.get(
    'SECRET_KEY') or b'6\xe9\xda\xead\x81\xf7\x8d\xbbH\x87\xe8m\xdd3%'

URL = "https://9aebc7405841.ngrok.io"

# Facebook Config
FB_CLIENT_ID = "484970169157197"
FB_CLIENT_SECRET = "8161685a27aa1c66ca51e4eb8ce673db"

FB_AUTHORIZATION_BASE_URL = "https://www.facebook.com/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"

FB_SCOPE = ["email"]

# Firebase Config
firebase_config = {
    "apiKey": "AIzaSyAKXOcPOF6HJSB-vSTGAram9dyPtGNWDYc",
    "authDomain": "friend-zones-7500a.firebaseapp.com",
    "databaseURL": "https://friend-zones-default-rtdb.firebaseio.com",
    "storageBucket": "friend-zones.appspot.com"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()


@app.route("/")
def home():
    if session.get('email'):
        return redirect(url_for('fb_callback'))

    return render_template("login.html")


@app.route("/fb-login")
def fb_login():
    facebook = requests_oauthlib.OAuth2Session(
        FB_CLIENT_ID, redirect_uri=URL + "/fb-callback", scope=FB_SCOPE
    )
    authorization_url, _ = facebook.authorization_url(
        FB_AUTHORIZATION_BASE_URL)

    return redirect(authorization_url)


@app.route("/fb-callback")
def fb_callback():
    facebook = requests_oauthlib.OAuth2Session(
        FB_CLIENT_ID, scope=FB_SCOPE, redirect_uri=URL + "/fb-callback"
    )

    facebook = facebook_compliance_fix(facebook)

    facebook.fetch_token(
        FB_TOKEN_URL,
        client_secret=FB_CLIENT_SECRET,
        authorization_response=URL + request.full_path,
    )

    facebook_user_data = facebook.get(
        "https://graph.facebook.com/me?fields=id,name,email,picture{url}"
    ).json()

    email = facebook_user_data.get("email")
    name = facebook_user_data["name"]
    avatar_url = facebook_user_data.get(
        "picture", {}).get("data", {}).get("url")

    data = {"email": email, "avatar_url": avatar_url}
    db.child("users").child(name).set(data)

    session['email'] = email
    session['name'] = name
    session['avatar_url'] = avatar_url

    """
    return render_template(
        "test.html",
        name=name,
        email=email,
        avatar_url=avatar_url,
        provider="Facebook",
    )
    """
    return render_template("map.html", api_key=api_key)


@app.route("/logout")
def logout():
    session['email'] = False
    session.pop('name', None)
    session.pop('avatar_url', None)
    return redirect(url_for('home'))


@app.route("/recommendations", methods=["POST"])
def get_recommendations():
    # The variable name for form input tag needs to be interests, end_time, etc. in HTML
    # interests = request.form["interests"]
    # end_time = request.form["end_time"]
    # max_budget = request.form["max_budget"]
    # min_budget = request.form["min_budget"]
    latitude_longitude = request.get_json()

    return latitude_longitude
    # location_info = get_recommended_locations(lat, lng, interests, end_time, max_budget, min_budget)
    
    # return render_template("<REPLACE_ME>", location_info=location_info) # location_info is a dict
