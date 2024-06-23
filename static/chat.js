



// chat.js
$(document).ready(function() {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    $('#send-button').click(function() {
        var message = $('#message-input').val();
        socket.emit('message', message);
        $('#message-input').val('');
    });

    socket.on('message', function(msg) {
        var messageClass = 'message sender';
        if (msg.sender === 'receiver') {
            messageClass = 'message receiver';
        }
        $('#chat-window').append(`<div class="${messageClass}">${msg.text}</div>`);
    });
});

window.setTimeout(function() {
    let flashes = document.querySelectorAll('.flash');
    flashes.forEach(function(flash) {
        flash.style.display = 'none';
    });
}, 3000);  // Adjust time as needed