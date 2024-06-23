
document.addEventListener('DOMContentLoaded', (event) => {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    socket.on('user_follow', function(data) {
        var userId = "{{other.id}}"
        var notificationDiv = document.getElementById('notificationbar');
        var message = 'You have a new follower! ';
        var link = '<a href=""> View profile </a>';
        notificationDiv.innerHTML = message + link; 
    });
})