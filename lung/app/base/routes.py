from bcrypt import checkpw
from flask import jsonify, render_template, redirect, request, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user

from app import db, login_manager
from app.base import blueprint
from app.base.forms import LoginForm, CreateAccountForm
from app.base.models import User


# default page
@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))


@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')


@blueprint.route('/fixed_<template>')
@login_required
def route_fixed_template(template):
    return render_template(f'fixed/fixed_{template}.html')


@blueprint.route('/page_<error>')
def route_errors(error):
    return render_template(f'errors/page_{error}.html')


# @blueprint.route('/cac', methods=['GET', 'POST'])
# def test():
#     return redirect(url_for('home_blueprint.index'))


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

    # elif current_user.is_authenticated:
    #     return redirect(url_for('home_blueprint.index'))

    return render_template('login/login.html', title='Login', form=form)


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
        return redirect(url_for('base_blueprint.login'))

    # if already logged in, can't go to register page
    # if current_user.is_authenticated:
    #     flash('Please log out to create a new account!', 'info')
    #     return redirect(url_for('home_blueprint.index'))

    return render_template('login/register.html', title='Register', form=form)


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('base_blueprint.login'))


@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


# Errors

# @login_manager.unauthorized_handler
# def unauthorized_handler():
#     return redirect()


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('errors/page_403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page_404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page_500.html'), 500
