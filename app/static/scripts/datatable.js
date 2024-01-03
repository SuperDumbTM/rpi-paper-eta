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
    if (!$(this).data('href')) return


    if ($(this).data('href-method') === "") {
        window.location.href = $(this).data('href')
    }

    $.ajax({
        method: $(this).data('href-method'),
        url: $(this).data('href'),
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify($(this).data('href-payload')),
        dataType: "json",
        success: function (res) {
            alertify.success(res.message)
            datatable.ajax.reload()
        },
        error: function (xhr, status, error) {
            if (error) {
                alertify.error(error)
            }

            if (isJSON(xhr.responseText)) {
                let = json = $.parseJSON(xhr.responseText)
                if (json.message) {
                    alertify.error(json.message)
                }
            }
        },
    })
})