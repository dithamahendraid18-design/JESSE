export const API_BASE = import.meta.env.VITE_API_BASE || "https://jesse-x1d4.onrender.com";

const params = new URLSearchParams(window.location.search);
export const CLIENT_ID = params.get("client_id");

export const STORAGE_KEY = "jesse_chat_history_" + (CLIENT_ID || "default");
export const CLEANUP_KEY = "fix_avatar_v1_done";
