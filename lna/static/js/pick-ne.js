
$(document).ready(function($) {
    // get ready for multiselect

    var multiselect = $('#multiselect');

    // get json data about NE list and populate select
    function get_and_place_NE() {
        $.getJSON('/api/ne_list/', function (data) {
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
    $.getJSON('/api/vendors/', function (data) {
        var vendors_text = '<option value="All">All</option>';
        data.forEach(function (vendor) {
            vendors_text += '<option value="' + vendor.vendor +
                    '">' + vendor.vendor + '</option>'
        });
        $('#vendors_select').html(vendors_text)
    });

    // multiselect prepare form
    multiselect.multiselect();


    $('#vendors_select').change(function () {
        //console.log('was changed to ' + this.value)
        var filter = $(this).val();
        filterSelect(filter)
    });

    function filterSelect(value) {
        console.log('filter select - ' + value);
        var list = $("#multiselect option");
        if (value === 'All') {
            //list.show();
            get_and_place_NE()
        } else {
            list.hide();
            $(".multiselect").find("option[data-vendor*=" + value + "]").each(function (i) {
                $(this).show();
            });
        }

    }


});
