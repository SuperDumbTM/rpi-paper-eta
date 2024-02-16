from flask_babel import lazy_gettext

RP_CODE_TRANSL = {
    "eta-end-of-service": lazy_gettext("eta-end-of-service"),
    "eta-error-response": lazy_gettext("eta-error-response"),
    "eta-api-error": lazy_gettext("eta-api-error"),
    "eta-no-entry": lazy_gettext("eta-no-entry"),
    "eta-stop-closure": lazy_gettext("eta-stop-closure"),
    "eta-abnormal-service": lazy_gettext("eta-abnormal-service"),
    "route-not-exist": lazy_gettext("route-not-exist"),
    "stop-not-exist": lazy_gettext("stop-not-exist")
}

# ETA companies
lazy_gettext('kmb')
lazy_gettext('mtr_lrt')
lazy_gettext('mtr_train')
lazy_gettext('mtr_bus')
lazy_gettext('ctb')
lazy_gettext('nlb')

# ETA language
lazy_gettext('en')
lazy_gettext('tc')
lazy_gettext('default')

# ETA Type
lazy_gettext('mixed')
