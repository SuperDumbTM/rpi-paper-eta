import wtforms
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext

from paper_eta.src.libs import eta_img, hketa


class EpaperSettingForm(FlaskForm):
    epd_brand = wtforms.SelectField(lazy_gettext('brand'),
                                    [
                                        wtforms.validators.DataRequired(),
                                        wtforms.validators.NoneOf(["None"])],
                                    # "-" for HTMX to request /epd-models/<brand> successfully,
                                    # so that the options can be swapped out to the "empty option".
                                    choices=[("-", lazy_gettext('please_select'))] + [
                                        (b, b.title()) for b in eta_img.generator.EtaImageGeneratorFactory.brands()])  # pylint: disable=line-too-long

    epd_model = wtforms.SelectField(lazy_gettext('model'),
                                    [
                                        wtforms.validators.DataRequired()],
                                    choices=[
                                        ("", lazy_gettext('please_select'))],
                                    validate_choice=False)

    submit = wtforms.SubmitField(lazy_gettext('submit'))

    def validate_epd_model(self, field: wtforms.Field):
        if not self.epd_brand.validate(self):
            return

        choices = map(lambda c: c.__name__,
                      eta_img.generator.EtaImageGeneratorFactory.models(self.epd_brand.data))
        if field.data not in choices:
            raise wtforms.ValidationError("Not a valid choice.")


class BookmarkForm(FlaskForm):
    locale = wtforms.SelectField(lazy_gettext("language"),
                                 choices=[(l.value, lazy_gettext(l.value))
                                          for l in hketa.enums.Locale
                                          ]
                                 )

    transport = wtforms.SelectField(lazy_gettext("company"),
                                    choices=[(l.value, lazy_gettext(l.value))
                                             for l in hketa.enums.Transport
                                             ]
                                    )

    no = wtforms.SelectField(lazy_gettext("route"),
                             validate_choice=False)

    direction = wtforms.SelectField(lazy_gettext("direction"),
                                    choices=[
                                        ("", lazy_gettext('please_select'))],
                                    validate_choice=False
                                    )

    service_type = wtforms.SelectField(lazy_gettext("service_type"),
                                       choices=[
                                           ("", lazy_gettext('please_select'))],
                                       validate_choice=False
                                       )

    stop_id = wtforms.SelectField(lazy_gettext("stop"),
                                  choices=[
                                      ("", lazy_gettext('please_select'))],
                                  validate_choice=False
                                  )

    submit = wtforms.SubmitField(lazy_gettext('submit'))


class ScheduleForm(FlaskForm):
    schedule = wtforms.StringField(lazy_gettext("schedule"),
                                   render_kw={
                                       "placeholder": "Cron Expression"},
                                   validators=[wtforms.validators.DataRequired()])

    eta_format = wtforms.SelectField(lazy_gettext("eta_format"),
                                     [wtforms.validators.DataRequired()],
                                     choices=[(l.value, lazy_gettext(l.value))
                                              for l in eta_img.enums.EtaFormat
                                              ],
                                     )

    layout = wtforms.RadioField(lazy_gettext("layout"),
                                validate_choice=False)

    is_partial = wtforms.BooleanField(lazy_gettext("partial_refresh"))

    enabled = wtforms.BooleanField(lazy_gettext("enable"))

    submit = wtforms.SubmitField(lazy_gettext('submit'))
