const userType = "{{ user_type }}";  // Get user type from the server
document.getElementById('profile-image').addEventListener('click', function() {
document.getElementById('profile-input').click();
});

document.getElementById('profile-input').addEventListener('change', function() {
// Automatically submit the form when a file is selected
document.getElementById('profile-form').submit();
});

// Handle the password edit button click
document.getElementById('password-edit-button').addEventListener('click', function() {
if (userType === 'naver' || userType === 'kakao' || userType === 'google') {
    alert('소셜 회원가입은 비밀번호 수정이 불가능합니다!');
} else {
    // Redirect to password change page
    window.location.href = "{{ url_for('change_password_handler') }}";
}
});

// Handle profile image click
document.getElementById('profile-image').addEventListener('click', function() {
document.getElementById('profile-input').click();
});

document.getElementById('profile-input').addEventListener('change', function(event) {
// 이미지 업로드 처리 로직 추가
});