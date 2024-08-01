import wtforms
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm

from paper_eta.src.libs import hketa, imgen


class EpaperSettingForm(FlaskForm):
    epd_brand = wtforms.SelectField(lazy_gettext('brand'),
                                    [wtforms.validators.DataRequired(),
                                        wtforms.validators.NoneOf(["None"])],
                                    # "-" for HTMX to request /epd-models/<brand> successfully,
                                    # so that the options can be swapped out to the "empty option".
                                    choices=[("-", lazy_gettext('please_select'))] + [
                                        (b, b.title()) for b in imgen.brands()])  # pylint: disable=line-too-long

    epd_model = wtforms.SelectField(lazy_gettext('model'),
                                    [
                                        wtforms.validators.DataRequired()],
                                    choices=[
                                        ("", lazy_gettext('please_select'))],
                                    validate_choice=False)

    eta_locale = wtforms.SelectField(lazy_gettext('language'),
                                     [wtforms.validators.DataRequired()],
                                     choices=[(l.value, l.text())
                                              for l in hketa.Locale],)

    dry_run = wtforms.BooleanField(lazy_gettext('dry_run'),
                                   [wtforms.validators.DataRequired()],
                                   description=lazy_gettext('dry_run_help'))

    submit = wtforms.SubmitField(lazy_gettext('submit'))

    def validate_epd_model(self, field: wtforms.Field):
        if not self.epd_brand.validate(self):
            return

        if field.data not in imgen.models(self.epd_brand.data):
            raise wtforms.ValidationError("Not a valid choice.")


class BookmarkForm(FlaskForm):

    transport = wtforms.SelectField(lazy_gettext("company"),
                                    choices=[(l.value, lazy_gettext(l.value))
                                             for l in hketa.Company]
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
                                              for l in imgen.enums.EtaFormat
                                              ],
                                     )

    layout = wtforms.RadioField(lazy_gettext("layout"),
                                validate_choice=False)

    is_partial = wtforms.BooleanField(lazy_gettext("partial_refresh"))

    enabled = wtforms.BooleanField(lazy_gettext("enable"))

    submit = wtforms.SubmitField(lazy_gettext('submit'))
