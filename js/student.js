// frontend/js/student.js
import { fetchAPI } from "./utils.js";

export async function addStudent(student) {
    await fetchAPI("http://localhost:5000/add", {
        method: "POST",
        body: JSON.stringify(student)
    });
    alert("Student added!");
}