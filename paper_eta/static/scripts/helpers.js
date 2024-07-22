function showLoading() {
    $("#loading-overlay").show()
}

function hideLoading() {
    $("#loading-overlay").hide()
}

function formToJson(form) {
    // reference: https://stackoverflow.com/a/11339012/17789727
    var unindexed_array = form.serializeArray();
    var indexed_array = {};

    $.map(unindexed_array, function (n, i) {
        indexed_array[n['name']] = n['value'];
    });

    // turn checkbox values into boolean
    // reference: https://stackoverflow.com/a/7335358/17789727
    $("input:checkbox", form).each(function () {
        indexed_array[this.name] = this.checked;
    });

    return indexed_array;
}

function titleCase(str) {
    // reference: https://stackoverflow.com/a/40111894/17789727
    return str.toLowerCase().replace(/\b\w/g, s => s.toUpperCase());
}

function isJSON(str) {
    // reference: https://stackoverflow.com/a/32278428/17789727
    try {
        return (JSON.parse(str) && !!str);
    } catch (e) {
        return false;
    }
}

function autoJsonFrom(form, settings = {}) {
    form.submit(function(e) {
        e.preventDefault()

        $.ajax({
            url: settings.url || form.attr('action'),
            type: settings.type || form.attr('method'),
            data: JSON.stringify(formToJson(form)),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            error: settings.error || function (xhr, status, error) {
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
            success: settings.success || function (res) {
                if (res.success) {
                    alertify.success(res.message)
                } else {
                    alertify.error(res.message)
                }
            }
        })
    })
}