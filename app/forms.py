from typing import Optional
import requests
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import (HiddenField, PasswordField, SelectField, StringField,
                     SubmitField, RadioField)
from wtforms.validators import AnyOf, DataRequired, NoneOf

from app import enums
from app.config import site_data
from app.modules.image.enums import EtaMode
from app.modules.image.eta_image import EtaImageGeneratorFactory


class ApiServerForm(FlaskForm):
    """HTML Form for editing the details of the API server.
    """
    url = StringField(
        "Server URL",
        validators=[DataRequired()])
    # Reference: https://stackoverflow.com/a/53107448/17789727
    username = StringField("Username")
    password = PasswordField("Password")
    submit = SubmitField()


class BookmarkForm(FlaskForm):
    """HTML Form for creating/editing an ETA bookmark.
    """
    company = SelectField("Company",
                          choices=([("", "-----")] +
                                   [(v.value, v.name) for v in enums.EtaCompany]),
                          validators=[DataRequired(), AnyOf([v for v in enums.EtaCompany])])
    route = StringField("Route Name",
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
    stop_code = SelectField("Stop",
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

        return [(stop['stop_code'], f"{stop['seq']:02}. {stop['name']['tc']}")
                for stop in stops['stops']]


class EpaperForm(FlaskForm):
    brand = SelectField(f"{lazy_gettext('E-Paper')} {lazy_gettext('brand').title()}",
                        choices=([("", "-----")] +
                                 [(b, b.title()) for b in EtaImageGeneratorFactory.brands()]),
                        validators=[DataRequired(),
                                    AnyOf([v for v in EtaImageGeneratorFactory.brands()])])
    format = SelectField(lazy_gettext("ETA Display Format"),
                         choices=([("", "-----")] +
                                  [(m.value, m.name.title().replace('_', ' ')) for m in EtaMode]),
                         validators=[DataRequired(),
                                     AnyOf([v for v in EtaImageGeneratorFactory.brands()])])
    model = HiddenField(lazy_gettext("Model"),
                        validators=[NoneOf(["", "None"])])
    layout = HiddenField(validators=[NoneOf(["", "None"])])
    submit = SubmitField()
