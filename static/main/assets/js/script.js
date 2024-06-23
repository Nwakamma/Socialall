// On page load or when changing themes, best to add inline in `head` to avoid FOUC
if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark')
    } else {
    document.documentElement.classList.remove('dark')
    }

// Whenever the user explicitly chooses light mode
localStorage.theme = 'light'

// Whenever the user explicitly chooses dark mode
localStorage.theme = 'dark'

// Whenever the user explicitly chooses to respect the OS preference
localStorage.removeItem('theme')



// add post upload image 
document.getElementById('addPostUrl').addEventListener('change', function(){
if (this.files[0] ) {
    var picture = new FileReader();
    picture.readAsDataURL(this.files[0]);
    picture.addEventListener('load', function(event) {
    document.getElementById('addPostImage').setAttribute('src', event.target.result);
    document.getElementById('addPostImage').style.display = 'block';
    });
}
});


// Create Status upload image 
// document.getElementById('createStatusUrl').addEventListener('change', function(){
// if (this.files[0] ) {
//     var picture = new FileReader();
//     picture.readAsDataURL(this.files[0]);
//     picture.addEventListener('load', function(event) {
//     document.getElementById('createStatusImage').setAttribute('src', event.target.result);
//     document.getElementById('createStatusImage').style.display = 'block';
//     });
// }
// });


// create product upload image
document.getElementById('createProductUrl').addEventListener('change', function(){
if (this.files[0] ) {
    var picture = new FileReader();
    picture.readAsDataURL(this.files[0]);
    picture.addEventListener('load', function(event) {
    document.getElementById('createProductImage').setAttribute('src', event.target.result);
    document.getElementById('createProductImage').style.display = 'block';
    });
}
});

//for upload hidden div//

function upload() {
    var uppop = document.getElementById('forup');
    if (uppop.style.display=== 'none'){
        uppop.style.display = 'block';
    } else{
        uppop.style.display = 'none';
    }
    
}


//for previewing//

// function previewMedia() {
//     const input = document.getElementById('forfile');
//     const imagepreview = document.getElementById('imagepreview');
//     const videopreview = document.getElementById('videopreview');
//     let currentBlobUrl = null;
//     input.addEventListener('change', function(event){
//         if (currentBlobUrl) {
//             URL.revokeObjectURL(currentBlobUrl);
//         }
//         const file = event.target.files[0];
//         if (!file) {
//             return;
//         }
//         const fileType = file['type'];
//         const validImageType = ['image/*'];
//         const validVideoType = ['video/*'];
//         if (validImageType.includes(fileType)) {
//             currentBlobUrl = URL.createObjectURL(file);
//             imagepreview.src = currentBlobUrl;
//             imagepreview.style.display = 'block';
//             videopreview.style.display = 'none';
//         } else if (validVideoType.includes(fileType)) {
//             currentBlobUrl = URL.createObjectURL(file);
//             videopreview.src = currentBlobUrl;
//             videopreview.style.display = 'block';
//             imagepreview.style.display = 'none';
//             videopreview.load();
//             videopreview.play();
//         } else {
//             alert('Invalid file type!');
//         }

//     });

// }
// previewMedia();

//preview uploads//




function showcomm1() {
    var comm2 = document.getElementById('comm1')
    if (comm2.style.display === 'none') {
        comm2.style.display = 'block';
    } else{
        comm2.style.display = 'none';
    }
}
    
function showcomm3() {
    var comm2 = document.getElementById('comm3')
    if (comm2.style.display === 'none') {
        comm2.style.display = 'block';
    } else{
        comm2.style.display = 'none';
    }
}

//for upload div//
function showUploaddiv() {
    var uploaddiv = document.getElementById('uploaddiv');
    if (uploaddiv.style.display === 'none') {
        uploaddiv.style.display = 'block';
    } else {
        uploaddiv.style.display = 'none';
    }
}
function showvidupload() {
    var uploaddiv = document.getElementById('uploaddivvid');
    var close = document.getElementById('closediv');
    if (uploaddiv.style.display === 'none') {
        uploaddiv.style.display = 'block';
    } else {
        uploaddiv.style.display = 'none';
    }
    close.onclick = function(){
        uploaddiv.style.display = 'none';
    }
}

function showvidupload1() {
    var uploaddiv = document.getElementById('uploaddivvid1');
    var close = document.getElementById('closediv');
    if (uploaddiv.style.display === 'none') {
        uploaddiv.style.display = 'block';
    } else {
        uploaddiv.style.display = 'none';
    }
    close.onclick = function(){
        uploaddiv.style.display = 'none';
    }
}
// static/scripts.js for dark mood

document.addEventListener('DOMContentLoaded', (event) => {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const body = document.body;

    // Check for saved user preference, if any
    if (localStorage.getItem('darkMode') === 'enabled') {
        body.classList.add('darkd');
    }

    darkModeToggle.addEventListener('click', () => {
        body.classList.toggle('darkd');

        // Save or remove the state in localStorage
        if (body.classList.contains('darkd')) {
            localStorage.setItem('darkMode', 'enabled');
        } else {
            localStorage.removeItem('darkMode');
        }
    });
});



function showvidupload3() {
    var uploaddiv = document.getElementById('uploaddivvid3');
    var close = document.getElementById('closediv');
    if (uploaddiv.style.display === 'none') {
        uploaddiv.style.display = 'block';
    } else {
        uploaddiv.style.display = 'none';
    }
    close.onclick = function(){
        uploaddiv.style.display = 'none';
    }
}

// script.js
function react(emoji) {
    // Handle the reaction logic here (e.g., update database, show animation, etc.)
    console.log(`User reacted with ${emoji}`);
}

function editphoto(){
    const imagediv = document.getElementById('myphotos');
    const closeit = document.getElementById('closeit');
    //const droped = document.getElementById('droped');
    if (imagediv.style.display === 'none'){
        imagediv.style.display = 'block';
        closeit.style.display = 'block';
        //droped.style.display = 'none';
    } else{
        imagediv.style.display = 'none';
        //droped.style.display = 'block';
    }
    closeit.onclick = function(){
        imagediv.style.display = 'none';
    }
}
