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
            "text": "Here’s everything we have for you today — take your time and pick your favorite!",
        },
        {"type": "text", "text": "Choose a category below:"},
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

        # ✨ Tetap pakai Bold untuk Nama Makanan (User suka ini)
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
    """Response untuk intent: order_food (KEMBALI KE GAYA LAMA)."""
    ch = ctx.channels or {}

    phone = (ch.get("phone") or "").strip()
    whatsapp = (ch.get("whatsapp") or ch.get("wa") or "").strip()
    
    gofood = (ch.get("gofood") or ch.get("go_food") or "").strip()
    grabfood = (ch.get("grabfood") or ch.get("grab_food") or "").strip()
    ubereats = (ch.get("ubereats") or ch.get("uber_eats") or ch.get("uberfood") or "").strip()
    doordash = (ch.get("doordash") or ch.get("door_dash") or "").strip()
    deliveroo = (ch.get("deliveroo") or "").strip()
    website = (ch.get("order_url") or ch.get("website") or "").strip()

    # ✨ HEADLINE LAMA (Lebih Ramah)
    msg = "You can order your food from our official ordering channels! 😊✨\n\n"

    any_line = False
    if phone:
        msg += f"Phone: {phone}\n"; any_line = True
    if whatsapp:
        msg += f"WhatsApp: {whatsapp}\n"; any_line = True
    if gofood:
        msg += f"GoFood: {gofood}\n"; any_line = True
    if grabfood:
        msg += f"GrabFood: {grabfood}\n"; any_line = True
    if ubereats:
        msg += f"UberEats: {ubereats}\n"; any_line = True
    if doordash:
        msg += f"DoorDash: {doordash}\n"; any_line = True
    if deliveroo:
        msg += f"Deliveroo: {deliveroo}\n"; any_line = True
    if website:
        msg += f"Website order: {website}\n"; any_line = True

    if not any_line:
        msg += "Ordering links are not available right now. Please contact us and we’ll help you order 😊\n"

    msg += "\nJust choose whichever works best for you!"

    # ✨ DUA BUBBLE TERPISAH (Seperti sebelumnya)
    messages = [
        {"type": "text", "text": msg},
        {"type": "text", "text": "Want me to help you with anything else? 😄"},
    ]

    buttons = [
        {"label": "About us", "intent": "about_us"},
        {"label": "Opening hours", "intent": "hours"},
        {"label": "Location", "intent": "location"},
        {"label": "Contact / Reservation", "intent": "contact"},
        {"label": "No, I'm all good", "intent": "goodbye"},
        {"label": "Back", "intent": "menu"},
    ]
    return messages, buttons