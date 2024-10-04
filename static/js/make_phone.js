document.addEventListener('DOMContentLoaded', function () {
    const nextButton = document.getElementById('next-btn');
    const phoneForm = document.getElementById('phone-form');
    let isVerified = false;  // Variable to track whether the phone is verified

    // Disable the '다음으로' button initially
    nextButton.disabled = true;

    document.getElementById('verify-btn').addEventListener('click', function () {
        const phoneNumber = document.querySelector('.phone-input').value;

        if (!phoneNumber) {
            alert('전화번호를 입력하세요.');
            return;
        }

        fetch('/send_verification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ phone_number: phoneNumber })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const verificationSection = document.getElementById('verification-section');
                verificationSection.innerHTML = '';

                const verificationInput = document.createElement('input');
                verificationInput.setAttribute('type', 'text');
                verificationInput.setAttribute('name', 'verification_code');
                verificationInput.setAttribute('placeholder', '인증번호 입력');
                verificationInput.classList.add('verification-input');
                verificationInput.setAttribute('required', 'true');

                const confirmButton = document.createElement('button');
                confirmButton.textContent = '확인';
                confirmButton.classList.add('confirm-button');
                confirmButton.setAttribute('type', 'button');  // Prevent form submission

                verificationSection.appendChild(verificationInput);
                verificationSection.appendChild(confirmButton);

                // Add event listener to confirm button
                confirmButton.addEventListener('click', function () {
                    const enteredCode = verificationInput.value;

                    if (!enteredCode) {
                        alert('인증번호를 입력하세요.');
                        return;
                    }

                    // Bypass verification if 'test-user' is entered
                    if (enteredCode === 'test-user') {
                        alert('인증번호가 확인되었습니다.');
                        nextButton.disabled = false;  // Enable the '다음으로' button
                        isVerified = true;  // Mark the phone as verified
                    } else {
                        // Send the entered code to the server for verification
                        fetch('/verify_code', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ verification_code: enteredCode })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                alert('인증번호가 확인되었습니다.');
                                nextButton.disabled = false;  // Enable the '다음으로' button
                                isVerified = true;  // Mark the phone as verified
                            } else {
                                alert('인증번호가 틀렸습니다. 다시 입력해주세요.');
                                verificationInput.value = '';  // Clear the input field
                                nextButton.disabled = true;  // Keep '다음으로' disabled
                                isVerified = false;
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('서버 오류가 발생했습니다.');
                        });
                    }
                });
            } else {
                alert('인증번호 전송에 실패했습니다. 다시 시도해주세요.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('서버 오류가 발생했습니다.');
        });
    });

    // Prevent form submission if the phone isn't verified
    phoneForm.addEventListener('submit', function (event) {
        if (!isVerified) {
            event.preventDefault();  // Prevent form submission
            alert('인증번호를 먼저 확인해주세요!');
        }
    });
});
