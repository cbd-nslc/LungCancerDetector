from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField

from wtforms.validators import DataRequired, ValidationError


class AnonymousForm(FlaskForm):
    raw_file = FileField('RAW', validators=[DataRequired()])
    mhd_file = FileField('MHD', validators=[DataRequired()])

    submit = SubmitField('Upload')
    cancel = SubmitField('Cancel')

