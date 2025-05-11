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
    current_user = session.get('username')
    if not current_user:
        return redirect(url_for('login_page'))
    
    if request.method == 'POST':
        user = db_session.query(User).filter_by(username=current_user).first()
        if not user:
            return redirect(url_for('logout_page')) 
        
        note_content = request.form['note_content']
        note_title = request.form['note_title']
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

    user = db_session.query(User).filter_by(username=current_user).first()
    notes = db_session.query(Note).filter_by(author_id=user.id).all() if user else []
    return render_template("bord.html", notes=notes, user=current_user)

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
    return render_template("profile.html", user=user, notes=notes)

if __name__ == "__main__":
    app.run(debug=True)