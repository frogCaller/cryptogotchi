// Get canvas and context
const canvas = document.getElementById('drawingCanvas');
const ctx = canvas.getContext('2d');

// Initialize drawing mode as default
let isDrawing = false;
let brushSize = 2; // Initial brush size
let isEraser = false; // Default to drawing mode
ctx.fillStyle = "black"; // Default drawing color
      
function initializeCanvas() {
    ctx.fillStyle = "#ffffff"; // Set fill color to white
    ctx.fillRect(0, 0, canvas.width, canvas.height); // Fill the canvas
    ctx.fillStyle = "black"; // Reset to black for drawing
}
window.onload = initializeCanvas;

// Highlight the draw button by default
document.getElementById('drawButton').classList.add('active-tool');

// Utility to get correct coordinates for both mouse and touch events
function getCoordinates(event) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    if (event.touches) {
        const touch = event.touches[0] || event.changedTouches[0];
        return {
            x: (touch.clientX - rect.left) * scaleX,
            y: (touch.clientY - rect.top) * scaleY,
        };
    } else {
        return {
            x: (event.clientX - rect.left) * scaleX,
            y: (event.clientY - rect.top) * scaleY,
        };
    }
}

// Start drawing
function startDrawing(event) {
    isDrawing = true;
    const { x, y } = getCoordinates(event);
    draw(x, y);
}

// Stop drawing
function stopDrawing() {
    isDrawing = false;
    ctx.beginPath(); // Reset the path
    lastX = null;
    lastY = null;
}
        
let lastX = null;
let lastY = null;
function draw(x, y) {
    if (!isDrawing) return;

    ctx.beginPath();
    ctx.lineWidth = brushSize * 2; // Set line width to match brush size
    ctx.lineCap = "round"; // Smooth line ends
    ctx.strokeStyle = isEraser ? "#ffffff" : "black"; // Eraser or draw color

    if (lastX !== null && lastY !== null) {
        ctx.moveTo(lastX, lastY); // Move to the last position
        ctx.lineTo(x, y); // Draw to the current position
        ctx.stroke();
    }

    lastX = x; // Update the last position
    lastY = y;
}

// Add event listeners for mouse events
canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mouseup', stopDrawing);
canvas.addEventListener('mousemove', (event) => {
    if (!isDrawing) return;
    const { x, y } = getCoordinates(event);
    draw(x, y);
});

// Add event listeners for touch events
canvas.addEventListener('touchstart', (event) => {
    startDrawing(event);
    event.preventDefault(); // Prevent scrolling
});
canvas.addEventListener('touchmove', (event) => {
    if (!isDrawing) return;
    const { x, y } = getCoordinates(event);
    draw(x, y);
    event.preventDefault(); // Prevent scrolling
});
canvas.addEventListener('touchend', stopDrawing);
      
        
// State for line drawing
let isLineDrawing = false;
let lineStart = null; // Stores the start point for the line

// Save the current canvas state to enable undo/redo and previews
let lastCanvasState = null;

function saveCanvasState() {
    lastCanvasState = canvas.toDataURL();
}

function restoreCanvasState() {
    if (lastCanvasState) {
        const img = new Image();
        img.src = lastCanvasState;
        img.onload = () => ctx.drawImage(img, 0, 0);
    }
}

// Line button functionality
document.getElementById('lineButton').addEventListener('click', () => {
    isLineDrawing = !isLineDrawing; // Toggle line drawing mode
    if (isLineDrawing) {
        document.getElementById('lineButton').classList.add('active-tool');
    } else {
        document.getElementById('lineButton').classList.remove('active-tool');
    }
});

// Handle line drawing
canvas.addEventListener('mousedown', (event) => {
    if (!isLineDrawing) return;
    saveCanvasState(); // Save state for preview
    const { x, y } = getCoordinates(event);
    lineStart = { x, y }; // Set the start point
});

canvas.addEventListener('mousemove', (event) => {
    if (!isLineDrawing || !lineStart) return;
    restoreCanvasState(); // Restore the saved state
    const { x, y } = getCoordinates(event);
    ctx.beginPath();
    ctx.lineWidth = brushSize * 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = isEraser ? "#ffffff" : "black"; // Use current tool color
    ctx.moveTo(lineStart.x, lineStart.y);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.closePath();
});

canvas.addEventListener('mouseup', (event) => {
    if (!isLineDrawing || !lineStart) return;
    const { x, y } = getCoordinates(event);
    ctx.beginPath();
    ctx.lineWidth = brushSize * 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = isEraser ? "#ffffff" : "black";
    ctx.moveTo(lineStart.x, lineStart.y);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.closePath();
    lineStart = null; // Reset line drawing state
});

canvas.addEventListener('touchstart', (event) => {
    if (!isLineDrawing) return;
    saveCanvasState();
    const { x, y } = getCoordinates(event);
    lineStart = { x, y };
    event.preventDefault();
});

canvas.addEventListener('touchmove', (event) => {
    if (!isLineDrawing || !lineStart) return;
    restoreCanvasState();
    const { x, y } = getCoordinates(event);
    ctx.beginPath();
    ctx.lineWidth = brushSize * 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = isEraser ? "#ffffff" : "black";
    ctx.moveTo(lineStart.x, lineStart.y);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.closePath();
    event.preventDefault();
});

canvas.addEventListener('touchend', (event) => {
    if (!isLineDrawing || !lineStart) return;
    const { x, y } = getCoordinates(event.changedTouches[0]);
    ctx.beginPath();
    ctx.lineWidth = brushSize * 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = isEraser ? "#ffffff" : "black";
    ctx.moveTo(lineStart.x, lineStart.y);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.closePath();
    lineStart = null;
    event.preventDefault();
});      
      
// Stacks for undo and redo operations
const undoStack = [];
const redoStack = [];

// Save current canvas state to undo stack
function saveState() {
    undoStack.push(canvas.toDataURL());
    // Clear redo stack whenever a new state is saved
    redoStack.length = 0;
}

// Restore canvas state from a given data URL
function restoreState(stateURL) {
    const img = new Image();
    img.src = stateURL;
    img.onload = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
    };
}

// Undo button functionality
document.getElementById('undoButton').addEventListener('click', () => {
    if (undoStack.length > 0) {
        // Push current state to redo stack
        redoStack.push(canvas.toDataURL());
        // Pop from undo stack and restore
        const previousState = undoStack.pop();
        restoreState(previousState);
    }
});

// Redo button functionality
document.getElementById('redoButton').addEventListener('click', () => {
    if (redoStack.length > 0) {
        // Push current state to undo stack
        undoStack.push(canvas.toDataURL());
        // Pop from redo stack and restore
        const nextState = redoStack.pop();
        restoreState(nextState);
    }
});
// Save canvas state whenever a drawing operation starts
canvas.addEventListener('mousedown', saveState);
canvas.addEventListener('touchstart', (event) => {
    saveState();
    event.preventDefault();
});

// Brush size buttons
document.getElementById('increaseBrush').addEventListener('click', () => {
    brushSize = Math.min(brushSize + 1, 20); // Cap max size at 20
});

document.getElementById('decreaseBrush').addEventListener('click', () => {
    brushSize = Math.max(brushSize - 1, 1); // Cap min size at 1
});

// Draw button functionality
document.getElementById('drawButton').addEventListener('click', () => {
    isEraser = false; // Switch to draw mode
    ctx.fillStyle = "black"; // Set the drawing color to black

    // Highlight active tool
    document.getElementById('drawButton').classList.add('active-tool');
    document.getElementById('eraseButton').classList.remove('active-tool');
});

// Erase button functionality
document.getElementById('eraseButton').addEventListener('click', () => {
    isEraser = true; // Switch to erase mode
    ctx.fillStyle = "#ffffff"; // Set the drawing color to white (eraser)

    // Highlight active tool
    document.getElementById('eraseButton').classList.add('active-tool');
    document.getElementById('drawButton').classList.remove('active-tool');
});

        // Clear button functionality
document.getElementById('clearButton').addEventListener('click', () => {
    saveState();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    isEraser = false; // Reset to draw mode
    ctx.fillStyle = "black"; // Reset drawing color to black
    document.getElementById('drawButton').classList.add('active-tool');
    document.getElementById('eraseButton').classList.remove('active-tool');
});
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
    }, 3000);
}

// Save button functionality
document.getElementById('saveButton').addEventListener('click', () => {
    // Prompt the user for a file name
    const fileName = prompt("Enter a name for your drawing (without extension):", "drawing");
    if (!fileName) {
        showNotification("Save canceled. No file name provided.", true);
        return;
    }
    const dataURL = canvas.toDataURL('image/png');
    // Send the image and file name to the server
    fetch('/save_image', {
        method: 'POST',
        body: JSON.stringify({ 
            image: dataURL,
            file_name: `${fileName}.png` // Append .png extension
        }),
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(`Image saved as ${fileName}.png successfully to the server!`);
        } else {
            showNotification(`Failed to save image: ${data.message}`, true);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error saving image to the server.', true);
    });
});

// Display button functionality
document.getElementById('displayButton').addEventListener('click', () => {
    const dataURL = canvas.toDataURL('image/png'); // Get the image data from the canvas

    // List of scripts to terminate
    const scriptsToTerminate = ['cryptogotchi.py', 'write.py', 'time.py', 'weather.py'];

    // Stop all scripts in the list
    fetch('/manage-script', {
        method: 'POST',
        body: JSON.stringify({ kill_scripts: scriptsToTerminate, start_script: null }),
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        console.log('Scripts terminated:', data.details);

        // Save the image to the server
        return fetch('/save_image', {
            method: 'POST',
            body: JSON.stringify({ image: dataURL }),
            headers: {
                'Content-Type': 'application/json',
            },
        });
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Displaying on e-Ink...', false);

            // Call the /display endpoint to display the image
            return fetch('/display', { method: 'POST' });
        } else {
            throw new Error(`Failed to save image: ${data.message}`);
        }
    })
    .then(displayResponse => displayResponse.json())
    .then(displayData => {
        if (displayData.success) {
            showNotification(displayData.message, false);
        } else {
            showNotification(displayData.message, true);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error stopping scripts, saving, or displaying the image.', true);
    });
});


document.addEventListener("DOMContentLoaded", () => {
    const savedMode = localStorage.getItem("theme");
    if (savedMode === "dark-mode") {
        document.body.classList.add("dark-mode");
    } else {
        document.body.classList.remove("dark-mode");
    }
});
document.getElementById('homePageButton').addEventListener('click', () => {
    window.location.href = '/'; // Redirect to draw.html
});
      
      
      
const fileInput = document.getElementById('fileInput');
const importButton = document.getElementById('importButton');
// Open file selector when the import button is clicked
importButton.addEventListener('click', () => {
    fileInput.click();
});      
// Handle file selection
fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();

        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                // Clear the canvas
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = "#ffffff"; // Set background to white
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                // Draw the image, scaled to fit the canvas
                const scaleX = canvas.width / img.width;
                const scaleY = canvas.height / img.height;
                const scale = Math.min(scaleX, scaleY); // Maintain aspect ratio

                const imgWidth = img.width * scale;
                const imgHeight = img.height * scale;

                const x = (canvas.width - imgWidth) / 2; // Center horizontally
                const y = (canvas.height - imgHeight) / 2; // Center vertically

                ctx.drawImage(img, x, y, imgWidth, imgHeight);
            };
            img.src = e.target.result; // Set the image source to the file data
        };

        reader.readAsDataURL(file); // Read the file as a Data URL
    } else {
        showNotification('Please select a valid image file.', true);
    }
});      
      
 // Drag-and-drop functionality
 canvas.addEventListener('dragover', (event) => {
     event.preventDefault(); // Prevent default behavior to allow dropping
 });
 
 canvas.addEventListener('drop', (event) => {
     event.preventDefault(); // Prevent default behavior
 
     // Get the file from the drop event
     const file = event.dataTransfer.files[0];
     if (file && file.type.startsWith('image/')) {
         const reader = new FileReader();
 
         // When the file is loaded, draw it on the canvas
         reader.onload = (e) => {
             const img = new Image();
             img.onload = () => {
                 // Clear the canvas
                 ctx.clearRect(0, 0, canvas.width, canvas.height);
                 ctx.fillStyle = "#ffffff"; // Set background to white
                 ctx.fillRect(0, 0, canvas.width, canvas.height);
 
                 // Draw the image, scaled to fit the canvas
                 const scaleX = canvas.width / img.width;
                 const scaleY = canvas.height / img.height;
                 const scale = Math.min(scaleX, scaleY); // Maintain aspect ratio
 
                 const imgWidth = img.width * scale;
                 const imgHeight = img.height * scale;
 
                 const x = (canvas.width - imgWidth) / 2; // Center horizontally
                 const y = (canvas.height - imgHeight) / 2; // Center vertically
 
                 ctx.drawImage(img, x, y, imgWidth, imgHeight);
             };
             img.src = e.target.result; // Set the image source to the file data
         };
 
         reader.readAsDataURL(file); // Read the file as a Data URL
     } else {
         showNotification('Please drop a valid image file.', true);
     }
 });
