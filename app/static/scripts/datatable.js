const DT_LANG_URLS = {
    'en': '//cdn.datatables.net/plug-ins/1.13.7/i18n/en-GB.json',
    'zh_Hant_HK': '//cdn.datatables.net/plug-ins/1.13.7/i18n/zh-HANT.json',
    'zh_Hant': '//cdn.datatables.net/plug-ins/1.13.7/i18n/zh-HANT.json',
    'zh_Hant_TW': '//cdn.datatables.net/plug-ins/1.13.7/i18n/zh-HANT.json',
    'zh_Hans': '//cdn.datatables.net/plug-ins/1.13.7/i18n/zh.json',
    'zh_Hans_CN': '//cdn.datatables.net/plug-ins/1.13.7/i18n/zh.json'
}

// set datatable default settings
// reference: https://datatables.net/forums/discussion/68947/localize-settings-global
$.extend(true, $.fn.dataTable.defaults, {
    language: {
        'url': DT_LANG_URLS[Cookies.get('locale') || 'en']
    }
})

$(document).on("click", "td button.dt-action", function (e) {
    var btn = $(this)
    if (!btn.data('href')) return


    if (btn.data('href-method') === "") {
        window.location.href = btn.data('href')
    }

    $.ajax({
        method: btn.data('href-method'),
        url: btn.data('href'),
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify(btn.data('href-payload')),
        beforeSend: btn.data('busy-load') ? () => $.busyLoadFull('show') : null,
        complete: btn.data('busy-load') ? () => $.busyLoadFull('hide') : null,
        dataType: "json",
        success: function (res) {
            if (res.success) {
                alertify.success(res.message)
            } else {
                alertify.error(res.message)
            }

            if (btn.data('200-reload') || true)
                datatable.ajax.reload()
        }
    })
})