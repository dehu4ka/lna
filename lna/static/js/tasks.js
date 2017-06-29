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

}
