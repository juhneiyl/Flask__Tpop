from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = "janelle"

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('mysql://'):
    database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'mysql+pymysql://root:@localhost/tpop_db'
db = SQLAlchemy(app)

class TpopEntry(db.Model):
    _tablename_ = 'tpop_entry'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    fav_group = db.Column(db.String(100), nullable=False)
    bias = db.Column(db.String(100), nullable=False)
    bias_wrecker = db.Column(db.String(100), nullable=False)
    song_count = db.Column(db.Integer, nullable=False)
    fav_song = db.Column(db.String(200), nullable=False)
    fav_album = db.Column(db.String(200), nullable=True)
    fav_era = db.Column(db.String(100), nullable=False)
    fav_memory = db.Column(db.Text, nullable=False)
    stan_since = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    try:
        entry = TpopEntry(
            name=request.form['name'],
            fav_group=request.form['fav_group'],
            bias=request.form['bias'],
            bias_wrecker=request.form['bias_wrecker'],
            song_count=int(request.form['song_count']),
            fav_song=request.form['fav_song'],
            fav_album=request.form.get('fav_album'),
            fav_era=request.form.get('fav_era'),
            fav_memory=request.form['fav_memory'],
            stan_since=request.form.get('stan_since')
        )

        db.session.add(entry)
        db.session.commit()
        flash("Thanks for sharing your T-pop love!", "success")

    except Exception as e:
        db.session.rollback()
        print("ERROR:", e)
        flash("Something went wrong. Please try again.", "error")

    return redirect(url_for('index'))


@app.route('/entries')
def entries():
    all_entries = TpopEntry.query.order_by(TpopEntry.created_at.desc()).all()
    return render_template('entries.html', entries=all_entries)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

