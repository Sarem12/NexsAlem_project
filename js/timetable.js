// frontend/js/timetable.js
export function renderTimetable(timetableData) {
    const table = document.getElementById("timetable");
    table.innerHTML = "";
    timetableData.forEach(slot => {
        const row = document.createElement("tr");
        row.innerHTML = <><td>${slot.time}</td><td>${slot.subject}</td></>;
        table.appendChild(row);
    });
}