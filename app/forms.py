from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Regexp, EqualTo


class ApiServerForm(FlaskForm):
    url = StringField(
        "Server URL",
        validators=[DataRequired(),])
    # Reference: https://stackoverflow.com/a/53107448/17789727
    username = StringField("Username")
    password = PasswordField("Password")
    submit = SubmitField()
