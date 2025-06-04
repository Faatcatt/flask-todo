from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tajny_klucz'  # do sesji logowania

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'logowanie'

# konfiguracja bazy danych SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zadania.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# MODEL – definicja tabeli
class Zadanie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tresc = db.Column(db.String(200), nullable=False)
    zrobione = db.Column(db.Boolean, default=False)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'))

class Uzytkownik(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), unique=True, nullable=False)
    haslo = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Uzytkownik.query.get(int(user_id))

@app.route("/rejestracja", methods=["GET", "POST"])
def rejestracja():
    if request.method == "POST":
        login = request.form["login"]
        haslo = request.form["haslo"]

        istnieje = Uzytkownik.query.filter_by(login=login).first()
        if istnieje:
            flash("Login już istnieje")
            return redirect("/rejestracja")

        nowy = Uzytkownik(
            login=login,
            haslo=generate_password_hash(haslo)
        )
        db.session.add(nowy)
        db.session.commit()
        flash("Zarejestrowano! Teraz możesz się zalogować.")
        return redirect("/logowanie")

    return render_template("rejestracja.html")

@app.route("/logowanie", methods=["GET", "POST"])
def logowanie():
    if request.method == "POST":
        login = request.form["login"]
        haslo = request.form["haslo"]

        uzytkownik = Uzytkownik.query.filter_by(login=login).first()
        if not uzytkownik or not check_password_hash(uzytkownik.haslo, haslo):
            flash("Nieprawidłowy login lub hasło")
            return redirect("/logowanie")

        login_user(uzytkownik)
        return redirect("/")

    return render_template("logowanie.html")

@app.route("/wyloguj")
@login_required
def wyloguj():
    logout_user()
    return redirect("/logowanie")

@app.route("/przelacz/<int:zadanie_id>")
@login_required
def przelacz_status(zadanie_id):
    zadanie = Zadanie.query.get_or_404(zadanie_id)
    if zadanie.uzytkownik_id == current_user.id:
        zadanie.zrobione = not zadanie.zrobione
        db.session.commit()
    return redirect("/")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        tresc = request.form["zadanie"]
        nowe = Zadanie(tresc=tresc, uzytkownik_id=current_user.id)
        db.session.add(nowe)
        db.session.commit()
        return redirect("/")

    zadania = Zadanie.query.filter_by(uzytkownik_id=current_user.id).all()
    return render_template("index.html", zadania=zadania)

@app.route("/usun/<int:zadanie_id>")
@login_required
def usun_zadanie(zadanie_id):
    zadanie = Zadanie.query.get_or_404(zadanie_id)
    if zadanie.uzytkownik_id == current_user.id:
        db.session.delete(zadanie)
        db.session.commit()
    return redirect("/")

# tworzenie bazy przy pierwszym uruchomieniu
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
