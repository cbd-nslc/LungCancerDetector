from flask import Blueprint

blueprint = Blueprint(
    'main',
    __name__,
    url_prefix='/main',
    template_folder='templates',
)