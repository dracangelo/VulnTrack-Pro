const API_BASE = "http://127.0.0.1:5000/api";

async function loadTargets() {
    const res = await fetch(`${API_BASE}/targets/`);
    const data = await res.json();

    const list = document.getElementById("targetList");
    list.innerHTML = "";

    data.targets.forEach(target => {
        const item = document.createElement("div");
        item.className = "p-4 bg-gray-700 rounded flex justify-between items-center";

        item.innerHTML = `
            <div>
              <p class="font-semibold">${target.name}</p>
              <p class="text-sm text-gray-300">${target.ip}</p>
            </div>
        `;

        list.appendChild(item);
    });
}

document.getElementById("addTargetForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("targetName").value.trim();
    const ip = document.getElementById("targetIP").value.trim();

    if (!name || !ip) return alert("Name & IP required");

    await fetch(`${API_BASE}/targets/`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ name, ip })
    });

    document.getElementById("targetName").value = "";
    document.getElementById("targetIP").value = "";

    loadTargets();
});

// Load targets on page open
loadTargets();
