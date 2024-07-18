import wtforms
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext

from paper_eta.src.libs import eta_img


class EpaperSettingForm(FlaskForm):
    epd_brand = wtforms.SelectField(lazy_gettext('brand'),
                                    # "-" for HTMX to request /epd-models/<brand> successfully,
                                    # so that the options can be swapped out to the "empty option".
                                    choices=[("-", lazy_gettext('--- Please Select ---'))] + [
                                        (b, b.title()) for b in eta_img.generator.EtaImageGeneratorFactory.brands()],
                                    validators=[
                                        wtforms.validators.DataRequired(),
                                        wtforms.validators.NoneOf(["None"])])

    epd_model = wtforms.SelectField(lazy_gettext('model'),
                                    choices=[
                                        ("", lazy_gettext('--- Please Select ---'))],
                                    validate_choice=False,
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
