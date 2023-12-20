function showLoading() {
    $("#loading-overlay").show()
}

function hideLoading() {
    $("#loading-overlay").hide()
}

function formToJson(form){
    // reference: https://stackoverflow.com/a/11339012/17789727
    var unindexed_array = form.serializeArray();
    var indexed_array = {};

    $.map(unindexed_array, function(n, i){
        indexed_array[n['name']] = n['value'];
    });

    // turn checkbox values into boolean
    // reference: https://stackoverflow.com/a/7335358/17789727
    $("input:checkbox", form).each(function(){
        indexed_array[this.name] = this.checked;
    });

    return indexed_array;
}