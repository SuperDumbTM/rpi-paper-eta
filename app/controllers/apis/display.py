import requests
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_babel import force_locale
from app import models, translation
from app.config import site_data
from app.modules import image

bp = Blueprint('api_display',
               __name__,
               template_folder="../templates",
               url_prefix="/api/display")


@bp.route("/refresh")
def refresh():
    import os

    img = image.waveshare.epd3in7.Epd3in7EtaImage(
        image.enums.EtaMode.MIXED, "6-row-3-eta")
    api_server = site_data.ApiServerSetting()
    bookmarks = site_data.BookmarkList()

    try:
        etas = []
        for bm in bookmarks:
            bm: models.EtaConfig
            response = requests.get(
                f"{api_server.url}/{bm.company.value}/{bm.route}/{bm.direction.value}/etas",
                {'service_type': bm.service_type, 'stop': bm.stop_code, 'lang': bm.lang}).json()

            with force_locale('zh_Hant_HK' if bm.lang == 'tc' else bm.lang):
                if response['success']:
                    etas_ = response['data'].pop('etas')
                    etas.append(
                        image.models.Etas(**response['data'],
                                          etas=[image.models.Etas.Eta(**eta) for eta in etas_])
                    )
                else:
                    response.pop('message')
                    etas.append(
                        image.models.ErrorEta(**response['data'],
                                              code=response['code'],
                                              message=str(translation.RP_CODE_TRANSL.get(response['code'], "Error")))
                    )
    except Exception as e:
        pass

    img.write_images(os.path.dirname(__file__), img.draw(etas))

    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {}
    })
