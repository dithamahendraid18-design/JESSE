import { CLIENT_ID, CLEANUP_KEY } from "./config.js";
import { postChat, fetchGreeting } from "./api.js";
import * as UI from "./ui.js";

/* =========================
   LOGIC CONTROLLER
   ========================= */

async function handleSend(text) {
    if (!text) return;

    const statusEl = UI.addUserBubble(text);
    UI.setLoading(true);

    try {
        const data = await postChat({ client_id: CLIENT_ID, message: text });
        if (statusEl) statusEl.textContent = "Sent";
        renderBotResponse(data);
    } catch (e) {
        if (statusEl) {
            statusEl.textContent = "Failed";
            statusEl.classList.add("error");
        }
        UI.addBotBubble({ type: "text", text: `Sorry — ${e.message}` });
        UI.addChips([{ label: "Main menu", intent: "main_menu" }], null, handleIntent);
    } finally {
        UI.setLoading(false);
    }
}

async function handleIntent(intent, label = "") {
    if (!CLIENT_ID || !intent) return;

    const statusEl = label ? UI.addUserBubble(label) : null;
    UI.setLoading(true);

    try {
        const data = await postChat({ client_id: CLIENT_ID, intent });
        if (statusEl) statusEl.textContent = "Sent";
        renderBotResponse(data);
    } catch (e) {
        if (statusEl) {
            statusEl.textContent = "Failed";
            statusEl.classList.add("error");
        }
        UI.addBotBubble({ type: "text", text: `Sorry — ${e.message}` });
        UI.addChips([{ label: "Main menu", intent: "main_menu" }], null, handleIntent);
    } finally {
        UI.setLoading(false);
    }
}

function renderBotResponse(data) {
    const messages = Array.isArray(data.messages) && data.messages.length
        ? data.messages
        : [{ type: "text", text: data.reply || "" }];

    messages.forEach((m) => UI.addBotBubble(m));

    if (Array.isArray(data.buttons)) {
        UI.addChips(data.buttons, null, handleIntent);
    }
}

/* =========================
   INITIALIZATION
   ========================= */
const brandNameEl = document.getElementById("brandName");
const brandSubEl = document.getElementById("brandSub");
const composer = document.getElementById("composer");
const inputEl = document.getElementById("messageInput");
const themeToggle = document.getElementById("themeToggle");
const resetBtn = document.getElementById("resetBtn");

async function initApp() {

    // 1. Cleanup old data if needed
    if (!localStorage.getItem(CLEANUP_KEY)) {
        console.log("🧹 Cleanup old data...");
        localStorage.clear();
        localStorage.setItem(CLEANUP_KEY, "true");
    }

    // 2. Setup Theme
    UI.applyTheme(UI.getPreferredTheme());

    // 3. Client Name Placeholder
    if (CLIENT_ID) {
        const CLIENT_NAMES = {
            "luna_002": "Luna Ramen & Izakaya",
            "oceanbite_001": "OceanBite Seafood Grill",
        };
        const initialName = CLIENT_NAMES[CLIENT_ID] || "Restaurant Assistant";
        if (brandSubEl) brandSubEl.textContent = initialName;
    }

    // 4. Load History or Greeting
    const history = UI.loadHistory();

    if (history && history.length > 0) {
        // Restore History
        console.log("Restoring chat history...");

        // Background fetch to update brand/theme
        if (CLIENT_ID) {
            fetchGreeting(CLIENT_ID).then(data => {
                const theme = data.theme || {};
                UI.applyClientBrand(theme);
                if (theme.brand_name && brandNameEl) brandNameEl.textContent = theme.brand_name;
                if (data?.meta?.client && brandSubEl) brandSubEl.textContent = data.meta.client;
                if (theme.bot_avatar_url) UI.UI_STATE.BOT_AVATAR_URL = theme.bot_avatar_url;
            }).catch(() => { });
        }

        history.forEach(item => {
            if (item.role === "bot") {
                UI.addBotBubble(item.data, null, false);
            } else if (item.role === "user") {
                UI.addUserBubble(item.data, false);
            }
        });

        const divider = document.createElement("div");
        Object.assign(divider.style, {
            textAlign: "center", fontSize: "11px", color: "var(--muted)", margin: "20px 0"
        });
        divider.textContent = "—— Chat restored ——";
        document.getElementById("chat").appendChild(divider);

        // Re-show menu chips
        setTimeout(() => {
            UI.addBotBubble({ type: "text", text: "Welcome back! How can I help you?" }, null, false);
            UI.addChips([
                { label: "Menu & prices", intent: "menu" },
                { label: "Opening hours", intent: "hours" },
                { label: "Location", intent: "location" },
                { label: "Contact / Reservation", intent: "contact" },
                { label: "About us", intent: "about" }
            ], null, handleIntent);
        }, 500);

    } else {
        // New Session -> Fetch Greeting
        if (!CLIENT_ID) {
            UI.addBotBubble({ type: "text", text: "Missing client_id parameter.\nExample: ?client_id=oceanbite_001" }, null, false);
        } else {
            UI.setLoading(true);
            try {
                const data = await fetchGreeting(CLIENT_ID);
                const theme = data.theme || {};

                UI.applyClientBrand(theme);
                if (theme.brand_name && brandNameEl) brandNameEl.textContent = theme.brand_name;
                if (data?.meta?.client && brandSubEl) brandSubEl.textContent = data.meta.client;
                if (theme.bot_avatar_url) UI.UI_STATE.BOT_AVATAR_URL = theme.bot_avatar_url;

                renderBotResponse(data);
            } catch (e) {
                UI.addBotBubble({ type: "text", text: `Sorry — Could not load greeting.\n${e.message}` });
            } finally {
                UI.setLoading(false);
            }
        }
    }
}

/* =========================
   EVENT LISTENERS
   ========================= */
if (composer) {
    composer.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = (inputEl.value || "").trim();
        inputEl.value = "";
        handleSend(text);
    });
}

if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme") || "dark";
        UI.applyTheme(current === "dark" ? "light" : "dark");
    });
}

if (resetBtn) {
    resetBtn.addEventListener("click", () => {
        if (confirm("Start a new conversation? This will clear current history.")) {
            UI.clearHistory();
        }
    });
}

// Start
initApp();
