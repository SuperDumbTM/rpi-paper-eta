from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request)

from app import forms, enums
from app.config import site_data

bp = Blueprint('configuration',
               __name__,
               template_folder="../templates",
               url_prefix="/configuration")


@bp.route('/')
def index():
    return render_template("configuration/index.jinja")


@bp.route('/api-server', methods=['GET', 'POST'])
def api_server():
    setting = site_data.ApiServerSetting()
    form = forms.ApiServerForm()

    if form.validate_on_submit():
        try:
            setting.clear().update(url=form.url.data,
                                   username=form.username.data,
                                   password=form.password.data
                                   ).persist()
        except Exception:
            flash("Update failed due to internal errors.",
                  enums.FlashCategory.error)
        else:
            flash("Updated.", enums.FlashCategory.success)
    return render_template("configuration/api_server.jinja",
                           api_url=setting.url,
                           api_username=setting.username,
                           api_password=setting.password,
                           form=form
                           )
