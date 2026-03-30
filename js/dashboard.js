//frontend/js/dashboard.js
import { fetchAPI } from "./utils.js";
import { createLineChart, createPieChart } from "./chart.js";

console.log("Dashboard initialized");

async function loadDashboard() {
    // const students =await fetchAPI("http://localhost:5000/students");
    const students = [
  {
    "name": "Alice Johnson",
    "gpa": 3.8,
    "average": 85,
    "status": "Active"
  },
  {
    "name": "Bob Smith",
    "gpa": 3.2,
    "average": 78,
    "status": "Active"
  },
  {
    "name": "Charlie Brown",
    "gpa": 4.0,
    "average": 92,
    "status": "Graduated"
  },
  {
    "name": "Diana Prince",
    "gpa": 3.5,
    "average": 82,
    "status": "Active"
  },
  {
    "name": "Eve Adams",
    "gpa": 2.9,
    "average": 75,
    "status": "Probation"
  }
];
    updateStudentCards(students);
    const labels = students.map(s => s.name);
    const scores = students.map(s => s.average);
    createLineChart(labels, scores);
}

function updateStudentCards(students) {
    const container = document.getElementById("student-cards");
    container.innerHTML = "";
    students.forEach(s => {
        const card = document.createElement("div");
        card.classList.add("student-card");
        card.innerHTML = 
            <><h3>${s.name}</h3><p>GPA: ${s.gpa.toFixed(2)}</p><p>Average: ${s.average}</p><p>Status: ${s.status}</p></>
        ;
        container.appendChild(card);
    });
}

document.addEventListener("DOMContentLoaded", loadDashboard);