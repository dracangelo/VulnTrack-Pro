// frontend/app.js
const API_BASE = "";

function authHeaders() {
    const token = localStorage.getItem("token");
    return token ? { "Authorization": `Bearer ${token}` } : {};
}

// --- Login form handler (login.html) ---
document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("username").value;
            const password = document.getElementById("password").value;

            const formData = new URLSearchParams();
            formData.append("username", username);
            formData.append("password", password);

            const res = await fetch("/auth/login", {
                method: "POST",
                body: formData,
            });

            const data = await res.json();
            if (res.ok && data.access_token) {
                localStorage.setItem("token", data.access_token);
                window.location.href = "/";
            } else {
                document.getElementById("message").innerText = data.detail || "Login failed";
            }
        });
    }

    const addTargetForm = document.getElementById("addTargetForm");
    if (addTargetForm) {
        addTargetForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const name = document.getElementById("targetName").value.trim();
            const ip = document.getElementById("targetIP").value.trim();
            if (!name || !ip) return alert("Name & IP required");

            await fetch("/api/targets/", {
                method: "POST",
                headers: { "Content-Type": "application/json", ...authHeaders() },
                body: JSON.stringify({ name, ip })
            });

            document.getElementById("targetName").value = "";
            document.getElementById("targetIP").value = "";
            loadTargets();
        });

        // load targets on page load
        loadTargets();
    }

    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            localStorage.removeItem("token");
            window.location.href = "/login";
        });
    }
});

async function loadTargets() {
    const res = await fetch("/api/targets/", { headers: authHeaders() });
    if (!res.ok) {
        if (res.status === 401) {
            localStorage.removeItem("token");
            window.location.href = "/login";
            return;
        }
        console.error("Failed to load targets");
        return;
    }
    const data = await res.json();
    const list = document.getElementById("targetList");
    list.innerHTML = "";
    data.targets.forEach(target => {
        const item = document.createElement("div");
        item.className = "p-3 bg-gray-700 rounded flex justify-between items-center";
        item.innerHTML = `
            <div>
                <div class="font-semibold">${target.name || "(no name)"}</div>
                <div class="text-sm text-gray-300">${target.address}</div>
            </div>
        `;
        list.appendChild(item);
    });
}
