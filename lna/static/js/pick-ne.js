
$(document).ready(function($) {
    // get ready for multiselect

    // get json data
    $.getJSON('/api/ne_list/', function (data) {
        //console.log(data);
        // array of NE's
        var multiselect_text = '';
        data.forEach(function (ne) {
            //console.log(ne.hostname + "(" + ne.ne_ip + ")");
            multiselect_text += '<option value="' + ne.id + '"' +
                    ' data-vendor="' + ne.vendor + '"' +
                    ' data-model="' + ne.model +'"' +
                '>' +
                ne.hostname + "(" + ne.ne_ip + ")" + '</option>'
        });
        // console.log(multiselect_text)
        $("#multiselect").html(multiselect_text);
    });



    // multiselect prepare form
    $('#multiselect').multiselect();


});
