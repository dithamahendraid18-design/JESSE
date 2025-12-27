from __future__ import annotations

from typing import Any
from ..core.client_loader import ClientContext


def _currency(ctx: ClientContext) -> str:
    """Ambil currency dari menu.json. Fallback default 'SGD'."""
    cur = ((ctx.menu or {}).get("currency") or "").strip()
    return cur or "SGD"


def _promo(ctx: ClientContext) -> dict[str, Any] | None:
    promo = (ctx.menu or {}).get("promo") or {}
    if not isinstance(promo, dict):
        return None
    if not promo.get("enabled"):
        return None
    return promo


def _categories(ctx: ClientContext) -> list[dict[str, Any]]:
    cats = (ctx.menu or {}).get("categories") or []
    return cats if isinstance(cats, list) else []


def _fmt_price(price: Any) -> str:
    if price is None:
        return ""
    try:
        p = float(price)
        if p.is_integer():
            return str(int(p))
        return f"{p:.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(price)


def _asset_url(ctx: ClientContext, value: str, version: str = "1") -> str:
    """Normalize url gambar"""
    v = (value or "").strip()
    if not v:
        return ""
    if v.startswith("http://") or v.startswith("https://") or v.startswith("/client-assets/"):
        return v
    v = v.lstrip("/")
    return f"/client-assets/{ctx.id}/{v}?v={version}"


def nav_buttons(ctx: ClientContext) -> list[dict[str, str]]:
    buttons: list[dict[str, str]] = []

    for c in _categories(ctx):
        cid = (c.get("id") or "").strip()
        label = (c.get("label") or "Category").strip()
        if cid:
            buttons.append({"label": label, "intent": f"menu:{cid}"})

    buttons.append({"label": "Order Food", "intent": "order_food"})
    buttons.append({"label": "Back", "intent": "main_menu"})
    return buttons


def menu_entry(ctx: ClientContext):
    """Response saat user klik 'Menu & prices'."""
    if not _categories(ctx):
        messages = [
            {
                "type": "text",
                "text": "Menu is being updated right now 😊\nPlease check back later.",
            },
            {"type": "text", "text": "Choose an option below:"},
        ]
        return messages, nav_buttons(ctx)

    messages: list[dict[str, Any]] = []

    # ✅ PROMO BLOCK
    promo = _promo(ctx)
    if promo:
        title = (promo.get("title") or "🔥 Promo").strip()
        text = (promo.get("text") or "").strip()
        code = (promo.get("code") or "").strip()
        valid_until = (promo.get("valid_until") or "").strip()
        terms = (promo.get("terms") or "").strip()

        # Handle single/multiple images
        raw_images = promo.get("images") or promo.get("image", "")
        promo_images = []
        if isinstance(raw_images, str) and raw_images.strip():
            promo_images = [raw_images.strip()]
        elif isinstance(raw_images, list):
            promo_images = [str(x).strip() for x in raw_images if str(x).strip()]

        # Format Text dengan Bold (Markdown Style)
        promo_text = f"**{title}**"
        if text: promo_text += f"\n{text}"
        if code: promo_text += f"\n\nCode: **{code}**"
        if valid_until: promo_text += f"\nValid until: {valid_until}"
        if terms: promo_text += f"\n\n_{terms}_"

        messages.append({"type": "text", "text": promo_text})

        for i, img in enumerate(promo_images[:4], start=1):
            messages.append(
                {"type": "image", "url": _asset_url(ctx, img), "alt": f"Promo {i}"}
            )

    # Intro Message
    messages.extend([
        {
            "type": "text",
            "text": "Here’s our menu! Tap a category to see items 👇",
        }
    ])

    return messages, nav_buttons(ctx)


def menu_category(ctx: ClientContext, category_id: str):
    """Response saat user pilih kategori."""
    cats = _categories(ctx)
    cat = next((c for c in cats if (c.get("id") or "").strip() == category_id.strip()), None)
    if not cat:
        return menu_entry(ctx)

    cur = _currency(ctx)
    items = cat.get("items") or []
    if not isinstance(items, list):
        items = []

    messages: list[dict[str, Any]] = []

    if not items:
        messages.append({"type": "text", "text": "No items available in this category."})
        return messages, nav_buttons(ctx)

    for it in items:
        if not isinstance(it, dict): continue

        name = (it.get("name") or "Item").strip()
        price = it.get("price")
        desc = (it.get("desc") or "").strip()
        image = (it.get("image") or it.get("photo") or "").strip()

        # ✨ OPTIMASI: Pakai Bold untuk Nama Makanan
        text = f"**{name}**"
        if price is not None and str(price).strip() != "":
            text += f" — {cur} {_fmt_price(price)}"
        if desc:
            text += f"\n{desc}"

        messages.append({"type": "text", "text": text})

        if image:
            messages.append({"type": "image", "url": _asset_url(ctx, image), "alt": name})

    messages.append({"type": "text", "text": "Choose another category:"})
    return messages, nav_buttons(ctx)


def order_food(ctx: ClientContext):
    """Response untuk intent: order_food (Optimized Loop)."""
    ch = ctx.channels or {}
    
    # ⚡ OPTIMASI: Daftar channel mapping (Key JSON -> Label Tampilan)
    # Cukup tambah di sini kalau ada aplikasi baru
    channel_map = {
        "website": "🌐 Website",
        "order_url": "🌐 Order Online",
        "gofood": "🟢 GoFood",
        "grabfood": "🟢 GrabFood",
        "shopeefood": "🟠 ShopeeFood",
        "ubereats": "⚫ UberEats",
        "doordash": "🔴 DoorDash",
        "deliveroo": "🔵 Deliveroo",
        "phone": "📞 Phone",
        "whatsapp": "💬 WhatsApp",
        "wa": "💬 WhatsApp"
    }

    links_found = []
    
    # Loop pintar: Cek data json, kalau ada isinya, masukkan ke list
    for key, label in channel_map.items():
        val = (ch.get(key) or "").strip()
        if val:
            # Hindari duplikat label (misal wa & whatsapp)
            if not any(l.startswith(label) for l in links_found):
                links_found.append(f"{label}: {val}")

    if links_found:
        msg = "You can order via these official channels! 👇\n\n" + "\n".join(links_found)
    else:
        msg = "Ordering links are currently unavailable. Please contact us directly! 😊"

    messages = [{"type": "text", "text": msg}]

    buttons = [
        {"label": "Back to Menu", "intent": "menu"},
        {"label": "Contact Us", "intent": "contact"},
        {"label": "Home", "intent": "greeting"},
    ]
    return messages, buttons