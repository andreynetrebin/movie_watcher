// migration-helper.js - Утилиты для безопасной миграции
document.addEventListener('DOMContentLoaded', function() {
    // Проверка загрузки CSS переменных
    const testElement = document.createElement('div');
    testElement.className = 'migration-test migration-test--variables';
    testElement.style.display = 'none';
    testElement.textContent = 'CSS Variables: OK';
    document.body.appendChild(testElement);

    // Проверяем работу CSS переменных
    const styles = getComputedStyle(testElement);
    if (styles.backgroundColor === 'rgb(18, 192, 100)') {
        console.log('✅ CSS Variables working correctly');
        // Можно активировать дополнительные стили
    } else {
        console.log('⚠️ CSS Variables not working, fallback to legacy styles');
    }

    // Индикатор статуса миграции (опционально)
    const statusIndicator = document.createElement('div');
    statusIndicator.id = 'migration-status';
    statusIndicator.textContent = 'CSS Migration: Phase 1';
    document.body.appendChild(statusIndicator);

    // Показываем статус только в development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        statusIndicator.style.display = 'block';
    }
});