async function loadProgress(practiceId) {
    const res = await fetch(`/api/progress/${practiceId}`);
    if (!res.ok) return null;
    return res.json();
}

function renderChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext("2d");

    new Chart(ctx, {
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: "Выполнение",
                    data: data.completed,
                    type: "bar",
                    backgroundColor: "rgba(25, 135, 84, 0.4)",
                    borderColor: "rgba(25, 135, 84, 1)",
                    borderWidth: 1,
                    yAxisID: "y1"
                },
                {
                    label: "Серия (streak)",
                    data: data.streak,
                    type: "line",
                    tension: 0.2,
                    borderColor: "rgba(13, 110, 253, 1)",
                    backgroundColor: "rgba(13, 110, 253, 0.1)",
                    yAxisID: "y2",
                    pointRadius: 0,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y1: {
                    type: "linear",
                    position: "left",
                    min: 0,
                    max: 1,
                    grid: { display: false },
                    ticks: { stepSize: 1 }
                },
                y2: {
                    type: "linear",
                    position: "right",
                    min: 0,
                    grid: { display: true }
                }
            },
            plugins: {
                legend: { display: true },
                tooltip: { mode: "index", intersect: false }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", async () => {
    for (const practice of window.ANALYTICS_PRACTICES) {
        const data = await loadProgress(practice.id);
        if (data) {
            renderChart(`chart-${practice.id}`, data);
        }
    }
});
