// frontend/js/utils.js
export async function fetchAPI(url, options = {}) {
    const token = localStorage.getItem("token");
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
        "Authorization": "Bearer " + token
    };
    const res = await fetch(url, { ...options, headers });
    return await res.json();
}

export function formatGPA(gpa) {
    return gpa.toFixed(2);
}
