let _loadingTimerId;

function showLoading(delay = 0) {
    _loadingTimerId = setTimeout(() => {
        document.getElementById('loading-overlay').style.display = 'block';
    }, delay);
}

function hideLoading(delay = 0) {
    clearTimeout(_loadingTimerId);

    setTimeout(() => {
        document.getElementById('loading-overlay').style.display = 'none';
    }, delay);
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

function isNumeric(n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
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