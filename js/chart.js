// frontend/js/chart.js
export function createLineChart(labels, data) {
    const ctx = document.getElementById("lineChart").getContext("2d");
    new Chart(ctx, {
        type: "line",
        data: { labels, datasets: [{ label: "Student Average", data, borderColor: "cyan", tension: 0.4 }] },
        options: { responsive: true, animation: { duration: 1500 } }
    });
}

export function createPieChart(labels, data) {
    const ctx = document.getElementById("pieChart").getContext("2d");
    new Chart(ctx, {
        type: "pie",
        data: { labels, datasets: [{ data, backgroundColor: ["#38bdf8","#facc15","#f43f5e","#a855f7"] }] },
        options: { responsive: true }
    });
}