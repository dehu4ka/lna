;$(document).ready(function($) {
    // get ready for multiselect

    var multiselect = $('#multiselect');

    // get json data about NE list and populate select
    var ne_json = '';
    function get_and_place_NE() {
        $.getJSON('/api/ne_list/', function (data) {
            ne_json = data;
            // array of NE's
            var multiselect_text = '';
            data.forEach(function (ne) {
                multiselect_text += '<option value="' + ne.id + '"' +
                        ' data-vendor="' + ne.vendor + '"' +
                        ' data-model="' + ne.model +'"' +
                    '>' +
                    ne.hostname + "(" + ne.ne_ip + ")" + '</option>'
            });
            multiselect.html(multiselect_text);
        });
    }

    get_and_place_NE();

    // vendor list, get and populate select
    var vendor_json = '';
    $.getJSON('/api/vendors/', function (data) {
        vendor_json = data;
        var vendors_text = '<option value="All">All</option>';
        data.forEach(function (vendor) {
            vendors_text += '<option value="' + vendor.vendor +
                    '">' + vendor.vendor + '</option>'
        });
        $('#vendors_select').html(vendors_text)
    });

    var model_json = '';
    $.getJSON('/api/models', function (data) {
        model_json = data;
    });

    // multiselect prepare form
    multiselect.multiselect();


    function filterModelByVendor(value) {
        var filtered = $(model_json).filter(function (i, n) {
            return n.vendor === value;
        });
        var models_text = '<option value="All">All</option>';
        for (var i=0; i<filtered.length; i++){
            var f = filtered[i];
            models_text += '<option value="' + f.model + '">' + f.model + '</option>';
        }
        $('#models_select').html(models_text);
    }

    function filterNEjson(vendor, model) {
        var filtered = $(ne_json).filter(function (i, n) {
            if (vendor === 'All' && model === 'All') return true;
            if (vendor === 'All') return n.model === model;
            if (model === 'All') return n.vendor === vendor;
            return ((n.model === model) && (n.vendor === vendor));
        });
        var ne_html = '';
        for (var i=0; i < filtered.length; i++){
            var ne = filtered[i];
            ne_html += '<option value="' + ne.id + '"' +
                        ' data-vendor="' + ne.vendor + '"' +
                        ' data-model="' + ne.model +'"' +
                        '>' +
                        ne.hostname + "(" + ne.ne_ip + ")" + '</option>'
        }
        multiselect.html(ne_html);
    }

    $('#vendors_select').change(function () {
        var vendor = $('#vendors_select').val();
        var model = $('#models_select').val();
        filterModelByVendor(vendor);
        filterNEjson(vendor, model);
    });

    $('#models_select').change(function () {
        var vendor = $('#vendors_select').val();
        var model = $('#models_select').val();
        filterNEjson(vendor, model);
    });


});
