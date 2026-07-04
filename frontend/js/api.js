// ============================================================
// Central API client. Every page uses `api.get/post/put(...)`
// instead of raw fetch, so auth headers and error handling stay
// consistent everywhere.
// ============================================================
const API_BASE = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : "http://localhost:8000"; // change to your deployed backend URL when hosting

const TOKEN_KEY = "hrms_token";
const SESSION_KEY = "hrms_session"; // { role, login_id, full_name, must_change_password }

const Auth = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setSession(token, session) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  },
  getSession() {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
    window.location.href = "index.html";
  },
  requireLogin() {
    if (!Auth.getToken()) {
      window.location.href = "index.html";
    }
    return Auth.getSession();
  },
};

class ApiError extends Error {
  constructor(message, status, fieldErrors) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors || [];
  }
}

async function request(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = Auth.getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (networkErr) {
    // The backend is unreachable (not running, wrong URL, offline, CORS, etc.)
    throw new ApiError(
      "Can't reach the server. Make sure the backend is running and try again.",
      0
    );
  }

  if (response.status === 401) {
    Auth.logout();
    throw new ApiError("Your session expired. Please sign in again.", 401);
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch {
    /* empty body */
  }

  if (!response.ok) {
    const message = (data && data.detail) || "Something went wrong. Please try again.";
    throw new ApiError(message, response.status, data && data.errors);
  }
  return data;
}

const api = {
  get: (path) => request("GET", path),
  post: (path, body) => request("POST", path, body),
  put: (path, body) => request("PUT", path, body),
  del: (path) => request("DELETE", path),
};

// ---------------------------------------------------------- toasts
function toast(message, type = "info") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

function showBanner(el, message, type = "error") {
  el.textContent = message;
  el.className = `banner ${type} show`;
}

function hideBanner(el) {
  el.className = "banner";
}

function initials(name) {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] || "") + (parts[1]?.[0] || "")).toUpperCase();
}

function fmtCurrency(n) {
  return "₹" + Number(n || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(d) {
  if (!d) return "-";
  return new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function fmtTime(dt) {
  if (!dt) return "--:--";
  return new Date(dt).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}
