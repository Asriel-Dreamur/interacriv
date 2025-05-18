from flask import Flask, render_template, session, request, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Note

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
database_url = "sqlite:///secret_information.db"
engine = create_engine(database_url)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@app.route("/", methods=['GET', 'POST'])
def home_page():
    db_session = Session()
    current_username = session.get('username')
    
    if not current_username:
        return redirect(url_for('login_page'))

    user = db_session.query(User).filter_by(username=current_username).first()
    if not user:
        session.pop('username', None)
        return redirect(url_for('login_page'))

    show_all = request.args.get('showAll', 'false') == 'true'

    query = db_session.query(Note)
    if not show_all:
        query = query.filter(Note.author_id == user.id)

    filter_type = request.args.get('filter', 'newest')
    if filter_type == 'oldest':
        query = query.order_by(Note.created_at.asc())
    elif filter_type == 'alphabetical':
        query = query.order_by(Note.title.asc())
    else:
        query = query.order_by(Note.created_at.desc())

    notes = query.all()

    if request.method == 'POST':
        note_title = request.form.get('note_title')
        note_content = request.form.get('note_content')
        linked_note_id = request.form.get('linked_note') or None
        
        new_note = Note(
            title=note_title,
            content=note_content,
            author_id=user.id,
            bound_note_id=linked_note_id
        )
        db_session.add(new_note)
        db_session.commit()
        return redirect(url_for('home_page'))

    return render_template("bord.html", 
                         notes=notes, 
                         user=user,
                         show_all=show_all,
                         current_filter=filter_type)

@app.route("/registration", methods=["POST", "GET"])
def register_page():
    db_session = Session()
    if request.method == "GET":
        return render_template("register.html")
    
    username = request.form.get("username").lower()
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")

    if db_session.query(User).filter_by(username=username).first():
        return render_template("register.html", error="Пользователь с таким ником уже есть")

    if password != confirm_password:
        return render_template("register.html", error="Пароли не совпадают")

    if len(password) <= 8:
        return render_template("register.html", error="Пароль слишком маленький")


    new_user = User(username=username, password=password)
    db_session.add(new_user)
    db_session.commit()
    
    session["username"] = username
    return redirect('/')

@app.route("/logout")
def logout_page():
    session.pop('username', None)
    return redirect('/login')

@app.route("/login", methods=["POST", "GET"])
def login_page():
    db_session = Session()
    if request.method == "GET":
        return render_template("login.html")
    
    username = request.form.get("username").lower()
    password = request.form.get("password")

    user = db_session.query(User).filter_by(username=username).first()
    if not user or user.password != password:
        return render_template("login.html", error="Неправильный логин или пароль")

    session["username"] = username
    return redirect('/')
@app.route("/profile")
def profile_page():
    db_session = Session()
    current_user = session.get('username')
    if not current_user:
        return redirect(url_for('login_page'))
    
    user = db_session.query(User).filter_by(username=current_user).first()
    notes = db_session.query(Note).filter_by(author_id=user.id).all()
    filter_type = request.args.get('filter', 'newest')
    order = Note.created_at.desc()

    if filter_type == 'oldest':
        order = Note.created_at.asc()
    elif filter_type == 'alphabetical':
        order = Note.title.asc()
    
    notes = db_session.query(Note)\
        .filter_by(author_id=user.id)\
        .order_by(order)\
        .all()
    
    return render_template("profile.html", notes=notes, user=user, current_filter=filter_type)

@app.route("/delete_note/<int:note_id>", methods=['POST'])
def delete_note(note_id):
    db_session = Session()
    note = db_session.query(Note).get(note_id)
    
    db_session.delete(note)
    db_session.commit()
    return redirect(url_for('profile_page'))

@app.route("/edit_note/<int:note_id>", methods=['GET', 'POST'])
def edit_note(note_id):
    db_session = Session()
    note = db_session.query(Note).get(note_id)

    if request.method == 'POST':
        note.title = request.form['title']
        note.content = request.form['content']
        db_session.commit()
        return redirect(url_for('profile_page'))
    
    return render_template('edit_note.html', note=note)

if __name__ == "__main__":
    app.run(debug=True)