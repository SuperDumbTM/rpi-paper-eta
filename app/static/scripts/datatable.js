$(document).on("click", "td button.dt-action", function (event) {
    if ($(this).data('href')) {
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
                alertify.error("Failed to delete.")
            }
        })
    }
})