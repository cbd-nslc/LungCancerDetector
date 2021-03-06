from flask_wtf import FlaskForm

from flask_wtf.file import FileField
from wtforms import SubmitField

from wtforms.validators import DataRequired


class CTScanForm(FlaskForm):
    raw_file = FileField('RAW', validators=[DataRequired()])
    mhd_file = FileField('MHD', validators=[DataRequired()])

    submit = SubmitField('Upload')
    cancel = SubmitField('Cancel')

