import os
from flask import *
import pyrebase
import datetime
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
from places import get_recommended_locations, api_key

app = Flask(__name__)
app.config['STYLE_FOLDER'] = os.path.join('static', 'style')
app.config['SECRET_KEY'] = SECRET_KEY = os.environ.get(
    'SECRET_KEY') or b'6\xe9\xda\xead\x81\xf7\x8d\xbbH\x87\xe8m\xdd3%'

URL = "https://f2197a9b5ffd.ngrok.io"

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
    return render_template("menu.html")


@app.route("/logout")
def logout():
    session['email'] = False
    session.pop('name', None)
    session.pop('avatar_url', None)
    return redirect(url_for('home'))


@app.route("/join-group-temp")
def join_group_temp():
    return render_template("create-group.html")


@app.route("/join-group")
def join_group():

    return render_template("interests.html")


# @app.route("/profile")
# def profile():
#     return render_template("interests.html")


@app.route("/get-profile", methods=["POST", "GET"])
def get_profile():
    interests = request.form["interests"]
    max_budget = request.form["inlineRadioOptions"]
    end_time = request.form["appt2"]

    db.child("users").child(session.get("name")).child(
        "interests").set(interests)
    db.child("users").child(session.get("name")
                            ).child("end_time").set(end_time)
    db.child("users").child(session.get("name")).child(
        "max_budget").set(max_budget)

    return render_template("map.html", api_key=api_key)


@app.route("/recommendations", methods=["POST"])
def get_recommendations():
    latitude_longitude = request.get_json()
    interests = db.child("users").child(
        session.get("name")).child("interests").get().val()
    end_time = db.child("users").child(
        session.get("name")).child("end_time").get().val()
    max_budget = db.child("users").child(
        session.get("name")).child("max_budget").get().val()

    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    day = datetime.datetime.now().day

    end_time = datetime.datetime.strptime(
        f"{year}-{month}-{day} {end_time}", "%Y-%m-%d %H:%M")

    locations = get_recommended_locations(
        latitude_longitude["latitude"],
        latitude_longitude["longitude"],
        interests,
        end_time,
        len(max_budget)
    )
    print(locations)
    return jsonify(locations)

@app.route("/groupmembers")
def group_members():
    members = {}
    members["Olivia Xie"] = "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=10223800101526716&height=50&width=50&ext=1613460767&hash=AeSPpq7qAVZTW_lXR4Y"
    members["Laura Dang"] = "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=2234534156678233&height=50&width=50&ext=1613461426&hash=AeRfyYt44G8ZBTv0W_Y"
    members["Yifei Zhang"] = "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=4139616992734146&height=50&width=50&ext=1613461249&hash=AeRbETb0mukSewdxlbo"
    members["William Wen"] = "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=2860772024206205&height=50&width=50&ext=1613458462&hash=AeRMcAUTSatbq4Hzlxc"

    return render_template("groupmembers.html", members=members)
