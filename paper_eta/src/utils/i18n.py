from typing import Optional

from flask import request

from .. import extensions


def get_locale() -> Optional[str]:
    crrt_locale = (request.cookies.get('locale')
                   or request.headers.get("X-Locale"))
    translations = [str(translation)
                    for translation in extensions.babel.list_translations()]

    if crrt_locale in translations:
        return crrt_locale

    return request.accept_languages.best_match(translations)
