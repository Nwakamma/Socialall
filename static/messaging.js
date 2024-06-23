var socket = io();

        var chatDiv = document.getElementById('chat');
        var messageInput = document.getElementById('message_input');
        var sendButton = document.getElementById('send_button');
        var typingIndicator = document.getElementById('typingIndicator');
        

        var typing = false;

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

        sendButton.addEventListener('click', function() {
            var messager = messageInput.value;
            socket.emit('messager', messager);
            messageInput.value = '';
        });

        socket.on('messager', function(messager) {
            chatDiv.innerHTML += '<p>' + messager + '</p>';
        });

        socket.on('typing', function(isTyping) {
            typingIndicator.innerText = isTyping ? 'Someone is typing...' : '';
        });