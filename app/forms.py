from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Regexp


class ApiServerForm(FlaskForm):
    url = StringField(
        "Server URL",
        validators=[
            DataRequired(),
            Regexp(r"^(http|https):\/\/[\w.\-]+(\.[\w.\-]+)+.*$'",
                   0,
                   'URL must be a valid link')
        ])
    # Reference: https://stackoverflow.com/a/53107448/17789727
    username = StringField("Username")
    password = PasswordField("Password")
    submit = SubmitField()
