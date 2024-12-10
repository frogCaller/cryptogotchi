const body = document.body;
const savedMode = localStorage.getItem('theme');
if (savedMode) {
    body.classList.add(savedMode);
}

const setInitialTheme = () => {
    const body = document.body;
    const darkModeToggle = document.getElementById("darkModeToggle");
    const icon = darkModeToggle.querySelector("i");

    // Check saved theme in localStorage
    const savedMode = localStorage.getItem("theme");
    if (savedMode === "dark-mode") {
        body.classList.add("dark-mode"); // Apply dark mode
        icon.classList.remove("fa-moon");
        icon.classList.add("fa-sun"); // Set icon to sun
    } else {
        body.classList.remove("dark-mode"); // Apply light mode
        icon.classList.remove("fa-sun");
        icon.classList.add("fa-moon"); // Set icon to moon
    }
};

// Toggle dark mode and update icon
const toggleDarkMode = () => {
    const body = document.body;
    const darkModeToggle = document.getElementById("darkModeToggle");
    const icon = darkModeToggle.querySelector("i");

    if (body.classList.contains("dark-mode")) {
        // Switch to light mode
        body.classList.remove("dark-mode");
        localStorage.setItem("theme", "");
        icon.classList.remove("fa-sun");
        icon.classList.add("fa-moon"); // Change to moon icon
    } else {
        // Switch to dark mode
        body.classList.add("dark-mode");
        localStorage.setItem("theme", "dark-mode");
        icon.classList.remove("fa-moon");
        icon.classList.add("fa-sun"); // Change to sun icon
    }
};

document.addEventListener("DOMContentLoaded", setInitialTheme); // Set theme on page load
document.getElementById("darkModeToggle").addEventListener("click", toggleDarkMode);

// Fetch and update system information
const fetchSystemInfo = () => {
    fetch("/system-info")
        .then(response => response.json())
        .then(data => {
            document.getElementById("cpu-usage").textContent = `${data.cpu_usage}%`;
            document.getElementById("memory-usage").textContent = `${data.memory_usage}%`;
            document.getElementById("cpu-temp").textContent = data.cpu_temp;
            document.getElementById("storage-usage").textContent = `${data.storage_percent}%`;
        })
        .catch(error => console.error("Error fetching system info:", error));
};
setInterval(fetchSystemInfo, 15000);
fetchSystemInfo();
