import { API_BASE } from "./config.js";

const ADMIN_PASSWORD = "secret-password"; // Hardcoded for prototype

const state = {
    clients: [],
    currentItem: null
};

// --- DOM Utils ---
const $ = (sel) => document.querySelector(sel);
const show = (el) => el.classList.remove("hidden");
const hide = (el) => el.classList.add("hidden");

// --- API ---
async function api(path, method = "GET", body = null) {
    const headers = {
        "Content-Type": "application/json",
        "X-Admin-Password": ADMIN_PASSWORD
    };

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    const r = await fetch(`${API_BASE}${path}`, opts);
    if (!r.ok) {
        // alert("API Error: " + r.statusText);
        throw new Error("API Error");
    }
    return r.json();
}

// --- App Logic ---
const app = {
    async init() {
        console.log("Admin Init");
        this.loadClients();
    },

    async loadClients() {
        show($("#client-list"));
        hide($("#menu-view"));

        const clients = await api("/api/admin/clients");
        state.clients = clients;

        const tbody = $("#clients-table tbody");
        tbody.innerHTML = clients.map(c => `
            <tr>
                <td>${c.id}</td>
                <td><strong>${c.name}</strong></td>
                <td>${c.plan_type}</td>
                <td>
                    <button class="primary" onclick="app.viewMenu('${c.id}', '${c.name}')">View Menu</button>
                </td>
            </tr>
        `).join("");
    },

    async viewMenu(clientId, clientName) {
        hide($("#client-list"));
        show($("#menu-view"));
        $("#menu-title").textContent = `Menu: ${clientName}`;

        const categories = await api(`/api/admin/clients/${clientId}/menu`);
        this.renderMenu(categories);
    },

    renderMenu(categories) {
        const tbody = $("#menu-table tbody");
        tbody.innerHTML = "";

        categories.forEach(cat => {
            cat.items.forEach(item => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><span style="font-size:0.8em; color:#666; bg:#eee; padding:2px 4px; border-radius:4px">${cat.label}</span></td>
                    <td>
                        <div>${item.name}</div>
                        <div style="font-size:0.8em; color:#666">${item.desc || ""}</div>
                    </td>
                    <td>${item.price.toFixed(2)}</td>
                    <td>
                        <button class="edit-btn">Edit</button>
                    </td>
                `;
                tr.querySelector(".edit-btn").onclick = () => this.openEditModal(item);
                tbody.appendChild(tr);
            });
        });
    },

    openEditModal(item) {
        state.currentItem = item;
        $("#edit-id").value = item.id;
        $("#edit-name").value = item.name;
        $("#edit-price").value = item.price;
        $("#edit-desc").value = item.desc || "";
        show($("#modal"));
    },

    closeModal() {
        hide($("#modal"));
        state.currentItem = null;
    },

    async saveItem() {
        const id = $("#edit-id").value;
        const payload = {
            name: $("#edit-name").value,
            price: parseFloat($("#edit-price").value),
            desc: $("#edit-desc").value
        };

        try {
            await api(`/api/admin/menu-items/${id}`, "PUT", payload);
            alert("Saved!");
            this.closeModal();
            // Refresh logic omitted for prototype simplicity (reload page or re-fetch)
            // Ideally we re-fetch the menu, but we need client_id for that.
            // For now, let's just create a quick 'Back' UX flow or state reload
            // Simpler: just reload clients.
            this.loadClients();
        } catch (e) {
            alert("Failed to save");
        }
    },

    showClients() {
        this.loadClients();
    }
};

// Export to window for HTML onclick handlers
window.app = app;

// Start
app.init();
