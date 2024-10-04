document.addEventListener("DOMContentLoaded", function () {
    const progressBar = document.querySelector(".loading-progress");
    
    let width = 0;
    const interval = setInterval(function () {
        if (width >= 100) {
            clearInterval(interval);
            window.location.href = "login.html"; // Redirect to login.html
        } else {
            width++;
            progressBar.style.width = width + '%';
        }
    }, 30); // Adjust the speed of the loading bar
});
