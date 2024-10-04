// Redirect to home.html after 5 seconds
setTimeout(function(){
    window.location.href = 'home.html';
}, 4000);

// Function to generate calendar days based on the month
function generateCalendar(month, daysInMonth) {
    const calendar = document.getElementById('calendar');
    calendar.innerHTML = ''; // Clear any existing days
    for (let i = 1; i <= daysInMonth; i++) {
        const dayDiv = document.createElement('div');
        dayDiv.classList.add('day');
        
        // Add the date text inside a span
        const dateSpan = document.createElement('span');
        dateSpan.innerText = i;
        dayDiv.appendChild(dateSpan);
        
        if (i <= 3) { // Mark first three days as checked for demonstration
            dayDiv.classList.add('checked');
        }
        
        calendar.appendChild(dayDiv);
    }
}

// Define the number of days in September
const daysInMonth = 30;
generateCalendar(9, daysInMonth);

// Play the video when the button is clicked
document.getElementById('watch-ad-btn').addEventListener('click', function() {
    var video = document.createElement('video');
    video.src = 'check.mp4';
    video.controls = true;
    document.body.appendChild(video);
    video.play();
});
