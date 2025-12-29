/* =========================
   HELPERS
   ========================= */

export function escapeHtml(str = "") {
    return String(str)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

export function linkifySafe(text = "") {
    let escaped = escapeHtml(text);

    // 1. Detect Website Links (http, https, www)
    const urlRegex = /((https?:\/\/|www\.)[^\s<]+)/g;
    escaped = escaped.replace(urlRegex, (url) => {
        const href = url.startsWith("http") ? url : `https://${url}`;
        const cleanHref = href.replaceAll('"', "%22");
        return `<a href="${cleanHref}" target="_blank" rel="noreferrer">${url}</a>`;
    });

    // 2. Detect Email
    const emailRegex = /([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/g;
    escaped = escaped.replace(emailRegex, (email) => {
        return `<a href="mailto:${email}">${email}</a>`;
    });

    return escaped;
}

export function formatTextHtml(text = "") {
    return linkifySafe(text).replace(/\n/g, "<br/>");
}
