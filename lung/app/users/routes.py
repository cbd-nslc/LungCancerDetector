from bcrypt import checkpw
from flask import jsonify, render_template, redirect, request, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user

from app import db, login_manager
from app.base.models import User

from app.users import blueprint
from app.users.utils import save_picture
from app.users.forms import LoginForm, CreateAccountForm, UpdateAccountForm


## Login
@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and checkpw(form.password.data.encode('utf8'), user.password):
            login_user(user, remember=form.remember.data)

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home_blueprint.index'))

        else:
            flash('Login Unsuccessful. Please check your username and password', 'danger')

    if current_user.is_authenticated:
        flash('You are already logged in', 'info')
        return redirect(url_for('home_blueprint.index'))

    return render_template('login.html', title='Login', form=form)


## Registration
@blueprint.route('/register', methods=['GET', 'POST'])
def create_user():
    form = CreateAccountForm()

    # if form submit success, indicate "Account created for  " at "home" page
    if form.validate_on_submit():
        # create user
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        # add user to database
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to login', 'success')
        return redirect(url_for('users_blueprint.login'))

    # if already logged in, can't go to register page
    # elif current_user.is_authenticated:
    #     flash('Please log out to create a new account!', 'info')
    #     return redirect(url_for('home_blueprint.index'))

    return render_template('register.html', title='Register', form=form)


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('users_blueprint.login'))


@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def users_profile():
    form = UpdateAccountForm()

    if 'submit' in request.form:
        if form.validate_on_submit():
            if form.picture.data:

                current_user.picture = save_picture(form.picture.data)

            current_user.username = form.username.data
            current_user.email = form.email.data

            db.session.commit()
            flash('Your account has been updated!', 'success')
            return redirect(url_for('users_blueprint.users_profile'))

    if 'cancel' in request.form:
        return redirect(url_for('users_blueprint.users_profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('users_profile.html', title='Your Profile', form=form)


@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    if 'submit' not in request.form:
        flash('Please login to access this page', 'info')
    return redirect(url_for('users_blueprint.login'))


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('errors/page_403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page_404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page_500.html'), 500
