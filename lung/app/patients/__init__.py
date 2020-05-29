from flask import Blueprint

blueprint = Blueprint(
    'patients_blueprint',
    __name__,
    url_prefix='/patients',
    template_folder='templates',
    static_folder='static'
)
