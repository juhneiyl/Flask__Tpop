# main.py
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# DATABASE CONFIG
DB_USER = os.environ.get("MYSQL_USER", "root")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD", "password")
DB_HOST = os.environ.get("MYSQL_HOST", "localhost")
DB_NAME = os.environ.get("MYSQL_DB", "railway")

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# MODEL
class TpopEntry(db.Model):
    __tablename__ = "tpop_entry"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    fav_group = db.Column(db.String(100))
    bias = db.Column(db.String(100))
    bias_wrecker = db.Column(db.String(100))
    song_count = db.Column(db.Integer)
    fav_song = db.Column(db.String(200))
    fav_album = db.Column(db.String(200))
    fav_era = db.Column(db.String(50))
    fav_memory = db.Column(db.String(200))
    stan_since = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ROUTES
@app.route('/')
def home():
    return "Welcome to T-Pop Favorites App!"

@app.route('/entries')
def entries():
    # Ensure table exists
    db.create_all()
    
    all_entries = TpopEntry.query.order_by(TpopEntry.created_at.desc()).all()
    return render_template("entries.html", entries=all_entries)

# RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
