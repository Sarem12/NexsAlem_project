//frontend/js/mentalHealth.js
export function updateStress(student) {
    const bar = document.getElementById(stress-${student.id});
    bar.style.width = ${student.stressLevel}%;
    bar.style.backgroundColor = student.stressLevel > 70 ? "red" : "green";
}