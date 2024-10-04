document.addEventListener('DOMContentLoaded', function() {
    var buttons = document.querySelectorAll('.item-box button');
    var applyButton = document.querySelector('.apply-button');
    var resetButton = document.querySelector('.reset-button');
    var selectedAccessory = null;
    var imageDiv = document.querySelector('.image');
    var originalCharacterImage = imageDiv.dataset.characterImageOriginal;
    var currentCharacterImage = imageDiv.dataset.characterImage;

    var nocheckValue = parseInt(nocheck); // nocheck를 숫자로 변환

    buttons.forEach(function(button) {
        button.addEventListener('click', function() {
            var accessoryName = this.dataset.accessoryName;
            var price = parseInt(this.dataset.price);
            var buttonText = this.textContent.trim();

            if (nocheckValue > 9) {
                alert('현재 상태에서는 악세사리 착용이 불가합니다! 때밀기를 먼저 해주세요!');
                return;
            }

            if (buttonText === '선택') {
                // 액세서리 선택
                selectedAccessory = accessoryName;
                // 적용 버튼 활성화
                applyButton.disabled = false;
                alert(accessoryName + '가 선택되었습니다.');
                // 미리보기 이미지 업데이트
                updatePreviewImage(accessoryName);
            } else {
                // 구매 확인
                if (confirm('구매하시겠습니까?')) {
                    purchaseAccessory(accessoryName, price);
                }
            }
        });
    });

    // 적용 버튼 클릭 시 액세서리 적용
    applyButton.addEventListener('click', function() {
        if (selectedAccessory) {
            applyAccessory(selectedAccessory);
        }
    });

    // 초기화 버튼 클릭 시 액세서리 제거
    resetButton.addEventListener('click', function() {
        if (confirm('액세서리를 제거하시겠습니까?')) {
            removeAccessory();
        }
    });
    // 액세서리 구매 함수
    function purchaseAccessory(accessoryName, price) {
        fetch('/buy_accessory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                accessory_name: accessoryName
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('구매가 완료되었습니다!');

                // 버튼 텍스트를 '선택'으로 변경
                var button = document.querySelector('button[data-accessory-name="' + accessoryName + '"]');
                button.textContent = '선택';

                // 아이템 이미지 잠금 해제 (이미지를 업데이트)
                var itemBox = button.closest('.item-box');
                var itemImage = itemBox.querySelector('.item-image');
                var accessoryImageUrl = staticImageBaseURL + accessoryName + "_스티커.png";

                // 즉시 이미지를 변경하여 잠금을 해제하고 악세사리 표시
                var img = new Image();
                img.src = accessoryImageUrl;
                img.onload = function() {
                    itemImage.style.backgroundImage = "url('" + accessoryImageUrl + "')";
                };

                img.onerror = function() {
                    // 만약 이미지가 로드되지 않으면 새로고침
                    location.reload();
                };

                // 크레딧 업데이트 (필요 시)
                credits -= price;

            } else {
                alert(data.message);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
            // 오류 발생 시 새로고침
            location.reload();
        });
    }


    // 액세서리 적용 함수
    function applyAccessory(accessoryName) {
        if (nocheckValue > 9) {
            alert('꼬질이 상태에서는 악세사리 착용이 불가합니다!');
            return;
        }

        fetch('/select_accessory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                accessory_name: accessoryName
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('액세서리가 적용되었습니다!');
                // 캐릭터 이미지 업데이트
                updateCharacterImage(accessoryName);
                // 적용 버튼 비활성화
                applyButton.disabled = true;
                selectedAccessory = null;
            } else {
                alert(data.message);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }

    // 액세서리 제거 함수
    function removeAccessory() {
        fetch('/remove_accessory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('액세서리가 제거되었습니다.');
                // 캐릭터 이미지 업데이트
                imageDiv.style.backgroundImage = "url('" + getStaticImageUrl(originalCharacterImage) + "')";
                // 적용 버튼 비활성화
                applyButton.disabled = true;
                selectedAccessory = null;
            } else {
                alert(data.message);
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    }

    // 캐릭터 이미지 업데이트 함수
    function updateCharacterImage(accessoryName) {
        var newCharacterImage = originalCharacterImage.replace('.png', '_' + accessoryName + '.png');
        imageDiv.style.backgroundImage = "url('" + getStaticImageUrl(newCharacterImage) + "')";
    }

    // 미리보기 이미지 업데이트 함수
    function updatePreviewImage(accessoryName) {
        var newCharacterImage = originalCharacterImage.replace('.png', '_' + accessoryName + '.png');
        imageDiv.style.backgroundImage = "url('" + getStaticImageUrl(newCharacterImage) + "')";
    }

    // 정적 이미지 URL 생성 함수
    function getStaticImageUrl(imageName) {
        return staticImageBaseURL + imageName;
    }
});
