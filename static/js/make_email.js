// Event listener for the '인증' (Verify) button
document.getElementById('verify-btn').addEventListener('click', function () {
    // Get the entered email value
    const email = document.querySelector('.email-input').value;

    // Send the email verification request to the server
    fetch('/send_verification', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('인증 이메일이 발송되었습니다.');

            // Select the verification section
            const verificationSection = document.getElementById('verification-section');

            // Create new input for verification code
            const verificationInput = document.createElement('input');
            verificationInput.setAttribute('type', 'text');
            verificationInput.setAttribute('placeholder', '인증번호 입력');
            verificationInput.classList.add('verification-input');
            verificationInput.setAttribute('required', 'true');

            // Create new confirmation button
            const confirmButton = document.createElement('button');
            confirmButton.textContent = '확인';
            confirmButton.classList.add('confirm-button');
            confirmButton.setAttribute('type', 'button');

            // Clear the section and append new elements
            verificationSection.innerHTML = '';
            verificationSection.appendChild(verificationInput);
            verificationSection.appendChild(confirmButton);

            // Event listener for the '확인' (Confirm) button
            confirmButton.addEventListener('click', function() {
                const verificationCode = verificationInput.value; // Get the input value

                // Perform a fetch call to the server to verify the code
                fetch('/verify_code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ verification_code: verificationCode })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('인증번호가 확인되었습니다!');
                        // Enable the form submit button
                        document.getElementById('submit-btn').disabled = false;
                    } else {
                        alert('인증번호가 잘못되었습니다. 다시 시도하세요.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('인증번호 확인 중 오류가 발생했습니다.');
                });
            });
        } else {
            alert('인증 이메일 발송에 실패했습니다.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('인증 요청 중 오류가 발생했습니다.');
    });
});
