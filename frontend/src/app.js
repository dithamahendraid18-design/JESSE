import "./styles.css";

/* =========================
   CONFIG
   ========================= */
const API_BASE = import.meta.env.VITE_API_BASE || "https://jesse-x1d4.onrender.com";

const chatEl = document.getElementById("chat");
const brandNameEl = document.getElementById("brandName");
const brandSubEl = document.getElementById("brandSub");

const composer = document.getElementById("composer");
const inputEl = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const themeToggle = document.getElementById("themeToggle");
const resetBtn = document.getElementById("resetBtn");
const imageModal = document.getElementById("imageModal");
const fullImage = document.getElementById("fullImage");
const closeBtn = document.querySelector(".close-btn");
const params = new URLSearchParams(window.location.search);
const CLIENT_ID = params.get("client_id");

/* =========================
   STATE
   ========================= */
let BOT_AVATAR_URL = "/bot.png";
let isLoading = false;
let typingRow = null;

/* =========================
   THEME (Light/Dark) - FIXED
   ========================= */
// 1. Definisikan Ikon SVG
const MOON_ICON = `<svg viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
const SUN_ICON  = `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;

function getPreferredTheme() {
  const saved = localStorage.getItem("jesse_theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches
    ? "light"
    : "dark";
}

function applyTheme(mode) {
  document.documentElement.setAttribute("data-theme", mode);
  localStorage.setItem("jesse_theme", mode);
  
  // Update ikon menggunakan innerHTML (SVG)
  if (themeToggle) {
    themeToggle.innerHTML = mode === "dark" ? MOON_ICON : SUN_ICON;
  }
}

// Event Listener Tema
if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    applyTheme(current === "dark" ? "light" : "dark");
  });
}

// Event Listener Reset Chat
if (resetBtn) {
  resetBtn.addEventListener("click", () => {
    if (confirm("Start a new conversation? This will clear current history.")) {
      clearHistory(); 
    }
  });
}

// Jalankan Tema saat awal load
applyTheme(getPreferredTheme());

function applyClientBrand(theme) {
  if (!theme) return;
  if (theme.primary_color) document.documentElement.style.setProperty("--primary", theme.primary_color);
  if (theme.font_family) document.documentElement.style.setProperty("--font", theme.font_family);
}

/* =========================
   HELPERS
   ========================= */
function escapeHtml(str = "") {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function linkifySafe(text = "") {
  let escaped = escapeHtml(text);

  // 1. Deteksi Link Website (http, https, www)
  const urlRegex = /((https?:\/\/|www\.)[^\s<]+)/g;
  escaped = escaped.replace(urlRegex, (url) => {
    const href = url.startsWith("http") ? url : `https://${url}`;
    const cleanHref = href.replaceAll('"', "%22");
    return `<a href="${cleanHref}" target="_blank" rel="noreferrer">${url}</a>`;
  });

  // 2. Deteksi Email (nama@domain.com) -> TAMBAHAN BARU
  const emailRegex = /([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/g;
  escaped = escaped.replace(emailRegex, (email) => {
    // Hindari double link jika email sudah ada di dalam tag href (kasus jarang)
    return `<a href="mailto:${email}">${email}</a>`;
  });

  return escaped;
}

function formatTextHtml(text = "") {
  return linkifySafe(text).replace(/\n/g, "<br/>");
}

/* =========================
   CHAT HISTORY (PERSISTENCE)
   ========================= */
const STORAGE_KEY = "jesse_chat_history_" + (CLIENT_ID || "default");

function saveHistory(role, data) {
  const history = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  history.push({ role, data, timestamp: Date.now() });
  if (history.length > 50) history.shift(); 
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

function loadHistory() {
  const history = JSON.parse(localStorage.getItem(STORAGE_KEY));
  return history;
}

function clearHistory() {
  localStorage.removeItem(STORAGE_KEY);
  window.location.reload();
}

/* =========================
   LIGHTBOX / MODAL
   ========================= */
function openModal(imgUrl) {
  if (!imageModal || !fullImage) return;
  fullImage.src = imgUrl; 
  imageModal.classList.add("active"); 
}

function closeModal() {
  if (!imageModal) return;
  imageModal.classList.remove("active"); 
  setTimeout(() => { if (fullImage) fullImage.src = ""; }, 300);
}

if (closeBtn) closeBtn.onclick = closeModal;
if (imageModal) {
  imageModal.onclick = (e) => {
    if (e.target === imageModal) closeModal();
  };
}

/* =========================
   UI: AVATAR & BUBBLES
   ========================= */
function createBotAvatar(explicitUrl = null) {
  const img = document.createElement("img");
  img.className = "avatar";
  img.alt = "bot";
  img.src = explicitUrl || BOT_AVATAR_URL || "/favicon.ico";
  img.loading = "lazy";
  img.onerror = () => {
    img.removeAttribute("src");
    img.classList.add("fallback");
  };
  return img;
}

function addBotBubble(message, avatarUrl = null, save = true) {
  const row = document.createElement("div");
  row.className = "row bot";

  row.appendChild(createBotAvatar(avatarUrl));

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const type = message?.type || "text";

  if (type === "image") {
    const img = document.createElement("img");
    img.className = "chat-image";
    let finalUrl = message.url || "";
    if (finalUrl.startsWith("/")) {
      finalUrl = `${API_BASE}${finalUrl}`;
    }
    
    if (save) {
      saveHistory("bot", message);
    }

    img.src = finalUrl;
    img.alt = message.alt || "image";
    img.loading = "lazy";
    img.style.cursor = "pointer";
    img.onclick = () => openModal(finalUrl);

    img.onerror = () => {
      console.warn("Gagal load gambar chat:", finalUrl);
      bubble.innerHTML = "";
      const p = document.createElement("div");
      p.innerHTML = "Image unavailable 🖼️";
      p.style.color = "var(--muted)";
      p.style.fontSize = "12px";
      bubble.appendChild(p);
    };

    bubble.appendChild(img);
  } else {
    bubble.innerHTML = formatTextHtml(message?.text || "");
    if (save) {
      saveHistory("bot", message);
    }
  }

  row.appendChild(bubble);
  chatEl.appendChild(row);
  scrollToBottom();
}

function addUserBubble(text, save = true) {
  const row = document.createElement("div");
  row.className = "row user";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  const status = document.createElement("div");
  status.className = "status";
  status.textContent = "Sending…";

  if (save) {
    saveHistory("user", text);
  }

  row.appendChild(bubble);
  row.appendChild(status);

  chatEl.appendChild(row);
  scrollToBottom();

  return status;
}

function addChips(buttons, avatarUrl = null) {
  if (!Array.isArray(buttons) || !buttons.length) return;

  const row = document.createElement("div");
  row.className = "row bot chips-row";
  
  row.appendChild(createBotAvatar(avatarUrl));

  const wrap = document.createElement("div");
  wrap.className = "chips";

  buttons.forEach((b) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn";
    btn.textContent = b.label || "Option";
    btn.disabled = isLoading;

    btn.addEventListener("click", () => {
      sendIntent(b.intent, b.label || "");
    });

    wrap.appendChild(btn);
  });

  row.appendChild(wrap);
  chatEl.appendChild(row);
  scrollToBottom();
}

/* =========================
   TYPING & LOADING
   ========================= */
function showTyping() {
  if (typingRow) return;

  const row = document.createElement("div");
  row.className = "row bot";
  row.appendChild(createBotAvatar(BOT_AVATAR_URL));

  const bubble = document.createElement("div");
  bubble.className = "typing-bubble";
  const typing = document.createElement("div");
  typing.className = "typing";
  typing.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;

  bubble.appendChild(typing);
  row.appendChild(bubble);

  chatEl.appendChild(row);
  scrollToBottom();
  typingRow = row;
}

function hideTyping() {
  if (!typingRow) return;
  typingRow.remove();
  typingRow = null;
}

function setLoading(loading) {
  isLoading = loading;
  inputEl.disabled = loading;
  sendBtn.disabled = loading;
  document.querySelectorAll(".btn").forEach((b) => (b.disabled = loading));

  if (loading) showTyping();
  else hideTyping();
}

/* =========================
   RENDER BOT RESPONSE
   ========================= */
function renderBotResponse(data) {
  const currentAvatarUrl = BOT_AVATAR_URL;
  const messages = Array.isArray(data.messages) && data.messages.length
      ? data.messages
      : [{ type: "text", text: data.reply || "" }];

  messages.forEach((m) => addBotBubble(m, currentAvatarUrl));
  addChips(Array.isArray(data.buttons) ? data.buttons : [], currentAvatarUrl);
}

/* =========================
   API CALLS
   ========================= */
async function postChat(payload) {
  const apiKey = "KELEVERDO12345jesse"
  const r = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      "x-api-key": apiKey
    },
    body: JSON.stringify(payload),
  });

  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const msg = data?.error || `Request failed (${r.status})`;
    throw new Error(msg);
  }
  return data;
}

async function loadGreeting() {
  const apiKey = "KELEVERDO12345jesse"
  if (!CLIENT_ID) {
    addBotBubble({ type: "text", text: "Missing client_id parameter.\nExample: ?client_id=oceanbite_001" }, null, false);
    return;
  }

  setLoading(true);
  try {
    const r = await fetch(`${API_BASE}/api/greeting?client_id=${encodeURIComponent(CLIENT_ID)}`, {
        method: "GET",
        headers: { 
          "content-type": "application/json",
          "x-api-key": apiKey
        }
    });

    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      throw new Error(data.error || "failed to load greeting");
    }
    const theme = data.theme || {};
    applyClientBrand(theme);
    BOT_AVATAR_URL = theme.bot_avatar_url || null; 

    if (theme.brand_name) brandNameEl.textContent = theme.brand_name;
    brandSubEl.textContent = data?.meta?.client || theme.brand_name || "Restaurant Assistant";

    renderBotResponse(data);
  } catch (e) {
    addBotBubble({ type: "text", text: `Sorry — Could not load greeting.\n${e.message}` });
  } finally {
    setLoading(false);
  }
}

async function sendIntent(intent, label = "") {
  if (!CLIENT_ID || !intent) return;

  const status = label ? addUserBubble(label) : null;

  setLoading(true);
  try {
    const data = await postChat({ client_id: CLIENT_ID, intent });
    if (status) status.textContent = "Sent";
    renderBotResponse(data);
  } catch (e) {
    if (status) {
      status.textContent = "Failed";
      status.classList.add("error");
    }
    addBotBubble({ type: "text", text: `Sorry — ${e.message}` });
    addChips([{ label: "Main menu", intent: "main_menu" }], BOT_AVATAR_URL);
  } finally {
    setLoading(false);
  }
}

/* =========================
   EVENT LISTENERS
   ========================= */
composer.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = (inputEl.value || "").trim();
  if (!text) return;

  inputEl.value = "";
  const status = addUserBubble(text);

  setLoading(true);
  try {
    const data = await postChat({ client_id: CLIENT_ID, message: text });
    status.textContent = "Sent";
    renderBotResponse(data);
  } catch (e2) {
    status.textContent = "Failed";
    status.classList.add("error");
    addBotBubble({ type: "text", text: `Sorry — ${e2.message}` });
    addChips([{ label: "Main menu", intent: "main_menu" }], BOT_AVATAR_URL);
  } finally {
    setLoading(false);
  }
});

function scrollToBottom() {
  chatEl.scrollTop = chatEl.scrollHeight;
}

/* =========================
   BOOTSTRAP (LOGIKA STARTUP)
   ========================= */
async function initApp() {
  const history = loadHistory();

  if (history && history.length > 0) {
    console.log("Memuat riwayat chat...");
    
    // Fetch theme config diam-diam
    if (CLIENT_ID) {
        try {
            const r = await fetch(`${API_BASE}/api/greeting?client_id=${encodeURIComponent(CLIENT_ID)}`);
            const data = await r.json();
            const theme = data.theme || {};
            applyClientBrand(theme);
            BOT_AVATAR_URL = theme.bot_avatar_url || null;
            
            if (theme.brand_name) brandNameEl.textContent = theme.brand_name;
            brandSubEl.textContent = data?.meta?.client || theme.brand_name;
        } catch (e) { console.warn("Gagal load theme config"); }
    }

    history.forEach(item => {
      if (item.role === "bot") {
        addBotBubble(item.data, BOT_AVATAR_URL, false); 
      } else if (item.role === "user") {
        addUserBubble(item.data, false);
      }
    });

    const divider = document.createElement("div");
    divider.style.textAlign = "center";
    divider.style.fontSize = "11px";
    divider.style.color = "var(--muted)";
    divider.style.margin = "20px 0";
    divider.textContent = "—— Chat restored ——";
    chatEl.appendChild(divider);

    // Tampilkan tombol menu lagi setelah refresh
    setTimeout(() => {
        addBotBubble({ type: "text", text: "Welcome back! How can I help you?" }, BOT_AVATAR_URL, false);
        addChips([
            { label: "Menu & prices", intent: "menu" },
            { label: "Opening hours", intent: "hours" },
            { label: "Location", intent: "location" },
            { label: "Contact / Reservation", intent: "contact" },
            { label: "About us", intent: "about" }
        ], BOT_AVATAR_URL);
    }, 500);
    
    scrollToBottom();

  } else {
    loadGreeting();
  }
}

// Jalankan aplikasi
initApp();