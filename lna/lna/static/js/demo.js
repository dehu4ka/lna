/**
 * Created by dehu4 on 18.06.2017.
 */

var socket = new WebSocket("ws://" + window.location.host + "/chat/");

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
