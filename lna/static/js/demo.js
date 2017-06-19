/**
 * Created by dehu4 on 18.06.2017.
 */

var socket = new WebSocket("ws://" + window.location.host + "/chat/hui");

socket.onopen = function () {
    $('#status').html('websocket connected')
};

socket.onclose = function (event) {
    if (event.wasClean) {
        $('#status').html('Clean disconnect')
    } else {
        $('#status').html('Disconnected!')
    }
};

socket.onmessage = function (event) {
    html2 = $('#status').html();
    str = "<br>message:" + event.data;
    $('#status').html(html+str);
};
