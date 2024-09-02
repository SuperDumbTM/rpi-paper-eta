import croniter
import wtforms
from flask_babel import lazy_gettext, gettext
from flask_wtf import FlaskForm

from paper_eta.src import database
from paper_eta.src.libs import epdcon, hketa, renderer


class EpaperSettingForm(FlaskForm):
    epd_brand = wtforms.SelectField(lazy_gettext('brand'),
                                    [wtforms.validators.DataRequired(),
                                        wtforms.validators.NoneOf(["None"])],
                                    # "-" for HTMX to request /epd-models/<brand> successfully,
                                    # so that the options can be swapped out to the "empty option".
                                    choices=[("-", lazy_gettext('please_select'))] + [
                                        (b, b.title()) for b in renderer.brands()])  # pylint: disable=line-too-long

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
                                   description=lazy_gettext('dry_run_help'))

    degree = wtforms.IntegerField(lazy_gettext('rotate_degree'),
                                  default=0,
                                  description=lazy_gettext('rotate_degree_help'))

    submit = wtforms.SubmitField(lazy_gettext('submit'))

    def validate_epd_model(self, field: wtforms.Field):
        if not self.epd_brand.validate(self):
            return

        if field.data not in epdcon.models(self.epd_brand.data):
            raise wtforms.ValidationError(gettext("Not a valid choice."))


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

    bookmark_group_id = wtforms.HiddenField(filters=[lambda v: v or None])

    submit = wtforms.SubmitField(lazy_gettext('submit'))


class BookmarkGroupForm(FlaskForm):

    name = wtforms.StringField(lazy_gettext("bookmark_group_name"),
                               validators=[wtforms.validators.DataRequired()])

    submit = wtforms.SubmitField(lazy_gettext('submit'))


class ScheduleForm(FlaskForm):
    schedule = wtforms.StringField(lazy_gettext("schedule"),
                                   render_kw={
                                       "placeholder": "Cron Expression"},
                                   validators=[wtforms.validators.DataRequired()])

    bookmark_group_id = wtforms.SelectField(lazy_gettext("bookmark_group"),
                                            choices=lambda: [
                                                ("", ""), *[(g.id, g.name) for g in database.BookmarkGroup.query.all()]],
                                            validators=[
                                                wtforms.validators.Optional()],
                                            filters=[lambda v: v or None])

    eta_format = wtforms.SelectField(lazy_gettext("eta_format"),
                                     [wtforms.validators.DataRequired()],
                                     choices=[(l.value, lazy_gettext(l.value))
                                              for l in renderer.EtaFormat
                                              ],
                                     )

    layout = wtforms.RadioField(lazy_gettext("layout"),
                                validate_choice=False)

    is_partial = wtforms.BooleanField(lazy_gettext("partial_refresh"))

    partial_cycle = wtforms.IntegerField(lazy_gettext("auto_full_refresh"),
                                         default=0,
                                         validators=[
                                             wtforms.validators.NumberRange(min=0)],
                                         description=lazy_gettext("auto_full_refresh_help"))

    enabled = wtforms.BooleanField(lazy_gettext("enable"))

    submit = wtforms.SubmitField(lazy_gettext('submit'))

    def validate_schedule(self, field: wtforms.Field):
        if not croniter.croniter.is_valid(field.data):
            raise wtforms.ValidationError(gettext("invalid_cron_expression"))
