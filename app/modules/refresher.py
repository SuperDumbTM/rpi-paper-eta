from io import BytesIO
import logging
import requests
from app import models, translation
from app.modules import image as eimage


def generate_image(
    app_config: models.Configuration,
    bookmarks: list[models.EtaConfig],
    generator: eimage.eta_image.EtaImageGenerator
):
    try:
        etas = []
        for bm in bookmarks:
            res = requests.get(
                f'{app_config.url}'
                f'/{bm.company.value}/{bm.route}/{bm.direction.value}/etas',
                params={
                    'service_type': bm.service_type,
                    'lang': bm.lang,
                    'stop': bm.stop_code}
            ).json()

            logo = (BytesIO(requests.get('{0}{1}'.format(app_config.url,
                                                         res['data'].pop(
                                                             'logo_url')
                                                         )).content
                            )
                    if res['data']['logo_url'] is not None
                    else None)

            if res['success']:
                eta = res['data'].pop('etas')
                etas.append(eimage.models.Etas(**res['data'],
                                               etas=[eimage.models.Etas.Eta(**e)
                                                     for e in eta],
                                               logo=logo,
                                               )
                            )
            else:
                res['data'].pop('etas')
                etas.append(eimage.models.ErrorEta(**res['data'],
                                                   code=res['code'],
                                                   message=str(translation.RP_CODE_TRANSL.get(
                                                       res['code'], res['message'])),
                                                   logo=logo,)
                            )
        images = generator.draw(etas)
    except requests.RequestException as e:
        logging.warning('Image generation failed with error: %s', str(e))
        images = generator.draw_error('Network Error')
    except Exception as e:
        logging.exception('Image generation failed with error: %s', str(e))
        images = generator.draw_error('Unexpected Error')
    return images
