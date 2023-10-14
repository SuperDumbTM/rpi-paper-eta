from typing import Optional
import requests
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import (HiddenField, PasswordField, SelectField, StringField,
                     SubmitField)
from wtforms.validators import AnyOf, DataRequired, NoneOf

from app import enums
from app.config import site_data


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

    @staticmethod
    def route_choices(company: str) -> list[tuple[str]]:
        routes: dict[str, dict] = (
            requests.get(
                f"{site_data.ApiServerSetting().url}/{company}/routes")
            .json()['data']['routes']
        )
        return [(route['name'], route['name']) for route in routes.values()]

    @staticmethod
    def direction_choices(company: str,
                          route: str) -> list[tuple[str]]:
        details: dict[str, dict] = (
            requests.get(
                f"{site_data.ApiServerSetting().url}/{company}/{route.upper()}")
            .json()['data']
        )

        directions = []
        if details['inbound']:
            directions.append((lazy_gettext("inbound"), "inbound"))
        if details['outbound']:
            directions.append((lazy_gettext("outbound"), "outbound"))
        return directions

    @staticmethod
    def type_choices(company: str,
                     route: str,
                     direction: str) -> list[tuple[str]]:
        details: dict[str, dict] = (
            requests.get(
                f"{site_data.ApiServerSetting().url}/{company}/{route}")
            .json()['data']
        )

        return [(t['service_type'], f"{t['service_type']} ({t['orig']['name']['tc']} -> {t['dest']['name']['tc']})")
                for t in details[direction]]

    @staticmethod
    def stop_choices(company: str,
                     route: str,
                     direction: str,
                     service_type: str) -> list[tuple[str]]:
        stops: dict[str, dict] = (
            requests.get(
                f"{site_data.ApiServerSetting().url}/{company}/{route.upper()}/{direction}/{service_type}/stops")
            .json()['data']
        )

        return [(stop['seq'], f"{stop['seq']:02}. {stop['name']['tc']}")
                for stop in stops['stops']]
