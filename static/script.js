function focus_func() {
    $.ajax({
        url: '/checkloggedon',
        type: 'POST',
        data: JSON.stringify({message: 'You must be logged on to make a new discussion'}),
        contentType: 'application/json',
        dataType: 'json',
        success: function(response) {
            if (!response.success) {
                window.location.href = response.redirect;
            }
        }
    });
}

function delete_object(object, object_id) {
    $.ajax({
        url: '/delete/' + object +  '/' + object_id,
        type: 'POST',
        success: function (response) {
            window.location.href = response.redirect
        }
    });
}

function assign_object() {
    return !$('#available option:selected').remove().appendTo('#assigned')
}

function unassign_object() {
    return !$('#assigned option:selected').remove().appendTo('#available')
}

$(document).ready( function() {
    $('#available').dblclick( assign_object );
    $('#assigned').dblclick( unassign_object );
});

function toggle_dropdown() {
    document.getElementById('filter_dropdown').classList.toggle("show");
}

function add_like(object, id, option) {
    // check user logged on
    $.ajax({
        url: '/checkloggedon',
        type: 'POST',
        data: JSON.stringify({message: 'Must be logged in to like or dislike'}),
        contentType: "application/json",
        dataType: 'json',
        success: function (response) {
            if (response.success) {
                call();
            }
            else {
                window.location.href = response.redirect
            }
        }
    });
    function call() {
        $.ajax({
            url: '/add_like/' + object + '/' + id + '/' + option,
            type: 'POST',
            data: {message: 'Failed to add like/dislike'},
            success: function (response) {
                if (response.success) {
                    window.location.reload();
                }
            }
        });
    }
}
