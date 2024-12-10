// Open tabs for different sections
let currentTab = 'cryptoList'; // Currently active tab
let previousTab = 'cryptoList'; // Last active tab before switching

function openTab(event, tabId) {
    const containers = document.querySelectorAll('.square-container');
    const selectedContainer = document.getElementById(tabId);

    // If clicking on the currently active tab, switch back to the previous tab
    if (currentTab === tabId && tabId === "settings" && previousTab) {
        tabId = previousTab; // Switch to the previous tab
        currentTab = null; // Clear current tab to allow toggling back
        openTab(event, tabId); // Call the function recursively for the previous tab
        return; // Exit to avoid resetting states below
    }

    // Update the previous tab before switching
    previousTab = currentTab;
    currentTab = tabId;

    // Deactivate all tabs
    containers.forEach(container => container.classList.remove('active'));

    // Activate the selected tab
    selectedContainer.classList.add('active');

    // Clear the search bar whenever a tab is clicked
    document.getElementById("search-bar").value = ""; // Clear the search bar
    updateCoinsTable(coins); // Reset the coins table with the full list

    // Reset the favorites list when the "Favorites" tab is clicked
    if (tabId === "favorites") {
        updateFavoritesTable(coins); // Refresh the favorites list with the full coins data
    }

    // If the "Settings" tab is clicked, load settings
    if (tabId === "settings") {
        loadSettings();
    }
}


document.getElementById('cryptoList').classList.add('active');

const getCoins = async () => {
    try {
        const response = await fetch("/get-coins");
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Fetched coins:", data);
        return data.coins;
    } catch (error) {
        console.error("Error fetching coins:", error);
    }
};


// Filter coins based on search query
const filterCoins = (query, coins) => {
    return coins.filter(
        (coin) =>
            coin.name.toLowerCase().includes(query.toLowerCase()) ||
            coin.display.toLowerCase().includes(query.toLowerCase())
    );
};

// Update the coins table dynamically
const updateCoinsTable = (coins) => {
    const tableBody = document.getElementById("coins-table-body");
    tableBody.innerHTML = ""; // Clear the existing table content

    // Show all coins from coins.json
    coins.forEach((coin) => {
        const row = document.createElement("tr");

        const rankCell = document.createElement("td");
        rankCell.textContent = coin.rank || "-";
        row.appendChild(rankCell);

        const nameCell = document.createElement("td");
        nameCell.textContent = coin.name;
        row.appendChild(nameCell);

        const displayCell = document.createElement("td");
        displayCell.textContent = coin.display;
        row.appendChild(displayCell);

        const priceCell = document.createElement("td");
        priceCell.textContent = coin.price ? `$${coin.price}` : "-";
        priceCell.style.fontWeight = "bold";
        row.appendChild(priceCell);

        const toggleCell = document.createElement("td");
        const toggleLabel = document.createElement("label");
        toggleLabel.classList.add("switch");

        const toggleInput = document.createElement("input");
        toggleInput.type = "checkbox";
        toggleInput.checked = coin.show; // Use the show property
        toggleInput.addEventListener("change", () => {
            fetch("/toggle-coin", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ coinId: coin.id, show: toggleInput.checked }),
            }).then((response) => {
                if (response.ok) {
                    console.log(`Updated show status for ${coin.id}`);
                    coin.show = toggleInput.checked; // Update locally
                    updateFavoritesTable(coins); // Refresh favorites dynamically
                }
            });
        });

        toggleLabel.appendChild(toggleInput);
        const slider = document.createElement("span");
        slider.classList.add("slider", "round");
        toggleLabel.appendChild(slider);
        toggleCell.appendChild(toggleLabel);

        row.appendChild(toggleCell);
        tableBody.appendChild(row);
    });
};

// Add event listener to search bar
document.getElementById("search-bar").addEventListener("input", (event) => {
    const query = event.target.value.toLowerCase();
    const activeTab = document.querySelector('.square-container.active').id;

    if (activeTab === "favorites") {
        const favoriteCoins = coins.filter((coin) => coin.show);
        const filteredFavorites = filterCoins(query, favoriteCoins);
        updateFavoritesTable(filteredFavorites);
    } else {
        const filteredCoins = filterCoins(query, coins);
        updateCoinsTable(filteredCoins);
    }
});


// Update the favorites table
const updateFavoritesTable = (coins) => {
    const favTableBody = document.getElementById("fav-coins-table-body");
    favTableBody.innerHTML = ""; // Clear existing content

    // Filter only coins with show: true for the favorites list
    const favoriteCoins = coins.filter((coin) => coin.show);

    if (favoriteCoins.length > 0) {
        favoriteCoins.forEach((coin) => {
            const row = document.createElement("tr");

            const rankCell = document.createElement("td");
            rankCell.textContent = coin.rank || "-";
            row.appendChild(rankCell);

            const nameCell = document.createElement("td");
            nameCell.textContent = coin.name;
            row.appendChild(nameCell);

            const displayCell = document.createElement("td");
            displayCell.textContent = coin.display;
            row.appendChild(displayCell);

            const priceCell = document.createElement("td");
            priceCell.textContent = coin.price ? `$${coin.price}` : "-";
            priceCell.style.fontWeight = "bold";
            priceCell.style.color = "#2196f3";
            row.appendChild(priceCell);

            favTableBody.appendChild(row);
        });
    } else {
        const noFavoritesRow = document.createElement("tr");
        const noFavoritesCell = document.createElement("td");
        noFavoritesCell.colSpan = 4;
        noFavoritesCell.textContent = "No favorite coins added.";
        noFavoritesRow.appendChild(noFavoritesCell);
        favTableBody.appendChild(noFavoritesRow);
    }
};

// Auto-refresh for coins
const autoRefresh = ({ dataFunction, onComplete, interval = 30000 }) => {
    const fetchAndUpdate = async () => {
        try {
            const data = await dataFunction();
            onComplete(data);
        } catch (error) {
            console.error("Error in auto-refresh:", error);
        }
    };

    fetchAndUpdate(); // Run once immediately
    setInterval(fetchAndUpdate, interval); // Schedule periodic updates
};

// Initialize auto-refresh and update tables
document.addEventListener("DOMContentLoaded", () => {
    autoRefresh({
        dataFunction: getCoins,
        onComplete: (coins) => {
            updateCoinsTable(coins);
            updateFavoritesTable(coins);
        },
        interval: 90000, // Refresh every 90 seconds
    });
});

// Fetch and update quotes
setInterval(() => {
    fetch("/get-quote")
        .then(response => response.json())
        .then(data => {
            document.getElementById("quote").textContent = data.quote;
        })
        .catch(error => console.error("Error fetching quote:", error));
}, 10000);


// Button event listeners
document.getElementById("update-list").addEventListener("click", () => {
    fetch("/switch-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script: "updateList.py" }),
    })
    .then(response => response.json())
    .catch(error => console.error("Error running script:", error));
});
