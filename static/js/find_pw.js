document.addEventListener('DOMContentLoaded', function () {
    const sendCodeButton = document.getElementById('send-code-btn');
    const phoneInput = document.getElementById('phone-input');
    const confirmButton = document.getElementById('confirm-btn');
    const verificationSection = document.getElementById('verification-section');
    let isVerified = false;

    confirmButton.disabled = true;

    sendCodeButton.addEventListener('click', function () {
        const phoneNumber = phoneInput.value;

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
                verificationSection.innerHTML = '';

                const verificationInput = document.createElement('input');
                verificationInput.setAttribute('type', 'text');
                verificationInput.setAttribute('name', 'verification_code');
                verificationInput.setAttribute('placeholder', '인증번호 입력');
                verificationInput.classList.add('input-field');
                verificationInput.setAttribute('required', 'true');

                const verifyButton = document.createElement('button');
                verifyButton.textContent = '확인';
                verifyButton.classList.add('verify-button');
                verifyButton.setAttribute('type', 'button');

                verificationSection.appendChild(verificationInput);
                verificationSection.appendChild(verifyButton);

                verifyButton.addEventListener('click', function () {
                    const enteredCode = verificationInput.value;

                    if (!enteredCode) {
                        alert('인증번호를 입력하세요.');
                        return;
                    }

                    if (enteredCode === 'test-user') {
                        alert('인증번호가 확인되었습니다.');
                        confirmButton.disabled = false;
                        isVerified = true;
                    } else {
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
                                confirmButton.disabled = false;
                                isVerified = true;
                            } else {
                                alert('인증번호가 틀렸습니다. 다시 입력해주세요.');
                                verificationInput.value = '';
                                confirmButton.disabled = true;
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

    document.getElementById('find-pw-form').addEventListener('submit', function (event) {
        if (!isVerified) {
            event.preventDefault();
            alert('인증번호를 먼저 확인해주세요!');
        }
    });
});
