document.addEventListener("DOMContentLoaded", () => {

    // Находим все кнопки выполнения
    const buttons = document.querySelectorAll(".toggle-btn");

    buttons.forEach(btn => {
        btn.addEventListener("click", async () => {

            const practiceId = btn.dataset.practiceId;

            // Отправляем AJAX POST
            const response = await fetch(`/practice/${practiceId}/toggle`, {
                method: "POST"
            });

            const data = await response.json();

            // Обновляем кнопку
            updateButton(btn, data);

            // Обновляем streak
            updateStreak(data);

            // Обновляем прогресс
            updateProgress(data);
        });
    });
});


// ✅ Обновление кнопки
function updateButton(btn, data) {
    const completed = data.completed;

    if (completed) {
        btn.classList.remove("btn-outline-secondary");
        btn.classList.add("btn-success");
        btn.innerText = "✅ Выполнено";
        btn.dataset.completed = "1";
    } else {
        btn.classList.remove("btn-success");
        btn.classList.add("btn-outline-secondary");
        btn.innerText = "○ Отметить выполнение";
        btn.dataset.completed = "0";
    }

    // ✅ Обновляем карточку
    updateCard(btn, completed);
}


// ✅ Анимация карточки
function updateCard(btn, completed) {
    // Находим карточку (btn → card-body → card)
    const card = btn.closest(".card");

    if (!card) return;

    if (completed) {
        card.classList.add("completed");

        // Добавляем анимацию "пульса"
        card.classList.add("completed-animate");

        // Убираем класс анимации через 300 мс
        setTimeout(() => {
            card.classList.remove("completed-animate");
        }, 300);

    } else {
        card.classList.remove("completed");
    }
}



// ✅ Обновление streak
function updateStreak(data) {
    const block = document.getElementById(`streak-${data.practice_id}`);

    if (data.completed) {
        block.innerHTML = `<span class="text-success">Серия: ${data.streak} дней</span>`;
    } else {
        block.innerHTML = "";
    }
}


// ✅ Обновление прогресса
function updateProgress(data) {
    const bar = document.getElementById(`progress-14-${data.practice_id}`);
    const text = document.getElementById(`progress-text-14-${data.practice_id}`);

    // Плавная анимация
    bar.style.transition = "width 0.4s ease";
    bar.style.width = `${data.progress_14}%`;

    text.innerText = `Прогресс 14 дней: ${data.progress_14}%`;
}
