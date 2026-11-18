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
        location.href = "/";
    };
    return true;
}


// Full team names for display (the database stores abbreviations like "DET")
const TEAM_NAMES = {
    ARI: "Arizona Cardinals", ATL: "Atlanta Falcons", BAL: "Baltimore Ravens", BUF: "Buffalo Bills",
    CAR: "Carolina Panthers", CHI: "Chicago Bears", CIN: "Cincinnati Bengals", CLE: "Cleveland Browns",
    DAL: "Dallas Cowboys", DEN: "Denver Broncos", DET: "Detroit Lions", GB: "Green Bay Packers",
    HOU: "Houston Texans", IND: "Indianapolis Colts", JAX: "Jacksonville Jaguars", KC: "Kansas City Chiefs",
    LA: "Los Angeles Rams", LAC: "Los Angeles Chargers", LV: "Las Vegas Raiders", MIA: "Miami Dolphins",
    MIN: "Minnesota Vikings", NE: "New England Patriots", NO: "New Orleans Saints", NYG: "New York Giants",
    NYJ: "New York Jets", PHI: "Philadelphia Eagles", PIT: "Pittsburgh Steelers", SEA: "Seattle Seahawks",
    SF: "San Francisco 49ers", TB: "Tampa Bay Buccaneers", TEN: "Tennessee Titans", WAS: "Washington Commanders",
};

function teamName(abbr) {
    return TEAM_NAMES[abbr] || abbr;
}