from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, SearchField
from wtforms.validators import DataRequired, Regexp, EqualTo

from app import enums


class ApiServerForm(FlaskForm):
    url = StringField(
        "Server URL",
        validators=[DataRequired()])
    # Reference: https://stackoverflow.com/a/53107448/17789727
    username = StringField("Username")
    password = PasswordField("Password")
    submit = SubmitField()


class EtaForm(FlaskForm):
    company = SelectField("Company",
                          choices=[v.value for v in enums.EtaCompany],
                          validators=[DataRequired()])
    name = StringField("Route Name")
    direction = SelectField("Direction",
                            choices=[v.value for v in enums.RouteDirection],
                            validators=[DataRequired()])
    service_type = SelectField("Service Type")
    stop = StringField("Stop",
                       validators=[DataRequired()])
    lang = SelectField("Language",
                       choices=[v.value for v in enums.Locale],
                       validators=[DataRequired()])
    submit = SubmitField()
