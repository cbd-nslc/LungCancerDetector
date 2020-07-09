import os

from flask import Flask, url_for
from flask_login import LoginManager
from flask_mail import Mail

from flask_sqlalchemy import SQLAlchemy
from importlib import import_module
from logging import basicConfig, DEBUG, getLogger, StreamHandler
from os import path

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()



def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    for module_name in ['base', 'home', 'patients', 'users']:
        module = import_module(f'app.{module_name}.routes')
        app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()


def configure_logs(app):
    basicConfig(filename='error.log', level=DEBUG)
    logger = getLogger()
    logger.addHandler(StreamHandler())


def apply_themes(app):
    """
    Add support for themes.

    If DEFAULT_THEME is set then all calls to
      url_for('static', filename='')
      will modfify the url to include the theme name

    The theme parameter can be set directly in url_for as well:
      ex. url_for('static', filename='', theme='')

    If the file cannot be found in the /static/<theme>/ lcation then
      the url will not be modified and the file is expected to be
      in the default /static/ location
    """

    @app.context_processor
    def override_url_for():
        return dict(url_for=_generate_url_for_theme)

    def _generate_url_for_theme(endpoint, **values):
        if endpoint.endswith('static'):
            themename = values.get('theme', None) or \
                        app.config.get('DEFAULT_THEME', None)
            if themename:
                theme_file = "{}/{}".format(themename, values.get('filename', ''))
                if path.isfile(path.join(app.static_folder, theme_file)):
                    values['filename'] = theme_file
        return url_for(endpoint, **values)

    @app.after_request
    def add_header(response):
        response.cache_control.max_age = 0
        return response

def create_app(config, selenium=False):
    app = Flask(__name__, static_folder=path.join('base', 'static'))
    UPLOAD_FOLDER = path.join(app.static_folder, 'uploaded_ct_scan')

    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


    app.config.from_object(config)

    if selenium:
        app.config['LOGIN_DISABLED'] = True

    from app.base import models

    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    configure_logs(app)
    apply_themes(app)
    return app
