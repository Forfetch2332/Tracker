document.addEventListener("DOMContentLoaded", () => {

    const buttons = document.querySelectorAll(".toggle-btn");

    buttons.forEach(btn => {
        btn.addEventListener("click", async () => {

            const practiceId = btn.dataset.practiceId;

            const response = await fetch(`/practice/${practiceId}/toggle`, {
                method: "POST"
            });

            const data = await response.json();

            updateButton(btn, data);
            updateStreak(data);
            updateProgress(data);
        });
    });
});


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

    updateCard(btn, completed);
}


function updateCard(btn, completed) {
    const card = btn.closest(".card");

    if (!card) return;

    if (completed) {
        card.classList.add("completed");
        card.classList.add("completed-animate");

        setTimeout(() => {
            card.classList.remove("completed-animate");
        }, 300);

    } else {
        card.classList.remove("completed");
    }
}


function updateStreak(data) {
    const block = document.getElementById(`streak-${data.practice_id}`);

    if (data.completed) {
        block.innerHTML = `<span class="text-success">Серия: ${data.streak} дней</span>`;
    } else {
        block.innerHTML = "";
    }
}


function updateProgress(data) {
    const bar14 = document.getElementById(`progress-14-${data.practice_id}`);
    const text14 = document.getElementById(`progress-text-14-${data.practice_id}`);

    bar14.style.transition = "width 0.4s ease";
    bar14.style.width = `${data.progress_14}%`;
    text14.innerText = `Прогресс 14 дней: ${data.progress_14}%`;

    const bar30 = document.getElementById(`progress-30-${data.practice_id}`);
    const text30 = document.getElementById(`progress-text-30-${data.practice_id}`);

    bar30.style.transition = "width 0.4s ease";
    bar30.style.width = `${data.progress_30}%`;
    text30.innerText = `Прогресс 30 дней: ${data.progress_30}%`;

    const bar60 = document.getElementById(`progress-60-${data.practice_id}`);
    const text60 = document.getElementById(`progress-text-60-${data.practice_id}`);

    bar60.style.transition = "width 0.4s ease";
    bar60.style.width = `${data.progress_60}%`;
    text60.innerText = `Прогресс 60 дней: ${data.progress_60}%`;
}
