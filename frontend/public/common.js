// Shared helpers for the FairLine pages.
// Uses the same "token" the login page (index.html) saves.

function getToken() {
    return localStorage.getItem("token");
}

// Calls the backend. Returns { ok, status, data }.
async function api(path, method = "GET", body) {
    const headers = {};
    if (body) headers["Content-Type"] = "application/json";
    if (getToken()) headers.Authorization = "Bearer " + getToken();

    const res = await fetch("/api" + path, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => null);
    return { ok: res.ok, status: res.status, data };
}

function formatKickoff(value) {
    return new Date(value).toLocaleString(undefined, {
        weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
    });
}

function formatOdds(odds) {
    if (odds == null) return "Odds not available";
    return odds > 0 ? "+" + odds : String(odds);
}

function formatStake(stake) {
    return stake == null ? "No stake" : "$" + Number(stake).toFixed(2);
}

// Makes text safe to put inside HTML
function esc(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
}

// Shows "Logged in" + Log out, or a Log in link, in the nav bar
async function showLoginStatus() {
    const box = document.getElementById("login-status");
    if (!getToken()) {
        box.innerHTML = '<a href="/">Log in</a>';
        return false;
    }
    const me = await api("/auth/me");
    if (!me.ok) {
        localStorage.removeItem("token");
        box.innerHTML = '<a href="/">Log in</a>';
        return false;
    }
    box.innerHTML = 'Logged in · <a href="#" id="logout-link">Log out</a>';
    document.getElementById("logout-link").onclick = (event) => {
        event.preventDefault();
        localStorage.removeItem("token");
        location.reload();
    };
    return true;
}