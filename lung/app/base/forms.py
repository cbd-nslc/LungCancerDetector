from flask_wtf import FlaskForm

from wtforms import SubmitField, MultipleFileField

from wtforms.validators import DataRequired


class CTScanFormUI(FlaskForm):
    file = MultipleFileField('File', validators=[DataRequired()])
    submit = SubmitField('Upload')
