let currentTab = 'cryptoList';
let previousTab = 'cryptoList';
let coins = [];

function openTab(event, tabId) {
    const containers = document.querySelectorAll('.square-container');
    const selectedContainer = document.getElementById(tabId);

    if (currentTab === tabId && tabId === "settings" && previousTab) {
        tabId = previousTab; 
        currentTab = null;
        openTab(event, tabId);
        return; 
    }

    previousTab = currentTab;
    currentTab = tabId;

    containers.forEach(container => container.classList.remove('active'));

    selectedContainer.classList.add('active');

    document.getElementById("search-bar").value = ""; 
    updateCoinsTable(coins); 

    if (tabId === "favorites") {
        updateFavoritesTable(coins); 
    }

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

const filterCoins = (query, coins) => {
    return coins.filter(
        (coin) =>
            coin.name.toLowerCase().includes(query.toLowerCase()) ||
            coin.display.toLowerCase().includes(query.toLowerCase())
    );
};

const updateCoinsTable = (coins) => {
    const tableBody = document.getElementById("coins-table-body");
    tableBody.innerHTML = ""; 

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
        toggleInput.checked = coin.show; 
        toggleInput.addEventListener("change", () => {
            fetch("/toggle-coin", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ coinId: coin.id, show: toggleInput.checked }),
            }).then((response) => {
                if (response.ok) {
                    console.log(`Updated show status for ${coin.id}`);
                    coin.show = toggleInput.checked;
                    updateFavoritesTable(coins);
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


const updateFavoritesTable = (coins) => {
    const favTableBody = document.getElementById("fav-coins-table-body");
    favTableBody.innerHTML = "";

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

const autoRefresh = ({ dataFunction, onComplete, interval = 30000 }) => {
    const fetchAndUpdate = async () => {
        try {
            const data = await dataFunction();
            onComplete(data);
        } catch (error) {
            console.error("Error in auto-refresh:", error);
        }
    };

    fetchAndUpdate(); 
    setInterval(fetchAndUpdate, interval); 
};

document.addEventListener("DOMContentLoaded", () => {
    autoRefresh({
        dataFunction: getCoins,
        onComplete: (data) => {
            coins = data;
            updateCoinsTable(coins);
            updateFavoritesTable(coins);
        },
        interval: 90000,
    });
});

setInterval(() => {
    fetch("/get-quote")
        .then(response => response.json())
        .then(data => {
            document.getElementById("quote").textContent = data.quote;
        })
        .catch(error => console.error("Error fetching quote:", error));
}, 10000);


document.getElementById("update-list").addEventListener("click", () => {
    fetch("/switch-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script: "updateList.py" }),
    })
    .then(response => response.json())
    .catch(error => console.error("Error running script:", error));
});
