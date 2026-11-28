document.addEventListener('DOMContentLoaded', function() {
    var options = {
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken},
        mode: 'same-origin'
    };

// Обработчик для кнопки "Like"
document.querySelectorAll('button.like').forEach(function(likeButton) {
    likeButton.addEventListener('click', function(e) {
        e.preventDefault();

        // Подготовка данных для запроса
        var formData = new FormData();
        formData.append('id', likeButton.dataset.id);

        // Отправка HTTP-запроса
        fetch(url_like, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data['status'] === 'liked') {
                // Обновление состояния кнопки
                likeButton.classList.add('active');
                var likeIcon = likeButton.querySelector('i');
                likeIcon.classList.add('active');

                // Если dislike был ранее, отключаем его
                var dislikeButton = document.querySelector('button.dislike[data-id="' + likeButton.dataset.id + '"]');
                if (dislikeButton) {
                    dislikeButton.classList.remove('active');
                    var dislikeIcon = dislikeButton.querySelector('i');
                    dislikeIcon.classList.remove('active');
                }
            } else if (data['status'] === 'unliked') {
                // Снятие лайка
                likeButton.classList.remove('active');
                var likeIcon = likeButton.querySelector('i');
                likeIcon.classList.remove('active');
            }
        });
    });
});

// Обработчик для кнопки "Dislike"
document.querySelectorAll('button.dislike').forEach(function(dislikeButton) {
    dislikeButton.addEventListener('click', function(e) {
        e.preventDefault();

        // Подготовка данных для запроса
        var formData = new FormData();
        formData.append('id', dislikeButton.dataset.id);

        // Отправка HTTP-запроса
        fetch(url_dislike, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data['status'] === 'disliked') {
                // Обновление состояния кнопки
                dislikeButton.classList.add('active');
                var dislikeIcon = dislikeButton.querySelector('i');
                dislikeIcon.classList.add('active');

                // Если like был ранее, отключаем его
                var likeButton = document.querySelector('button.like[data-id="' + dislikeButton.dataset.id + '"]');
                if (likeButton) {
                    likeButton.classList.remove('active');
                    var likeIcon = likeButton.querySelector('i');
                    likeIcon.classList.remove('active');
                }
            } else if (data['status'] === 'undisliked') {
                // Снятие дизлайка
                dislikeButton.classList.remove('active');
                var dislikeIcon = dislikeButton.querySelector('i');
                dislikeIcon.classList.remove('active');
            }
        });
    });
});

document.querySelectorAll('button.wishlist').forEach(function(wishlistButton) {
    wishlistButton.addEventListener('click', function(e) {
        e.preventDefault();
        // Подготовка данных для запроса
        var formData = new FormData();
        formData.append('id', wishlistButton.dataset.id);
        formData.append('action', 'toggle'); // Указываем действие "toggle" для добавления/удаления
        // Отправка HTTP-запроса
        fetch(url_wishlist, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken') // Получите CSRF-токен
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data['status'] === 'added') {
                // Обновление состояния кнопки, если фильм добавлен в вишлист
                wishlistButton.querySelector('i').classList.add('transparent'); // Сделать иконку прозрачной
            } else if (data['status'] === 'removed') {
                // Обновление состояния кнопки, если фильм удален из вишлиста
                wishlistButton.querySelector('i').classList.remove('transparent'); // Вернуть иконку в цвет
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
        });
    });
});

// Функция для получения CSRF-токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.querySelectorAll('button.watched').forEach(function(watchedButton) {
    watchedButton.addEventListener('click', function(e) {
        e.preventDefault();
        var formData = new FormData();
        formData.append('id', watchedButton.dataset.id);
        fetch(url_watched, {
            method: 'POST',
            headers: {'X-CSRFToken': csrftoken},
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data['status'] === 'added') {
                watchedButton.querySelector('i').classList.add('fa-check');
                watchedButton.querySelector('.action-label').textContent = 'Просмотрен';
                watchedButton.closest('.movie-item').classList.add('watched');
            } else if (data['status'] === 'removed') {
                watchedButton.querySelector('i').classList.remove('fa-check');
                watchedButton.querySelector('.action-label').textContent = 'Пометить как просмотренный';
                watchedButton.closest('.movie-item').classList.remove('watched');
            }
        });
    });
});

document.querySelectorAll('button.recently-watched').forEach(function(watchedRecentlyButton) {
    watchedRecentlyButton.addEventListener('click', function(e) {
        e.preventDefault();
        var formData = new FormData();
        formData.append('id', watchedRecentlyButton.dataset.id);
        fetch(url_recently_watched, {
            method: 'POST',
            headers: {'X-CSRFToken': csrftoken},
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data['status'] === 'added' || data['status'] === 'already_marked') {
                watchedRecentlyButton.querySelector('i').classList.add('fa-check');
                watchedRecentlyButton.querySelector('.action-label').textContent = 'Просмотрен недавно';
                watchedRecentlyButton.closest('.movie-item').classList.add('watched');
            }
        });
    });
});
});