import { API_BASE } from "./config.js";

const REQUEST_TIMEOUT = 15000; // 15s timeout

export async function postChat(payload) {
    const apiKey = "KELEVERDO12345jesse"; // Hardcoded for MVP

    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
        const r = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": apiKey
            },
            body: JSON.stringify(payload),
            signal: controller.signal
        });

        clearTimeout(id);

        const data = await r.json().catch(() => ({}));
        if (!r.ok) {
            throw new Error(data.error || `Request failed (${r.status})`);
        }
        return data;
    } catch (e) {
        clearTimeout(id);
        throw e;
    }
}

export async function fetchGreeting(itemClientId) {
    const apiKey = "KELEVERDO12345jesse";
    if (!itemClientId) throw new Error("Missing client_id");

    const r = await fetch(`${API_BASE}/api/greeting?client_id=${encodeURIComponent(itemClientId)}`, {
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
    return data;
}
