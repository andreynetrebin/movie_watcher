document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('movie-search');
    const searchButton = document.querySelector('.search-button');

    searchInput.addEventListener('input', function() {
        const query = searchInput.value;

        if (query.length > 2) {  // Начинаем поиск после ввода 3 символов
            fetch(`/movies/search/?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    // Обработка результатов
                    const resultsContainer = document.createElement('div');
                    resultsContainer.classList.add('search-results');
                    resultsContainer.innerHTML = '';

                    data.forEach(movie => {
                        const resultItem = document.createElement('div');
                        resultItem.classList.add('result-item');

                        // Создаем элемент для отображения названия и года
                        resultItem.innerHTML = `
                            <strong>${movie.title}</strong>
                            <span class="movie-year"> (${movie.year})</span>
                        `;

                        // Добавляем обработчик клика для перехода на страницу фильма
                        resultItem.onclick = function() {
                            window.location.href = `/movies/detail/${movie.slug}/`; // Переход на страницу фильма
                        };

                        resultsContainer.appendChild(resultItem);
                    });

                    // Удаляем предыдущие результаты
                    const existingResults = document.querySelector('.search-results');
                    if (existingResults) {
                        existingResults.remove();
                    }

                    // Добавляем новые результаты
                    searchInput.parentNode.appendChild(resultsContainer);
                });
        }
    });

    // Закрытие результатов при клике вне
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target)) {
            const resultsContainer = document.querySelector('.search-results');
            if (resultsContainer) {
                resultsContainer.remove();
            }
        }
    });
});