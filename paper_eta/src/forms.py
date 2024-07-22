import wtforms
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext

from paper_eta.src.libs import eta_img, hketa


class EpaperSettingForm(FlaskForm):
    epd_brand = wtforms.SelectField(lazy_gettext('brand'),
                                    # "-" for HTMX to request /epd-models/<brand> successfully,
                                    # so that the options can be swapped out to the "empty option".
                                    choices=[("-", lazy_gettext('please_select'))] + [
                                        (b, b.title()) for b in eta_img.generator.EtaImageGeneratorFactory.brands()],
                                    validators=[
                                        wtforms.validators.DataRequired(),
                                        wtforms.validators.NoneOf(["None"])])

    epd_model = wtforms.SelectField(lazy_gettext('model'),
                                    choices=[
                                        ("", lazy_gettext('please_select'))],
                                    validate_choice=True,
                                    validators=[
                                        wtforms.validators.DataRequired()])

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
