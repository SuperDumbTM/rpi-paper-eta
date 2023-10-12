from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, SearchField
from wtforms.validators import DataRequired, NoneOf, AnyOf

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
                          choices=([("", "-----")] +
                                   [(v.value, v.name) for v in enums.EtaCompany]),
                          validators=[DataRequired(), AnyOf([v for v in enums.EtaCompany])])
    name = StringField("Route Name",
                       validators=[DataRequired()])
    direction = SelectField("Direction",
                            coerce=str,
                            choices=[("", "-----")],
                            validate_choice=False,
                            validators=[DataRequired()])
    service_type = SelectField("Service Type",
                               coerce=str,
                               choices=[("", "-----")],
                               validate_choice=False,
                               validators=[NoneOf(["", "None"])])
    stop = SelectField("Stop",
                       coerce=str,
                       choices=[(None, "-----")],
                       validate_choice=False,
                       validators=[DataRequired(), NoneOf(["", "None"])])
    lang = SelectField("Language",
                       coerce=str,
                       choices=[(v.value, v.name) for v in enums.Locale],
                       validators=[DataRequired(), AnyOf([v for v in enums.Locale])])
    submit = SubmitField()
