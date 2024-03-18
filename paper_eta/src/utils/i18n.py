from typing import Optional
from flask import current_app, request


def get_locale() -> Optional[str]:
    crrt_locale = (request.cookies.get('locale')
                   or request.headers.get("X-Locale"))
    translations = [str(translation)
                    for translation in current_app.config.get('I18N', [])]

    if crrt_locale in translations:
        return crrt_locale

    return request.accept_languages.best_match(translations)
