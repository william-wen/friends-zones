import os
from flask import *

app = Flask(__name__)
app.config['STYLE_FOLDER'] = os.path.join('static', 'style')


@app.route("/")
def home():
    return render_template("index.html")
