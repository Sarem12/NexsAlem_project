// frontend/js/realtime.js
const socket = io("http://localhost:5000");

socket.on("update_chart", async (data) => {
    console.log("New student data:", data);
    await loadDashboard(); // refresh dashboard & charts
});