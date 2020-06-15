from flask_wtf import FlaskForm

from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField

from wtforms.validators import DataRequired, ValidationError


class AnonymousForm(FlaskForm):
    ct_scan = FileField('CT Scan', validators=[DataRequired(), FileAllowed(['jpg', 'png', 'raw', 'mhd'])])

    submit = SubmitField('Upload')
    cancel = SubmitField('Cancel')

