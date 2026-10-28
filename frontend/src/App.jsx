import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = "http://localhost:3001/api/games";


// enable da line below to make it work if the backend is ready
const AUTH_API_ENABLED = false;



const AUTH_API_URL = "http://localhost:3001/api/auth";

async function authRequest(path, { method = "GET", body, signal } = {}) {
  const response = await fetch(`${AUTH_API_URL}${path}`, {
    method,
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });

  let data = null;
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else if (!response.ok) {
    data = { message: await response.text() };
  }

  if (!response.ok) {
    const error = new Error(data?.error || data?.message || "Authentication request failed.");
    error.status = response.status;
    throw error;
  }

  return data;
}

function formatKickoff(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Kickoff time TBD";

  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function App() {
  const [games, setGames] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);
  const [view, setView] = useState("games");
  const [authMode, setAuthMode] = useState("login");
  const [authNotice, setAuthNotice] = useState("");
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (!AUTH_API_ENABLED) return undefined;

    const controller = new AbortController();

    async function restoreSession() {
      try {
        const data = await authRequest("/me", { signal: controller.signal });
        setUser(data.user || null);
      } catch (requestError) {
        if (requestError.name !== "AbortError" && requestError.status !== 401) {
          setAuthNotice(requestError.message);
        }
      }
    }

    restoreSession();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function loadGames() {
      setLoading(true);
      setError("");

      try {
        const response = await fetch(API_URL, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`The games service returned HTTP ${response.status}.`);
        }

        const data = await response.json();
        if (!Array.isArray(data)) {
          throw new Error("The games service returned an unexpected response.");
        }

        setGames(data);
      } catch (requestError) {
        if (requestError.name !== "AbortError") {
          setError(requestError.message || "Could not load games.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadGames();
    return () => controller.abort();
  }, [reloadKey]);

  const sortedGames = useMemo(
    () =>
      games
        .slice()
        .sort((first, second) => new Date(second.kickoff) - new Date(first.kickoff)),
    [games],
  );

  function openAuth(mode) {
    setAuthMode(mode);
    setAuthNotice("");
    setView("auth");
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();

    if (!AUTH_API_ENABLED) {
      return;
    }

    const formData = new FormData(event.currentTarget);
    const credentials = Object.fromEntries(formData.entries());
    const endpoint = authMode === "login" ? "/login" : "/signup";

    setAuthSubmitting(true);
    setAuthNotice("");

    try {
      const data = await authRequest(endpoint, {
        method: "POST",
        body: credentials,
      });
      setUser(data.user || { email: credentials.email });
      setView("games");
    } catch (requestError) {
      setAuthNotice(requestError.message || "Could not authenticate.");
    } finally {
      setAuthSubmitting(false);
    }
  }

  async function handleLogout() {
    try {
      await authRequest("/logout", { method: "POST" });
      setUser(null);
    } catch (requestError) {
      setAuthNotice(requestError.message || "Could not log out.");
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <a className="brand" href="#home" aria-label="Fairline home">
          <span className="brand-mark">F</span>
          <span>Fairline</span>
        </a>
        <div className="header-actions">
          {view === "games" ? (
            <>
              <span className={`connection-status ${error ? "offline" : ""}`}>
                <span className="connection-dot" />
                {error ? "Offline" : loading ? "Connecting" : "Games connected"}
              </span>
              {AUTH_API_ENABLED && user ? (
                <>
                  <span className="connection-status">{user.name || user.email}</span>
                  <button className="header-button" onClick={handleLogout} type="button">
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <button className="header-button" onClick={() => openAuth("login")} type="button">
                    Log in
                  </button>
                  <button className="header-button primary" onClick={() => openAuth("signup")} type="button">
                    Sign up
                  </button>
                </>
              )}
            </>
          ) : (
            <button
              className="header-button back-button"
              onClick={() => setView("games")}
              type="button"
            >
              <span aria-hidden="true">←</span> Back to games
            </button>
          )}
        </div>
      </header>

      {view === "auth" ? (
        <main className="auth-page">
          <section className="auth-card" aria-labelledby="auth-title">
            <a
              className="back-link"
              href="#games"
              onClick={(event) => {
                event.preventDefault();
                setView("games");
              }}
            >
              <span aria-hidden="true">←</span> Back to game list
            </a>
            <p className="eyebrow">FAIRLINE ACCOUNT</p>
            <h1 id="auth-title">{authMode === "login" ? "Welcome back" : "Create your account"}</h1>
            <p className="auth-description">
              {authMode === "login"
                ? "Log in to continue to your Fairline account."
                : "Sign up to get started with Fairline."}
            </p>

            <form className="auth-form" onSubmit={handleAuthSubmit}>
              {authMode === "signup" && (
                <label>
                  Name
                  <input autoComplete="name" name="name" placeholder="Your name" required />
                </label>
              )}
              <label>
                Email
                <input
                  autoComplete="email"
                  name="email"
                  placeholder="you@example.com"
                  required
                  type="email"
                />
              </label>
              <label>
                Password
                <input
                  autoComplete={authMode === "login" ? "current-password" : "new-password"}
                  minLength="8"
                  name="password"
                  placeholder="At least 8 characters"
                  required
                  type="password"
                />
              </label>
              <button className="submit-button" disabled={authSubmitting} type="submit">
                {authSubmitting
                  ? "Please wait…"
                  : authMode === "login"
                    ? "Log in"
                    : "Create account"}
              </button>
            </form>

            {authNotice && <p className="auth-notice" role="status">{authNotice}</p>}

            <p className="auth-switch">
              {authMode === "login" ? "New to Fairline?" : "Already have an account?"}{" "}
              <button
                onClick={() => openAuth(authMode === "login" ? "signup" : "login")}
                type="button"
              >
                {authMode === "login" ? "Sign up" : "Log in"}
              </button>
            </p>
            <p className="auth-demo-note">hi</p>
          </section>
        </main>
      ) : (
        <main className="dashboard" id="home">
          <section className="intro">
            <p className="eyebrow">OH YEAH! FOOTBALL!</p>
            <h1>Games</h1>
            <p className="intro-copy">every game listed in da database.</p>
          </section>

          <section className="games-section" id="games" aria-labelledby="games-title">
            <div className="section-heading">
              <div>
                <h2 id="games-title">All games</h2>
                {!loading && !error && (
                  <p className="section-subtitle">
                    {games.length} {games.length === 1 ? "game" : "games"} in the database
                  </p>
                )}
              </div>
            </div>

            {loading ? (
              <div className="notice" role="status">Loading games…</div>
            ) : error ? (
              <div className="notice error-notice" role="alert">
                <div>
                  <strong>Couldn’t load games</strong>
                  <p>{error} Check that the backend is running, then try again.</p>
                </div>
                <button
                  className="text-button"
                  onClick={() => setReloadKey((key) => key + 1)}
                  type="button"
                >
                  Try again
                </button>
              </div>
            ) : sortedGames.length === 0 ? (
              <div className="notice empty-notice">
                <span className="empty-icon" aria-hidden="true">🏈</span>
                <div>
                  <strong>No games :c</strong>
                  <p>Games will appear here when they’re added.</p>
                </div>
              </div>
            ) : (
              <div className="game-list">
                {sortedGames.map((game) => {
                  const hasScore =
                    game.home_team_score != null && game.away_team_score != null;

                  return (
                    <article className="game-card" key={game.game_id}>
                      <div className="game-info">
                        <p className="kickoff">{formatKickoff(game.kickoff)}</p>
                        <div className="matchup">
                          <span>{game.away_team}</span>
                          <span className="versus">@</span>
                          <span>{game.home_team}</span>
                        </div>
                        <p className="week-label">Season {game.season} · Week {game.week}</p>
                      </div>
                      <div className="game-result">
                        <span className="detail-label">{hasScore ? "FINAL SCORE" : "STATUS"}</span>
                        <strong>
                          {hasScore
                            ? `${game.away_team_score} – ${game.home_team_score}`
                            : "No score yet"}
                        </strong>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </main>
      )}
    </div>
  );
}

export default App;
