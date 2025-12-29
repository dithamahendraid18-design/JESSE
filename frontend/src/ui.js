import { API_BASE, STORAGE_KEY } from "./config.js";
import { formatTextHtml } from "./utils.js";

/* =========================
   DOM ELEMENTS
   ========================= */
const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const themeToggle = document.getElementById("themeToggle");
const imageModal = document.getElementById("imageModal");
const fullImage = document.getElementById("fullImage");
const closeBtn = document.querySelector(".close-btn");

/* =========================
   STATE
   ========================= */
let typingRow = null;
export const UI_STATE = {
    BOT_AVATAR_URL: "/final.png"
};

/* =========================
   THEME
   ========================= */
const MOON_ICON = `<svg viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
const SUN_ICON = `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;

export function getPreferredTheme() {
    const saved = localStorage.getItem("jesse_theme");
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches
        ? "light"
        : "dark";
}

export function applyTheme(mode) {
    document.documentElement.setAttribute("data-theme", mode);
    localStorage.setItem("jesse_theme", mode);
    if (themeToggle) {
        themeToggle.innerHTML = mode === "dark" ? MOON_ICON : SUN_ICON;
    }
}

export function applyClientBrand(theme) {
    if (!theme) return;
    if (theme.primary_color) document.documentElement.style.setProperty("--primary", theme.primary_color);
    if (theme.font_family) document.documentElement.style.setProperty("--font", theme.font_family);
}

/* =========================
   HISTORY MANAGER
   ========================= */
export function saveHistory(role, data) {
    const history = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    history.push({ role, data, timestamp: Date.now() });
    if (history.length > 50) history.shift();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

export function loadHistory() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
}

export function clearHistory() {
    localStorage.removeItem(STORAGE_KEY);
    window.location.reload();
}

/* =========================
   UI HELPERS
   ========================= */
export function scrollToBottom() {
    if (chatEl) chatEl.scrollTop = chatEl.scrollHeight;
}

export function openModal(imgUrl) {
    if (!imageModal || !fullImage) return;
    fullImage.src = imgUrl;
    imageModal.classList.add("active");
}

export function closeModal() {
    if (!imageModal) return;
    imageModal.classList.remove("active");
    setTimeout(() => { if (fullImage) fullImage.src = ""; }, 300);
}

// Bind Modal Events
if (closeBtn) closeBtn.onclick = closeModal;
if (imageModal) {
    imageModal.onclick = (e) => {
        if (e.target === imageModal) closeModal();
    };
}

/* =========================
   RENDERING
   ========================= */
function createBotAvatar(explicitUrl = null) {
    const img = document.createElement("img");
    img.className = "avatar";
    img.alt = "bot";
    img.src = explicitUrl || "/final.png";
    img.loading = "lazy";
    img.onerror = () => {
        if (img.src.includes("final.png")) {
            img.removeAttribute("src");
            img.classList.add("fallback");
        } else {
            img.src = "/final.png";
        }
    };
    return img;
}

export function addBotBubble(message, avatarUrl = null, save = true) {
    const row = document.createElement("div");
    row.className = "row bot";
    row.appendChild(createBotAvatar(avatarUrl || UI_STATE.BOT_AVATAR_URL));

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

        img.src = finalUrl;
        img.alt = message.alt || "image";
        img.loading = "lazy";
        img.style.cursor = "pointer";
        img.onclick = () => openModal(finalUrl);
        img.onerror = () => {
            bubble.innerHTML = "";
            const p = document.createElement("div");
            p.innerText = "Image unavailable 🖼️";
            p.style.color = "var(--muted)";
            p.style.fontSize = "12px";
            bubble.appendChild(p);
        };

        bubble.appendChild(img);
    } else {
        bubble.innerHTML = formatTextHtml(message?.text || "");
    }

    row.appendChild(bubble);
    chatEl.appendChild(row);
    scrollToBottom();

    if (save) saveHistory("bot", message);
}

export function addUserBubble(text, save = true) {
    const row = document.createElement("div");
    row.className = "row user";

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    const status = document.createElement("div");
    status.className = "status";
    status.textContent = "Sending…";

    row.appendChild(bubble);
    row.appendChild(status);
    chatEl.appendChild(row);
    scrollToBottom();

    if (save) saveHistory("user", text);

    return status;
}

export function addChips(buttons, avatarUrl = null, onChipClick) {
    if (!Array.isArray(buttons) || !buttons.length) return;

    const row = document.createElement("div");
    row.className = "row bot chips-row";
    row.appendChild(createBotAvatar(avatarUrl || UI_STATE.BOT_AVATAR_URL));

    const wrap = document.createElement("div");
    wrap.className = "chips";

    buttons.forEach((b) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn";
        btn.textContent = b.label || "Option";

        btn.addEventListener("click", () => {
            if (onChipClick) onChipClick(b.intent, b.label);
        });

        wrap.appendChild(btn);
    });

    row.appendChild(wrap);
    chatEl.appendChild(row);
    scrollToBottom();
}

/* =========================
   LOADING STATE
   ========================= */
export function showTyping() {
    if (typingRow) return;

    const row = document.createElement("div");
    row.className = "row bot";
    row.appendChild(createBotAvatar(UI_STATE.BOT_AVATAR_URL));

    const bubble = document.createElement("div");
    bubble.className = "typing-bubble";
    bubble.innerHTML = `<div class="typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>`;

    bubble.firstChild.className = "typing"; // Ensuring correct class if innerHTML mess up

    row.appendChild(bubble);
    chatEl.appendChild(row);
    scrollToBottom();
    typingRow = row;
}

export function hideTyping() {
    if (!typingRow) return;
    typingRow.remove();
    typingRow = null;
}

export function setLoading(loading) {
    if (inputEl) inputEl.disabled = loading;
    if (sendBtn) sendBtn.disabled = loading;
    document.querySelectorAll(".btn").forEach((b) => (b.disabled = loading));

    if (loading) showTyping();
    else hideTyping();
}
