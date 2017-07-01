function render_message(msg, msg_class) {
    msg_html = '<div class="alert alert-' + msg_class + ' alert-dismissible fade show" role="alert">\
              <button type="button" class="close" data-dismiss="alert" aria-label="Close">\
                <span aria-hidden="true">&times;</span>\
              </button>' + msg + '</div>';
    old_msg_html = $('#js_messages_bottom').html();
    $('#js_messages_bottom').html(old_msg_html + msg_html)
}


function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
var csrftoken = $("[name=csrfmiddlewaretoken]").val();
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function refresh_task(task_id) {
    $.getJSON("/api/tasks/"+task_id+"/", function (data) {
        var status_html = data.status + '<br>';
        var meta = data.meta;
        if (meta.current && meta.total) {
            var current = meta.current;
            var total = meta.total;
            var percent = Math.ceil((current/total)*100);
            status_html += '<div class="progress"> \
                    <div class="progress-bar progress-bar-animated progress-bar-striped" role="progressbar" \
            aria-valuenow="' + percent + '" aria-valuemin="0" aria-valuemax="100"\
             style="width: ' + percent + '%">' + percent + '%</div>\
                </div>'
        }
        $('#status-' + task_id).html(status_html)
    })
}

function terminate_task(task_id) {
    // Partial Update with PATCH HTTP Method
    $.ajax({
        url: '/api/tasks/' + task_id + '/',
        type: 'PATCH',
        data: {
            'task_id': task_id
        },
        headers: { 'X_METHODOVERRIDE': 'PATCH' },
        success: function (result) {
            render_message('Задание ' + task_id + ' остановлено', 'info');
            // And Refreshing task status
            refresh_task(task_id)
            // console.log(result)
        },
        error: function (result) {
            render_message('Ошибка остановки задания ' + task_id + '<br>' +result.responseText, 'error')
        }
    })
}

function delete_task(task_id) {
    $.ajax({
        url: '/api/tasks/' + task_id + '/',
        type: 'DELETE',
        data: {
            'task_id': task_id
        },
        headers: { 'X_METHODOVERRIDE': 'DELETE' },
        success: function (result) {
            render_message('Задание ' + task_id + ' удалено', 'info');
            $('#job_row_'+task_id).remove();
        },
        error: function (result) {
            render_message('Ошибка удаления задания ' + task_id + '<br>' +result.responseText, 'error')
        }
    })
}

function task_result(task_id) {
    $('#task_result_modal').modal('toggle');
    wsconnect(task_id)

}

function wsconnect(task_id) {
    // When we're using HTTPS, use WSS too.
    var ws_scheme = window.location.protocol === "https:" ? "wss" : "ws";
    var ws_path = ws_scheme + '://' + window.location.host + '/ws/active_tasks/' + task_id + '/';
    console.log("Connecting to " + ws_path);
    var socket = new ReconnectingWebSocket(ws_path);

    socket.onmessage = function(message) {
        console.log("Got message: " + message.data);
        var data = JSON.parse(message.data);

        /*
        We need to get from data:
        data.script_name (можно было бы взять из кода страницы, но пофиг) - видимо нужно отдавать при подсоединении
        data.meta.current, data.meta.total - для прогресс-бара
        data.result - from job_result
        data.result_update - рассылка для подписчиков.
         */

        if (data.script_name) {
            $('#modalTitle').html(data.script_name)
        }

        if (data.meta && data.meta.current && data.meta.total)  {
            var current = data.meta.current;
            var total = data.meta.total;
            var percent = Math.ceil((current/total)*100);
            status_html += '<div class="progress"> \
                    <div class="progress-bar progress-bar-animated progress-bar-striped" role="progressbar" \
            aria-valuenow="' + percent + '" aria-valuemin="0" aria-valuemax="100"\
             style="width: ' + percent + '%">' + percent + '%</div>\
                </div>';
            $("#modalStatus").html(status_html)

        }
        var modalResult = $("#modalResult");
        if (data.result){
            modalResult.html(data.result)
        }

        if (data.result_update) {
            var current_result = modalResult.html();
            modalResult.html(current_result + data.result_update)
        }


    };

    $("#taskform").on("submit", function(event) {
        var message = {
            action: "start_sec3",
            job_name: $('#task_name').val()
        };
        socket.send(JSON.stringify(message));
        $("#task_name").val('').focus();
        return false;
    });
};
