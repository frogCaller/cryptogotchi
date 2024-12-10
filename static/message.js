// Toggle dropdown visibility
function toggleDropdown(event) {
    const dropdown = document.getElementById("dropdownMenu");
    dropdown.classList.toggle("show");
}

// Close the dropdown if the user clicks outside of it
window.onclick = function (event) {
    if (!event.target.closest('.dropdown')) {
        const dropdowns = document.getElementsByClassName("dropdown-content");
        for (let i = 0; i < dropdowns.length; i++) {
            const openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
};
      
// Default font size and font index
let fontSize = 16;
let fontIndex = 0;
let textAlign = "left"; // Default text alignment
let verticalAlign = "top"; // Default vertical alignment
let fontStyle = 1; // Default font style
let darkMode = false; // Default dark mode
let rotation = 180; // Default rotation

// List of 7 fonts
const fonts = [
    "Font1",
    "Font2",
    "Font3",
    "Font4",
    "Font5",
    "Font6",
    "Font7"
];

// Get references to the textarea and buttons
const textBox = document.getElementById("textBox");
const increaseButton = document.getElementById("increaseTextHeight");
const decreaseButton = document.getElementById("decreaseTextHeight");
const currentTextHeightDisplay = document.getElementById("currentTextHeight");
const previousFontButton = document.getElementById("previousFont");
const nextFontButton = document.getElementById("nextFont");
const currentTextStyleDisplay = document.getElementById("currentTextStyle");
const justifyLeftButton = document.getElementById("justifyLeft");
const justifyCenterButton = document.getElementById("justifyCenter");
const justifyRightButton = document.getElementById("justifyRight");
const alignTopButton = document.getElementById("alignTop");
const alignMiddleButton = document.getElementById("alignMiddle");
const alignBottomButton = document.getElementById("alignBottom");
const displayButton = document.getElementById("displayButton");

// Adjust font size based on screen size
function adjustFontSize() {
    const fontSizeElement = document.getElementById("currentTextHeight");
    let einkFontSize = parseInt(fontSizeElement.textContent, 10);

    if (window.innerWidth <= 768) {
        // Mobile devices
        textBox.style.fontSize = `${einkFontSize}px`;
    } else {
        // Desktop devices (double the font size for desktop)
        textBox.style.fontSize = `${einkFontSize * 2}px`;
    }
}

// Call adjustFontSize on page load and whenever the window is resized
window.addEventListener("DOMContentLoaded", adjustFontSize);
window.addEventListener("resize", adjustFontSize);

// Update text height display
function updateTextHeightDisplay() {
    const fontSizeElement = document.getElementById("currentTextHeight");
    const einkFontSize = parseInt(fontSizeElement.textContent, 10);

    // Adjust font size dynamically
    adjustFontSize();

    // Ensure the textarea's font size matches the calculated size
    if (window.innerWidth <= 768) {
        textBox.style.fontSize = `${einkFontSize}px`;
    } else {
        textBox.style.fontSize = `${einkFontSize * 2}px`;
    }
}

// Increase text size
document.getElementById("increaseTextHeight").addEventListener("click", () => {
    const fontSizeElement = document.getElementById("currentTextHeight");
    let einkFontSize = parseInt(fontSizeElement.textContent, 10);

    fontSize += 1; // Increment font size
    fontSizeElement.textContent = einkFontSize; // Update displayed font size
    updateTextHeightDisplay();
});

// Decrease text size
document.getElementById("decreaseTextHeight").addEventListener("click", () => {
    const fontSizeElement = document.getElementById("currentTextHeight");
    let einkFontSize = parseInt(fontSizeElement.textContent, 10);

    if (einkFontSize > 10) {
        fontSize -= 1; // Decrement font size
        fontSizeElement.textContent = einkFontSize; // Update displayed font size
        updateTextHeightDisplay();
    }
});

// Ensure the initial font size is set correctly on load
document.addEventListener("DOMContentLoaded", updateTextHeightDisplay);

// Update text height display
function updateTextStyleDisplay() {
    currentTextStyleDisplay.textContent = fontStyle; // Update the display
}
// Increase text size
increaseButton.addEventListener("click", () => {
    const fontSizeElement = document.getElementById("currentTextHeight");
    let einkFontSize = parseInt(fontSizeElement.textContent, 10);

    einkFontSize += 1; // Increment font size
    fontSizeElement.textContent = einkFontSize; // Update displayed font size
    updateTextHeightDisplay();
});
// Decrease text size
decreaseButton.addEventListener("click", () => {
    const fontSizeElement = document.getElementById("currentTextHeight");
    let einkFontSize = parseInt(fontSizeElement.textContent, 10);

    if (einkFontSize > 10) {
        einkFontSize -= 1; // Decrement font size
        fontSizeElement.textContent = einkFontSize; // Update displayed font size
        updateTextHeightDisplay();
    }
});


// Go to the previous font
previousFontButton.addEventListener("click", () => {
    fontIndex = (fontIndex - 1 + fonts.length) % fonts.length;
    textBox.style.fontFamily = fonts[fontIndex];
    fontStyle = fontIndex + 1; // Font styles are 1-indexed in write.py
    updateTextStyleDisplay();
});

// Go to the next font
nextFontButton.addEventListener("click", () => {
    fontIndex = (fontIndex + 1) % fonts.length;
    textBox.style.fontFamily = fonts[fontIndex];
    fontStyle = fontIndex + 1; // Font styles are 1-indexed in write.py
    updateTextStyleDisplay();
});

// Justify text
justifyLeftButton.addEventListener("click", () => {
    textBox.style.textAlign = "left";
    textAlign = "left";
});
justifyCenterButton.addEventListener("click", () => {
    textBox.style.textAlign = "center";
    textAlign = "center";
});
justifyRightButton.addEventListener("click", () => {
    textBox.style.textAlign = "right";
    textAlign = "right";
});
        
// Vertical alignment
alignTopButton.addEventListener("click", () => {
    verticalAlign = "flex-start"; // Top alignment for flexbox
    textBox.style.alignItems = verticalAlign;
});

alignMiddleButton.addEventListener("click", () => {
    verticalAlign = "center"; // Center alignment for flexbox
    textBox.style.alignItems = verticalAlign;
});

alignBottomButton.addEventListener("click", () => {
    verticalAlign = "flex-end"; // Bottom alignment for flexbox
    textBox.style.alignItems = verticalAlign;
});

const scriptsToTerminate = ['cryptogotchi.py', 'time.py', 'write.py', 'weather.py']; // List of scripts to terminate

// Function to stop all scripts and start `write.py`
async function displayMessage() {
    const message = textBox.innerText.trim(); // Get message content

    // Ensure the message isn't empty
    if (!message) {
        showNotification("Message cannot be empty!", true);
        return;
    }

    const requestBody = {
        kill_scripts: scriptsToTerminate, // Scripts to terminate
        start_script: "write.py", // Script to start
        script_args: {
            message: message,
            font: fontSize, // Use the globally updated `fontSize`
            justify: textAlign,
            vertical_align: verticalAlign,
            font_style: fontStyle,
            dark_mode: darkMode ? "true" : "false", // Pass boolean as string
            rotate: rotation
        }
    };

    console.log("Sending request:", requestBody); // Log payload for debugging

    try {
        const response = await fetch("/manage-script", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();
        console.log("Response:", data);

        if (data.success) {
            showNotification("Message displayed successfully!");
        } else {
            showNotification(`Error displaying message: ${JSON.stringify(data.details)}`, true);
        }
    } catch (error) {
        console.error("Error displaying message:", error);
        showNotification("Unexpected error occurred while displaying message.", true);
    }
}

// Attach the `displayMessage` function to the Display button
document.getElementById("displayButton").addEventListener("click", displayMessage);

// Function to handle active button state
function setActiveButton(buttonGroupClass, clickedButton) {
    const buttons = document.querySelectorAll(buttonGroupClass);
    buttons.forEach(button => button.classList.remove("active-tool"));
    clickedButton.classList.add("active-tool");
}

// Justify buttons
const justifyButtons = document.querySelectorAll(".justify-button");
justifyButtons.forEach(button => {
    button.addEventListener("click", () => {
        // Set active button for justification
        setActiveButton(".justify-button", button);

        // Update text alignment based on the clicked button
        if (button.id === "justifyLeft") {
            textarea.style.textAlign = "left";
            textAlign = "left";
        } else if (button.id === "justifyCenter") {
            textarea.style.textAlign = "center";
            textAlign = "center";
        } else if (button.id === "justifyRight") {
            textarea.style.textAlign = "right";
            textAlign = "right";
        }
    });
});

// Alignment buttons
const alignButtons = document.querySelectorAll(".align-button");
alignButtons.forEach(button => {
    button.addEventListener("click", () => {
        // Set active button for alignment
        setActiveButton(".align-button", button);

        // Update vertical alignment based on the clicked button
        if (button.id === "alignTop") {
            verticalAlign = "top";
        } else if (button.id === "alignMiddle") {
            verticalAlign = "center";
        } else if (button.id === "alignBottom") {
            verticalAlign = "bottom";
        }
    });
});
document.addEventListener("DOMContentLoaded", () => {
    updateTextHeightDisplay();
    textBox.style.textAlign = textAlign;
    textBox.style.alignItems = verticalAlign;
    const savedMode = localStorage.getItem("theme");
    if (savedMode === "dark-mode") {
        document.body.classList.add("dark-mode");
    } else {
        document.body.classList.remove("dark-mode");
    }
});
document.getElementById('homePageButton').addEventListener('click', () => {
    window.location.href = '/';
});
      
      
      
function setupScriptRunner(buttonId, displayType) {
    const button = document.getElementById(buttonId);

    let isCooldown = false; // Variable to track if the button is on cooldown

    button.addEventListener("click", async () => {
        if (isCooldown) return; // Prevent action if cooldown is active

        try {
            // Show a notification that the operation is starting
            showNotification(`Attempting to display ${displayType}...`);

            // Disable the button and start the cooldown
            isCooldown = true;
            button.disabled = true;

            // Send the POST request to run the script
            const response = await fetch("/display-message", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    display_type: displayType, // Pass the display type
                    font: fontSize,
                    justify: textAlign,
                    vertical_align: verticalAlign,
                    font_style: fontStyle,
                    dark_mode: darkMode,
                    rotate: rotation,
                }),
            });

            if (!response.ok) {
                console.error(`Failed to display ${displayType}`);
                showNotification(`Failed to display ${displayType}.`, true);
            } else {
                const data = await response.json();
                if (data.success) {
                    showNotification(`${displayType.charAt(0).toUpperCase() + displayType.slice(1)} displayed successfully!`);
                } else {
                    showNotification(`Error: ${data.message}`, true);
                }
            }
        } catch (error) {
            console.error(`Error displaying ${displayType}:`, error);
            showNotification(`Error displaying ${displayType}.`, true);
        } finally {
            // Re-enable the button after 10 seconds
            setTimeout(() => {
                isCooldown = false;
                button.disabled = false;
            }, 10000);
        }
    });
}

function showNotification(message, isError = false) {
    // Create notification element
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.padding = '10px 20px';
    notification.style.backgroundColor = isError ? '#f8d7da' : '#d1e7dd';
    notification.style.color = isError ? '#721c24' : '#0f5132';
    notification.style.border = `1px solid ${isError ? '#f5c6cb' : '#c3e6cb'}`;
    notification.style.borderRadius = '5px';
    notification.style.boxShadow = '0px 4px 6px rgba(0, 0, 0, 0.1)';
    notification.style.fontSize = '14px';
    notification.style.zIndex = '1000';
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s';

   // Add to body
    document.body.appendChild(notification);
 
    // Fade in
    setTimeout(() => {
        notification.style.opacity = '1';
    }, 50);

    // Remove after 2 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300); // Remove after fade out
    }, 2500);
}

setupScriptRunner("runFortuneButton", "fortune");
setupScriptRunner("runJokeButton", "joke");
