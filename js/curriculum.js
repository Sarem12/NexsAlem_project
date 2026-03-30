// frontend/js/curriculum.js
import { fetchAPI } from "./utils.js";

export async function loadCurriculum() {
    const courses = await fetchAPI("http://localhost:5000/curriculum");
    const container = document.getElementById("curriculum");
    container.innerHTML = "";
    courses.forEach(course => {
        const card = document.createElement("div");
        card.classList.add("course-card");
        card.innerHTML = <><h4>${course.name}</h4><p>${course.description}</p></>;
        container.appendChild(card);
    });
}
