document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    const postList = document.getElementById('post-list');

    searchInput.addEventListener('input', function () {
        const query = searchInput.value.trim();

        if (query.length > 0) {
            fetch(`/search?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    postList.innerHTML = ''; // Clear previous results
                    
                    if (data.posts.length > 0) {
                        data.posts.forEach(post => {
                            // Create the post card HTML
                            const postCard = `
                                <div class="recommended-post-card">
                                    <a href="/post/${post._id}" class="post-link">
                                        <div class="post-header">
                                            <img src="${post.profile_image}" alt="프로필 이미지" class="profile-img">
                                            <span class="username">${post.nickname}</span>
                                        </div>
                                        <div class="image-placeholder">
                                            <img src="/static/${post.image_path}" alt="Post Image">
                                        </div>
                                        <div class="post-hashtags">
                                            ${post.tags_list.map(tag => `<span class="hashtag">#${tag}</span>`).join('')}
                                        </div>
                                    </a>
                                </div>`;
                            // Insert the post card into the post list
                            postList.insertAdjacentHTML('beforeend', postCard);
                        });
                    } else {
                        postList.innerHTML = '<p>발견된 게시글이 없습니다.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error fetching search results:', error);
                    postList.innerHTML = '<p>Error fetching posts</p>';
                });
        } else {
            postList.innerHTML = '<p>검색창에 입력을 해주세요.</p>';
        }
    });
});
