// .addImage 클릭 시 파일 입력 필드를 클릭하도록 설정
document.querySelector('.addImage').addEventListener('click', function() {
    document.querySelector('input[type="file"]').click();
});

function loadFile(input) {
    let file = input.files[0]; // 선택된 파일 가져오기

    if (file) {
        let newImage = document.createElement("img"); // 새 이미지 태그 생성

        // 이미지 source 가져오기
        newImage.src = URL.createObjectURL(file);
        newImage.style.width = "100%"; // div에 꽉 차게 설정
        newImage.style.height = "100%";
        newImage.style.objectFit = "cover"; // div에 맞게 자르기

        // 기존 이미지를 제거하고 새 이미지 추가
        let container = document.getElementById('image-show');
        container.innerHTML = ""; // 기존 이미지를 제거
        container.appendChild(newImage);

        // .addImage 클래스에 .image-uploaded 클래스를 추가
        container.parentElement.classList.add('image-uploaded');

        // 이미지 업로드 후 ::before content를 제거
        container.parentElement.style.setProperty('--before-content', 'none');
    }
}




function cancelUpload() {
    // 파일 입력 필드 초기화
    document.getElementById('file-input').value = "";

    // 이미지 미리보기 제거
    let container = document.getElementById('image-show');
    container.innerHTML = "";

    // 취소 버튼 숨기기
    document.getElementById('cancel-button').style.display = 'none';
}

document.querySelector('form').addEventListener('submit', function(event) {
    // 각 태그에 대해 체크박스가 선택되지 않았으면 기본값 설정
    if (document.getElementById('age-input').value === '') {
        document.getElementById('age-input').value = '미선택';
    }
    if (document.getElementById('gender-input').value === '') {
        document.getElementById('gender-input').value = '미선택';
    }
    if (document.getElementById('travel-type-input').value === '') {
        document.getElementById('travel-type-input').value = '미선택';
    }
    if (document.getElementById('region-input').value === '') {
        document.getElementById('region-input').value = '미선택';
    }
    if (document.getElementById('cost-input').value === '') {
        document.getElementById('cost-input').value = '미선택';
    }
    if (document.getElementById('relationship-input').value === '') {
        document.getElementById('relationship-input').value = '미선택';
    }
    if (document.getElementById('during-input').value === '') {
        document.getElementById('during-input').value = '미선택';
    }
});







// -------------------------------------------- //







// 모달 열기
// 모달 열기
// 모달 열기
function openModal(modalId) {
    document.getElementById(modalId).style.display = "block";
}

// 모달 닫기
function closeModal(modalId) {
    document.getElementById(modalId).style.display = "none";
}

// // 세분화된 지역 모달 열기
// function openSubRegionModal(modalId) {
//     closeModal('region-modal'); // 기존 지역 모달 닫기
//     openModal(modalId); // 세분화된 지역 모달 열기
// }

function openSubRegionModal(modalId, parentModalId) {
    closeModal(parentModalId); // 부모 모달 닫기
    openModal(modalId); // 세분화된 지역 모달 열기
}

// 모달 외부 클릭 시 닫기
window.onclick = function(event) {
    const modals = document.getElementsByClassName('modal');
    for (let i = 0; i < modals.length; i++) {
        if (event.target == modals[i]) {
            modals[i].style.display = "none";
        }
    }
}

function selectOption(buttonId, value, inputId) {
    document.getElementById(buttonId).innerText = value;  // 버튼의 텍스트를 업데이트
    document.getElementById(inputId).value = value;       // 숨겨진 input 필드에 값 설정

    closeModal('age-modal');
    closeModal('gender-modal');
    closeModal('travel-type-modal');
    closeModal('asia-modal');
    closeModal('korea-modal');
    closeModal('europe-modal');
    closeModal('africa-modal');
    closeModal('north-america-modal');
    closeModal('south-america-modal');
    closeModal('Oceania-modal');
    closeModal('cost-modal');
    closeModal('relationship-modal');
    closeModal('during-modal');


    // 지역 태그를 선택할 때만 추천 항목 업데이트
    if (inputId === 'region-input') {
        document.getElementById('recommendation-cards').style.display = 'flex';
        document.getElementById('region').style.display = 'none';
        document.getElementById('region1').style.display = 'none';
        fetchRecommendations(value);
    }
}

function fetchRecommendations(region) {
    const recommendationsContainer = document.querySelector('.recommendation-cards');

    fetch('/get_recommendations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ region: region })
    })
    .then(response => response.json())
    .then(data => {
        if (data.posts && data.posts.length > 0) {
            updateRecommendations(data.posts);
            recommendationsContainer.style.display = 'flex';
        } else {
            updateRecommendations([], "관련 게시물이 현재 없습니다.");
        }
    })
    .catch(error => {
        console.error('Error fetching recommendations:', error);
        updateRecommendations([], "관련 게시물을 가져오는 중 오류가 발생했습니다.");
    });
}

function updateRecommendations(posts) {
    const recommendationsContainer = document.querySelector('.recommendation-cards');
    recommendationsContainer.innerHTML = '';  // 기존의 추천 내용을 제거

    if (posts.length === 0) {
        recommendationsContainer.innerHTML = '<p style="text-align: center; margin:0 auto;">관련 게시물이 현재 없습니다.</p>';
        recommendationsContainer.style.display = 'flex';
        return;
    }

    recommendationsContainer.style.display = 'flex';  // 추천 카드 영역 표시

    posts.forEach(post => {
        const card = document.createElement('div');
        card.className = 'card';

        const img = document.createElement('img');
        img.src = post.image_path;  // 서버에서 받은 이미지 경로 사용
        img.className = 'card-img';
        card.appendChild(img);

        const cardContent = document.createElement('div');
        cardContent.className = 'card-content';

        const review = document.createElement('p');
        review.className = 'review';
        review.textContent = `한줄 후기: ${post.content}`;
        cardContent.appendChild(review);

        const location = document.createElement('p');
        location.className = 'location';
        location.textContent = `지역: ${post.tags.region}`;  // 지역 정보 업데이트
        cardContent.appendChild(location);

        const cost = document.createElement('p');
        cost.className = 'cost';
        cost.textContent = `비용: ${post.tags.cost}`;  // 비용 정보 업데이트
        cardContent.appendChild(cost);

        const author = document.createElement('p');
        author.className = 'author';
        author.textContent = `작성자: ${post.tags.relationship}`;
        cardContent.appendChild(author);

        card.appendChild(cardContent);
        recommendationsContainer.appendChild(card);
    });
}
