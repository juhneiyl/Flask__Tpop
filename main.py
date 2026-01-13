from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "janelle"

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('mysql://'):
    database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
    
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'mysql+pymysql://root:@localhost/tpop_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class TpopEntry(db.Model):
    __tablename__ = 'tpop_entry'
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
    youtube_link = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reactions = db.relationship('Reaction', backref='entry', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='entry', lazy=True, cascade='all, delete-orphan')

class Reaction(db.Model):
    __tablename__ = 'reactions'
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('tpop_entry.id'), nullable=False)
    user_identifier = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('tpop_entry.id'), nullable=False)
    commenter_name = db.Column(db.String(100), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

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
            stan_since=request.form.get('stan_since'),
            youtube_link=request.form.get('youtube_link')
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
    search = request.args.get('search', '')
    filter_group = request.args.get('group', '')
    
    query = TpopEntry.query
    
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                TpopEntry.fav_group.like(search_pattern),
                TpopEntry.bias.like(search_pattern),
                TpopEntry.fav_song.like(search_pattern),
                TpopEntry.name.like(search_pattern)
            )
        )
    
    if filter_group:
        query = query.filter(TpopEntry.fav_group.like(f'%{filter_group}%'))
    
    all_entries = query.order_by(TpopEntry.created_at.desc()).all()
    
    all_groups = db.session.query(TpopEntry.fav_group).distinct().all()
    groups_list = sorted([g[0] for g in all_groups])
    
    for entry in all_entries:
        entry.reaction_count = len(entry.reactions)
        entry.comment_count = len(entry.comments)
    
    return render_template('entries.html', entries=all_entries, groups=groups_list, search=search, filter_group=filter_group)

@app.route('/stats')
def stats():
    popular_groups = db.session.query(
        TpopEntry.fav_group,
        func.count(Reaction.id).label('reaction_count')
    ).join(Reaction).group_by(TpopEntry.fav_group).order_by(func.count(Reaction.id).desc()).limit(10).all()
    
    popular_biases = db.session.query(
        TpopEntry.bias,
        TpopEntry.fav_group,
        func.count(TpopEntry.id).label('mention_count')
    ).group_by(TpopEntry.bias, TpopEntry.fav_group).order_by(func.count(TpopEntry.id).desc()).limit(10).all()
    
    popular_songs = db.session.query(
        TpopEntry.fav_song,
        TpopEntry.fav_group,
        func.count(TpopEntry.id).label('mention_count')
    ).group_by(TpopEntry.fav_song, TpopEntry.fav_group).order_by(func.count(TpopEntry.id).desc()).limit(10).all()
    
    total_entries = TpopEntry.query.count()
    total_reactions = Reaction.query.count()
    total_comments = Comment.query.count()
    
    return render_template('stats.html', 
                         popular_groups=popular_groups,
                         popular_biases=popular_biases,
                         popular_songs=popular_songs,
                         total_entries=total_entries,
                         total_reactions=total_reactions,
                         total_comments=total_comments)

@app.route('/react/<int:entry_id>', methods=['POST'])
def react(entry_id):
    user_id = request.json.get('user_identifier', 'anonymous')
    
    # Check if user already reacted
    existing = Reaction.query.filter_by(entry_id=entry_id, user_identifier=user_id).first()
    
    if existing:
        # Unlike
        db.session.delete(existing)
        db.session.commit()
        action = 'removed'
    else:
        # Like
        reaction = Reaction(entry_id=entry_id, user_identifier=user_id)
        db.session.add(reaction)
        db.session.commit()
        action = 'added'
    
    count = Reaction.query.filter_by(entry_id=entry_id).count()
    return jsonify({'success': True, 'action': action, 'count': count})

@app.route('/comment/<int:entry_id>', methods=['POST'])
def comment(entry_id):
    try:
        commenter_name = request.form.get('commenter_name')
        comment_text = request.form.get('comment_text')
        
        if not commenter_name or not comment_text:
            flash("Please fill in all comment fields.", "error")
            return redirect(url_for('entries'))
        
        new_comment = Comment(
            entry_id=entry_id,
            commenter_name=commenter_name,
            comment_text=comment_text
        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added!", "success")
    except Exception as e:
        db.session.rollback()
        print("ERROR:", e)
        flash("Could not add comment.", "error")
    
    return redirect(url_for('entries'))

@app.route('/test-db')
def test_db():
    try:
        db.session.execute(db.text('SELECT 1'))
        return "DB is connected!"
    except Exception as e:
        return f"DB connection error: {e}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
