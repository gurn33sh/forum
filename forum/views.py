from flask import Blueprint, render_template, redirect, flash, url_for
from flask import request, jsonify
# import database models here
from forum.models.subreddit import Subreddit
from forum.models.thread import Link, Text, ThreadUpvote, ThreadDownvote
from forum.models.comment import Comment
from forum.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flask_login import current_user, login_user, login_required, logout_user
from forum.models.user import User
from forum import bcrypt, db, app
from PIL import Image
import secrets, os


views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def homepage():
    links = Link.query.all()
    texts = Text.query.all()
    threads = links + texts

    bindings = {
        'subreddit_list': Subreddit.query.all(),
        'threads': sorted(threads, key=lambda x: x.get_score(), reverse=True)
    }
    return render_template('index.html', **bindings)

@views_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.homepage'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            #next_page = request.args.get('next')
            return redirect(url_for('views.homepage'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@views_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('views.homepage'))

@views_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('views.login'))
    return render_template('register.html', title='Register', form=form)

def save_picture(form_picture):
    print('gggggggggg',form_picture)
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    #p = url_for('static', filename='profile_pics')
    picture_path = os.path.join(app.root_path,'static/profile_pics', picture_fn)
    form_picture.save(picture_path)

    output_size = (200, 200)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@views_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('views.account'))
    elif request.method == 'GET':
        form.username.data = current_user.name
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

@views_bp.route('/r/<string:sub_name>')
def subreddit(sub_name):
    # get subreddit
    sub = Subreddit.query.filter_by(name=sub_name).first()
    links = sub.links.all()
    texts = sub.texts.all()

    threads = links + texts

    bindings = {
        'subreddit_list': Subreddit.query.all(),
        'sub': sub,
        'threads': sorted(threads, key=lambda x: x.get_score(), reverse=True)
    }

    return render_template('subreddit.html', **bindings)


@views_bp.route('/r/<string:sub_name>/submit', methods=['POST', 'GET'])
def subreddit_submit(sub_name):
    # get subreddit
    sub = Subreddit.query.filter_by(name=sub_name).first()

    if request.method == 'POST':
        # handle form data here
        data = request.form
        if data['type'] == 'linkOption':
            Link(
                title=data['title'],
                link=data['url'],
                subreddit_id=sub.id,
                user_id=2
            ).save()
        else:
            Text(
                title=data['title'],
                text=data['text'],
                subreddit_id=sub.id,
                user_id=2
            ).save()

        return redirect(f'/r/{sub.name}')

    bindings = {
        'sub': sub,
        'subreddit_list': Subreddit.query.all(),
    }

    return render_template('submit.html', **bindings)


@views_bp.route('/link/<int:id>')
def link_view(id):
    # get the link by id
    link = Link.query.get(id)

    bindings = {
        'link': link,
        'sub': link.subreddit,
        'subreddit_list': Subreddit.query.all(),
        'comments': link.comments.all(),
    }

    return render_template('link.html', **bindings)


@views_bp.route('/link/<int:id>/reply', methods=['POST'])
def reply_link(id):
    data = request.form

    Comment(
        content=data['content'],
        user_id=2,
        link_id=id
    ).save()

    return redirect(f'/link/{id}')


@views_bp.route('/text/<int:id>')
def text_view(id):
    # get the link by id
    text = Text.query.get(id)

    bindings = {
        'text': text,
        'sub': text.subreddit,
        'subreddit_list': Subreddit.query.all(),
        'comments': text.comments.all(),
    }

    return render_template('text.html', **bindings)


@views_bp.route('/text/<int:id>/reply', methods=['POST'])
def reply_text(id):
    data = request.form

    Comment(
        content=data['content'],
        user_id=2,
        text_id=id
    ).save()

    return redirect(f'/text/{id}')


@views_bp.route('/comment/<int:id>/reply', methods=['GET', 'POST'])
def reply_comment(id):
    comment = Comment.query.get(id)
    print(comment)

    if request.method == 'POST':
        data = request.form
        Comment(
            content=data['content'],
            user_id=2,
            comment_id=id
        ).save()

        while comment.parent and comment.id:
            comment = comment.parent

        if comment.link_id:
            return redirect(f'/link/{comment.link_id}')
        else:
            return redirect(f'/text/{comment.text_id}')

    bindings = {
        'comment': comment,
        'subreddit_list': Subreddit.query.all(),
    }

    return render_template('comment.html', **bindings)


@views_bp.route('/link/<int:id>/upvote', methods=['POST'])
@login_required
def upvote_link(id):
    data = request.json
    ThreadUpvote(user_id=data['user_id'], link_id=id).save()
    return jsonify({'message': 'upvoted successfully'})


@views_bp.route('/text/<int:id>/upvote', methods=['POST'])
def upvote_text(id):
    data = request.json
    ThreadUpvote(user_id=data['user_id'], text_id=id).save()
    return jsonify({'message': 'upvoted successfully'})


@views_bp.route('/link/<int:id>/downvote', methods=['POST'])
@login_required
def downvote_link(id):
    data = request.json
    ThreadDownvote(user_id=data['user_id'], link_id=id).save()
    return jsonify({'message': 'downvoted successfully'})


@views_bp.route('/text/<int:id>/downvote', methods=['POST'])
def downvote_text(id):
    data = request.json
    ThreadDownvote(user_id=data['user_id'], text_id=id).save()
    return jsonify({'message': 'downvoted successfully'})
