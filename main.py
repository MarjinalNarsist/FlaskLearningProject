import requests
import wtforms
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField
from datetime import datetime
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from requests import request
# from libgravatar import Gravatar
from flask_gravatar import Gravatar



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# Avatar for Comments
gravatar = Gravatar(app, size=100, rating="g", default="retro", force_default=False, use_ssl=False, base_url=None)


# User Database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts= relationship("BlogPost", back_populates="author")
    comments= relationship("Comments", back_populates="author")

    def __repr__(self):
        return f"User(id={self.id!r}, email={self.email!r}, password={self.password!r}, name={self.name!r})"


# Blog Post Database
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    author= relationship("User", back_populates="posts")
    img_url = db.Column(db.String(250), nullable=False)
    comments= db.relationship('Comments', back_populates='post')

    def __repr__(self):
        return f"BlogPost(id={self.id!r}, title={self.title!r}, subtitle={self.subtitle!r}, date={self.date!r}, " \
               f"body={self.body!r}, author={self.author!r}, author_id={self.author_id!r}, img_url={self.img_url!r})"


# Comment Database
class Comments(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    comment= db.Column(db.Text, nullable=False)
    post_id= db.Column(db.Integer, db.ForeignKey('blog_post.id'))
    post= relationship("BlogPost", back_populates="comments")
    author_id=db.Column(db.Integer, db.ForeignKey('user.id'))
    author = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"Comments(id={self.id}, comment={self.comment}, post_id={self.post_id})"


# db.create_all()
# Post Form
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired()])
    body = CKEditorField('Body', validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# Register and Login Form
class UserForm(FlaskForm):
    name= StringField("Name")
    e_mail= StringField("E-mail", validators=[DataRequired()])
    password= PasswordField("Password", validators=[DataRequired()])
    submit= SubmitField("Submit")


# Comment Form
class CommentForm(FlaskForm):
    comment= CKEditorField('Comment', validators=[DataRequired()])
    submit= SubmitField("Comment")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Main Page
@app.route('/', methods=["GET", "POST"])
def get_all_posts():
    posts= BlogPost.query.all()
    page_title="Deniz's Blog"
    page_subtitle="Welcome to my world!"
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated,
                           page_title=page_title, page_subtitle=page_subtitle, user=current_user)


# Selected Post Page
@app.route("/post/<int:index>", methods=["GET", "POST"])
def show_post(index):
    form=CommentForm()
    comments= Comments.query.all()
    requested_post = BlogPost.query.get(index)
    page_title=requested_post.title
    page_subtitle=f"{requested_post.subtitle}\nPosted by {requested_post.author.name} on " \
                  f"{requested_post.date}"
    random_comment= Comments.query.get(3)
    print(random_comment.author.email)
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment= Comments(comment=form.comment.data, post_id=index, author_id=current_user.id)
            db.session.add(new_comment)
            db.session.commit()
        else:
            flash("Please login or register to comment.")
            return redirect(url_for("login"))
    return render_template(
        "post.html", post=requested_post, logged_in=current_user.is_authenticated,
        page_title=page_title, page_subtitle=page_subtitle, user=current_user, form=form, comments=comments
    )


# About Page
@app.route("/about", methods=["GET", "POST"])
def about():
    page_title="About Me"
    page_subtitle="Little bit me!"
    return render_template("about.html", logged_in=current_user.is_authenticated, page_title=page_title,
                           page_subtitle=page_subtitle)


# Contact Page
@app.route("/contact", methods=["GET", "POST"])
def contact():
    page_title="Contact"
    page_subtitle="Send a word!"
    return render_template("contact.html", logged_in=current_user.is_authenticated, page_title=page_title,
                           page_subtitle=page_subtitle)


# New Post Creation Page
@app.route("/make_post", methods=["GET", "POST"])
@login_required
def make_post():
    form=CreatePostForm()
    page_title="New Post"
    page_subtitle="You're going to make a great blog post!"
    if form.validate_on_submit():
        date=datetime.now()
        new_post= BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.strftime("%A-%m-%Y"),
            body=form.body.data,
            author_id=current_user.id,
            img_url=form.img_url.data
        )
        db.session.add(new_post)
        db.session.commit()
    return render_template("make-post.html", form=form, page_title=page_title, page_subtitle=page_subtitle,
                           logged_in=current_user.is_authenticated)


# Post Editing Page (Uses same page with Post Creation Page)
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post= BlogPost.query.get(post_id)
    form=CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        author=post.author,
        img_url=post.img_url,
        body=post.body
    )
    page_title="Edit Post"
    page_subtitle="Lets get this correct this time!"
    if form.validate_on_submit():
        print("Validation Success!")
        post.title=form.title.data
        post.subtitle=form.subtitle.data
        post.body=form.body.data
        post.img_url=form.img_url.data
        db.session.commit()
        return redirect(url_for('show_post', index=post_id))
    return render_template("make-post.html", form=form, page_title=page_title, page_subtitle=page_subtitle,
                           logged_in=current_user.is_authenticated)


# Post Delete Option (Does not contain new page, redirects main page)
@app.route('/delete/<int:post_id>', methods=["GET", "POST"])
@login_required
def delete_post(post_id):
    post= BlogPost.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    page_title="Register"
    page_subtitle="Welcome!"
    form=UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.e_mail.data).first() is None:
            hash_pass= generate_password_hash(password=form.password.data, method="pbkdf2:sha256", salt_length=8)
            new_user= User(
                name=form.name.data,
                email=form.e_mail.data,
                password=hash_pass
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("get_all_posts"))
        else:
            flash("E-mail is already registered!")
            return redirect(url_for("login"))

    return render_template("register.html", page_title=page_title, page_subtitle=page_subtitle,
                           form=form, logged_in=current_user.is_authenticated)


# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    page_title="Login"
    page_subtitle="Hello Again!"
    form= UserForm()
    if form.validate_on_submit():
        user_to_login= User.query.filter_by(email=form.e_mail.data).first()
        if check_password_hash(pwhash=user_to_login.password, password=form.password.data):
            login_user(user_to_login)
            flash("Login Successfully!")
            return redirect(url_for("get_all_posts"))
        else:
            flash("Password is Wrong!")
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated,
                           page_title=page_title, page_subtitle=page_subtitle)


@app.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("get_all_posts"))


if __name__ == "__main__":
    app.run(port=5000)