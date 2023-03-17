from data import db_session
from data.news import News
from data.jobs import Jobs
from data.users import User

from forms.user import RegisterForm, LoginForm
from forms.news import NewsForm

from flask import Flask, abort, redirect, render_template, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    logout_user,
    login_user,
)


DB_PATH = "/".join(__file__.split("/")[:-2]) + "/db/blogs.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"

login_manager = LoginManager()

login_manager.init_app(app)


@login_manager.user_loader
def load_user(id):
    db_sess = db_session.create_session()
    return db_sess.get(User, id)


@app.route("/")
def index():
    db_sess = db_session.create_session()

    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True)
        )
    else:
        news = db_sess.query(News).filter(News.is_private != True)

    return render_template("index.html", news=news)


@app.route("/register", methods=["GET", "POST"])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template(
                "register.html",
                title="Sign up",
                form=form,
                message="Passwords doesn't match",
            )
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template(
                "register.html",
                title="Sign up",
                form=form,
                message="This user exists",
            )
        user = User(
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            position=form.position.data,
            speciality=form.speciality.data,
            address=form.address.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user)
        return redirect("/")
    return render_template("register.html", title="Регистрация", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template(
            "login.html", message="Incorrect login or password", form=form
        )
    return render_template("login.html", title="Sign in", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/news", methods=["GET", "POST"])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect("/")
    return render_template("news.html", title="Add", form=form)


@app.route("/news/<int:id>", methods=["GET", "POST"])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = (
            db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        )
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = (
            db_sess.query(News).filter(News.id == id, News.user == current_user).first()
        )
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect("/")
        else:
            abort(404)
    return render_template("news.html", title="Edit", form=form)


@app.route("/news_delete/<int:id>", methods=["GET", "POST"])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id, News.user == current_user).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect("/")


def row_exists(model, **kwargs):
    return db_session.create_session().query(model).filter_by(**kwargs).count() != 0


def register_colonists():
    CAPTAIN = {
        "surname": "Scott",
        "name": "Ridley",
        "age": 21,
        "position": "captain",
        "speciality": "research engineer",
        "address": "module_1",
        "email": "scott_chief@mars.org",
    }
    COLONISTS = (
        {
            "surname": "Nick",
            "name": "Valentine",
            "age": 35,
            "position": "low",
            "speciality": "cleaner",
            "address": "module_5",
            "email": "nick_valley@mars.org",
        },
        {
            "surname": "Elon",
            "name": "Musk",
            "age": 51,
            "position": "high",
            "speciality": "business man",
            "address": "module_7",
            "email": "elon_musk@mars.org",
        },
        {
            "surname": "Tony",
            "name": "Stark",
            "age": 45,
            "position": "captain helper",
            "speciality": "tech engineer",
            "address": "module_4",
            "email": "tony_stark@mars.org",
        },
    )

    db_sess = db_session.create_session()

    if not row_exists(User, **CAPTAIN):
        db_sess.add(User(**CAPTAIN))

    for colonist in COLONISTS:
        if not row_exists(User, **colonist):
            db_sess.add(User(**colonist))

    db_sess.commit()


def create_initial_job():
    JOB = {
        "team_leader": 1,
        "job": "deployment of residential modules 1 and 2",
        "work_size": 15,
        "collaborators": "2, 3",
        "is_finished": False,
    }
    db_sess = db_session.create_session()
    if not row_exists(Jobs, **JOB):
        db_sess.add(Jobs(**JOB))
        db_sess.commit()


def main():
    db_session.global_init(DB_PATH)

    register_colonists()
    create_initial_job()

    app.run()


if __name__ == "__main__":
    main()
