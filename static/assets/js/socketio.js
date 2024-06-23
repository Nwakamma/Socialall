// document.addEventListener('DOMContentLoaded', () => {
//     var socket = io.connect('http://' + document.domain + ':' + location.port);

//     socket.on(`send_message`, data => {
//         // const p = document.createElement('p');
//         // const span_user = document.createElement('span');
//         // const br = document.createElement('br');
//         // span_user.innerHTML = data.username;
//         // p.innerHTML = span_user.outerHTML + br.outerHTML + data.msg + br.outerHTML;
//         // document.querySelector('#messages').append(p);
//         console.log(``)
        
//     });
//     socket.on('some_event', data => {
//         console.log(data);
//     });

//     document.querySelector('#sendmessage').onclick = () => {
//         socket.send(document.querySelector('#message_input').value);
//     }
// })



//var socket = io.connect('http://' + document.domain + ':' + location.port);
//    var typing = false;
//    var timeout = undefined;
//
//    function timeoutFunction() {
//        typing = false;
//        socket.emit('stop_typing', { 'sender_id': sender_id });
//    }
//
//    document.getElementById('message_input').addEventListener('keyup', function() {
//        if (typing == false) {
//            typing = true
//            socket.emit('start_typing', { 'sender_id': sender_id });
//            timeout = setTimeout(timeoutFunction, 2000);
//        } else {
//            clearTimeout(timeout);
//            timeout = setTimeout(timeoutFunction, 2000);
//        }
//    });
//
//    function sendMessage() {
//        var messageInput = document.getElementById('message_input');
//        var message = messageInput.value.trim();
//        if (message.length) {
//
//            console.log('Sending messge:', message);
//            socket.emit('send_message', {
//                'sender_id': sender_id,
//                'recipient_id': recipient_id,
//                'message': message
//            });
//            messageInput.value = '';
//        }
//    }
//
//    socket.on('receive_message', function(data) {
//        var messagesDiv = document.getElementById('messages');
//        var messageElement = document.createElement('div');
//        messageElement.textContent = data.sender_id + ': ' + data.message;
//        messagesDiv.appendChild(messageElement);
//        messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto scroll to the bottom
//    });
//
//    socket.on('user_typing', function(data) {
//        var typingIndicator = document.getElementById('typing-indicator');
//        if (data.typing && data.user_id !== sender_id) {
//            typingIndicator.textContent = 'User ' + data.user_id + ' is typing...';
//        } else {
//            typingIndicator.textContent = '';
//        }
//    });

document.addEventListener('DOMContentLoaded', (event) => {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    var sender_id = "{{ user.id }}";
    var recipient_id = "{{ other.id }}";
    var chatDiv = document.getElementById('chat');
    var messageInput = document.getElementById('message_input');
    var typingIndicator = document.getElementById('typingIndicator');
    var typing = false;
        //var sendButton = document.getElementById('send_button');
        
        

        

    socket.on('connect', () => {
        socket.emit('join', {recipient_id: sender_id});

        document.getElementById('send_button').onclick = () => {
            let message = document.getElementById('message_input').value;
            var messager = messageInput.value;
            socket.emit('messager', messager);
            messageInput.value = '';
            socket.emit('private_message', {recipient_id: recipient_id, message: message});
            document.getElementById('message_input').value='';
            console.log(message);
        };
    });

    socket.on('message', (data) => {
        if(data.message) {
            let messageDiv = document.createElement('div');
            messageDiv.textContent = 'Message from ' + data.sender_id + ': ' + data.message;
            document.getElementById('messages_container').appendChild(messageDiv);
        }
    });
    socket.on('messager', function(messager) {
            chatDiv.innerHTML += '<p>' + messager + '</p>';
        });
    socket.on('room_notification', (data) => {
        if (data.message) {
            let notificationDiv  = document.createElement('div');
            notificationDiv.innerHTML = data.message;
        document.getElementById('notifications_container').appendChild(notificationDiv);
        }
    });
    ///my ee
    

        messageInput.addEventListener('input', function() {
            if (!typing) {
                typing = true;
                socket.emit('typing', true);
            }

            setTimeout(function() {
                typing = false;
                socket.emit('typing', false);
            }, 2000);
        });
    // sendButton.addEventListener('click', function() {
    //         var messager = messageInput.value;
    //         socket.emit('messager', messager);
    //         messageInput.value = '';
    //     });

        socket.on('typing', function(isTyping) {
            typingIndicator.innerText = isTyping ? 'typing...' : '';
        });
});
