from dataclasses import asdict
import os
import requests
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)

from app import enums, forms, models, utils
from app.config import site_data

bp = Blueprint('api_display',
               __name__,
               template_folder="../templates",
               url_prefix="/api/display")


@bp.route("/refresh")
def refresh():
    from app.modules import image

    api_server = site_data.ApiServerSetting()
    bookmarks = site_data.BookmarkList()

    etas = []

    for bm in bookmarks:
        bm: models.EtaConfig
        response = requests.get(
            f"{api_server.url}/{bm.company.value}/{bm.route}/{bm.direction.value}/etas",
            {'service_type': bm.service_type, 'stop': bm.stop_code}).json()

        etas_ = response['data'].pop('etas')
        etas.append(image.models.Etas(**response['data'], etas=[
            image.models.Etas.Eta(**eta) for eta in etas_
        ]))

    img = image.waveshare.epd3in7.Epd3in7EtaImage(
        image.enums.EtaMode.MIXED, "6-row-3-eta")
    img.write_images(os.path.dirname(__file__), img.draw(etas))

    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {}
    })
