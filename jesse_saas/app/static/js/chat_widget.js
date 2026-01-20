// chat_widget.js - Standalone Chat Logic (Dark/Light Themed & Client Branded)

const chatContainer = document.getElementById('chat-container');
const conversationArea = document.getElementById('conversation-area');
const inputField = document.getElementById('user-input');
const messagesEnd = document.getElementById('messages-end');

// === LIGHTBOX LOGIC ===
if (!document.getElementById('image-lightbox')) {
    const lightboxHtml = `
    <div id="image-lightbox" class="fixed inset-0 z-[9999] bg-black/90 hidden flex items-center justify-end md:justify-center p-4 cursor-zoom-out animate-fade-in" onclick="closeLightbox()">
        <img id="lightbox-img" src="" class="max-w-full max-h-full rounded shadow-2xl object-contain transition-transform duration-300">
        <button class="absolute top-4 right-4 text-white/70 hover:text-white bg-black/50 rounded-full p-2">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', lightboxHtml);
}

// === WEBVIEW OVERLAY LOGIC ===
if (!document.getElementById('webview-overlay')) {
    const webviewHtml = `
    <div id="webview-overlay" class="fixed inset-0 z-[10000] hidden flex flex-col animate-fade-in bg-black/90 backdrop-blur-md">
        <div class="absolute top-0 left-0 w-full p-4 flex justify-end z-[99999]">
            <button id="webview-close-btn" onclick="closeWebview()" class="bg-gray-900 hover:bg-black text-white rounded-full p-2 transition-all duration-300 shadow-xl border border-white/20 backdrop-blur-md opacity-100 transform scale-100 ring-2 ring-black/50">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
        <div class="flex-1 relative w-full h-full flex items-center justify-center p-0 md:p-8">
            <div id="webview-spinner" class="absolute inset-0 flex items-center justify-center text-white">
                 <svg class="animate-spin h-10 w-10" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            </div>
            <iframe id="webview-iframe" class="w-full h-full md:rounded-lg overflow-hidden border-none opacity-0 transition-opacity duration-300 shadow-2xl" src="" onload="document.getElementById('webview-spinner').style.display='none'; this.classList.remove('opacity-0')"></iframe>
        </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', webviewHtml);
}

window.openWebview = function (url) {
    const box = document.getElementById('webview-overlay');
    const iframe = document.getElementById('webview-iframe');
    const spinner = document.getElementById('webview-spinner');
    if (box && iframe) {
        if (spinner) spinner.style.display = 'flex';
        iframe.classList.add('opacity-0');
        iframe.src = url;
        box.classList.remove('hidden');
    }
}

window.closeWebview = function () {
    const box = document.getElementById('webview-overlay');
    const iframe = document.getElementById('webview-iframe');
    if (box) {
        box.classList.add('hidden');
        if (iframe) iframe.src = ''; // Stop loading
    }
}

// Listen for messages from iframe to toggle close button visibility
window.addEventListener('message', function (event) {
    if (event.data && event.data.type === 'TOGGLE_CLOSE_BUTTON') {
        const closeBtn = document.getElementById('webview-close-btn');
        if (closeBtn) {
            if (event.data.show) {
                closeBtn.classList.remove('opacity-0', 'pointer-events-none', 'scale-90');
                closeBtn.classList.add('opacity-100', 'scale-100');
            } else {
                closeBtn.classList.remove('opacity-100', 'scale-100');
                closeBtn.classList.add('opacity-0', 'pointer-events-none', 'scale-90');
            }
        }
    }
});

window.openLightbox = function (src) {
    const box = document.getElementById('image-lightbox');
    const img = document.getElementById('lightbox-img');
    if (box && img) {
        img.src = src;
        box.classList.remove('hidden');
    }
}

window.closeLightbox = function () {
    const box = document.getElementById('image-lightbox');
    if (box) box.classList.add('hidden');
}

// === THEME MANAGEMENT ===
function toggleTheme() {
    const html = document.documentElement;
    html.classList.toggle('dark');

    const isDark = html.classList.contains('dark');
    const theme = isDark ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
    updateThemeIcons(isDark);

    // Sync with Webview Iframe
    const iframe = document.getElementById('webview-iframe');
    if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage({ type: 'THEME_CHANGE', theme: theme }, '*');
    }
}

function updateThemeIcons(isDark) {
    const sunIcon = document.getElementById('icon-sun');
    const moonIcon = document.getElementById('icon-moon');

    if (isDark) {
        sunIcon.classList.remove('hidden');
        moonIcon.classList.add('hidden');
    } else {
        sunIcon.classList.add('hidden');
        moonIcon.classList.remove('hidden');
    }
}

// Init Theme
(function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.classList.add('dark');
        updateThemeIcons(true);
    } else {
        document.documentElement.classList.remove('dark');
        updateThemeIcons(false);
    }
})();


// === CHAT LOGIC ===

function scrollToBottom() {
    messagesEnd.scrollIntoView({ behavior: "smooth" });
}

function linkify(text) {
    if (!text) return '';

    // 1. Emails
    text = text.replace(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+)/gi, '<a href="mailto:$1" class="text-blue-600 hover:text-blue-800 underline break-words z-50 relative pointer-events-auto">$1</a>');

    // 2. Standard URLs (http/https)
    // Negative lookbehind or simple replacement - regex here expects protocol
    const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
    text = text.replace(urlRegex, function (url) {
        return '<a href="' + url + '" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline break-words z-50 relative pointer-events-auto">' + url + '</a>';
    });

    // 3. Naked Domains (www, instagram.com, tiktok.com) - preceded by start or space
    // We avoid matching things already inside quotes (hrefs) by ensuring space/start prefix
    const nakedRegex = /(^|[\s\n])((?:www\.|instagram\.com|tiktok\.com|facebook\.com|x\.com|twitter\.com)[a-zA-Z0-9\-\.\/\_\?\=\+\&\%\@]+)/gim;
    text = text.replace(nakedRegex, function (match, prefix, content) {
        return prefix + '<a href="https://' + content + '" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline break-words z-50 relative pointer-events-auto">' + content + '</a>';
    });

    return text;
}

function appendMessage(text, sender) {
    const div = document.createElement('div');
    if (sender === 'user') {
        div.className = 'flex justify-end w-full animate-fade-in-up mb-2';

        div.innerHTML = `
            <div class="flex items-end gap-2 mb-1 justify-end w-full">
                <div class="rounded-2xl rounded-tr-none px-4 py-3 shadow-md text-sm text-white max-w-[85%] leading-relaxed font-medium whitespace-pre-line"
                     style="background-color: ${typeof CLIENT_THEME !== 'undefined' ? CLIENT_THEME : '#2563EB'}">${text}</div>
            </div>
        `;
    } else {
        let avatarHtml = '';
        if (typeof BOT_AVATAR_URL !== 'undefined' && BOT_AVATAR_URL) {
            avatarHtml = `<img src="${BOT_AVATAR_URL}" class="w-8 h-8 rounded-full object-cover border border-[var(--border-color)] shadow-sm">`;
        } else {
            const themeStyle = typeof CLIENT_THEME !== 'undefined' ? `style="background-color: ${CLIENT_THEME}; color: white;"` : 'class="bg-blue-900/50 text-blue-400"';
            avatarHtml = `<div class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs border border-[var(--border-color)] shadow-sm" ${themeStyle}>${typeof CLIENT_INITIAL !== 'undefined' ? CLIENT_INITIAL : 'B'}</div>`;
        }

        // Logic to detect if "text" is actually an object { text, image }
        let messageText = text;
        let imageHtml = '';

        if (typeof text === 'object' && text !== null) {
            messageText = text.text || '';
            if (text.image) {
                imageHtml = `<img src="${text.image}" onclick="openLightbox('${text.image}')" class="w-full h-32 object-cover rounded-lg mb-2 border border-gray-200 cursor-zoom-in hover:opacity-95 transition-opacity">`;
            }
        }

        div.className = 'flex flex-col items-start w-full animate-fade-in-up mb-4';
        div.innerHTML = `
            <div class="flex items-end gap-2 mb-1">
                ${avatarHtml}
                <div class="px-4 py-3 rounded-2xl rounded-tl-none shadow-sm text-sm leading-relaxed border transition-colors duration-300 max-w-[85%] break-words bg-white whitespace-pre-line"
                     style="background-color: var(--bg-bubble-bot); border: 1px solid var(--border-color); color: var(--text-primary);">${imageHtml}${linkify(messageText)}</div>
            </div>
            <div class="generated-buttons flex flex-wrap gap-2 mt-2 ml-10 justify-start"></div>
        `;
    }

    conversationArea.appendChild(div);
    scrollToBottom();
    return div;
}

// === TYPING INDICATOR ===
let typingIndicatorDiv = null;

function showTypingIndicator() {
    if (typingIndicatorDiv) return; // Already showing

    typingIndicatorDiv = document.createElement('div');
    typingIndicatorDiv.className = 'flex flex-col items-start w-full animate-fade-in-up mb-4';

    // Check if avatar logic needs to be repeated or simplified
    let avatarHtml = '';
    if (typeof BOT_AVATAR_URL !== 'undefined' && BOT_AVATAR_URL) {
        avatarHtml = `<img src="${BOT_AVATAR_URL}" class="w-8 h-8 rounded-full object-cover border border-[var(--border-color)] shadow-sm">`;
    } else {
        const themeStyle = typeof CLIENT_THEME !== 'undefined' ? `style="background-color: ${CLIENT_THEME}; color: white;"` : 'class="bg-blue-900/50 text-blue-400"';
        avatarHtml = `<div class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs border border-[var(--border-color)] shadow-sm" ${themeStyle}>${typeof CLIENT_INITIAL !== 'undefined' ? CLIENT_INITIAL : 'B'}</div>`;
    }

    typingIndicatorDiv.innerHTML = `
        <div class="flex items-end gap-2 mb-1">
            ${avatarHtml}
            <div class="px-4 py-3 rounded-2xl rounded-tl-none shadow-sm text-sm border transition-colors duration-300"
                 style="background-color: var(--bg-bubble-bot); border: 1px solid var(--border-color); color: var(--text-primary);">
                 <div class="typing-indicator">
                    <span></span><span></span><span></span>
                 </div>
            </div>
        </div>
    `;

    conversationArea.appendChild(typingIndicatorDiv);
    scrollToBottom();
}

function hideTypingIndicator() {
    if (typingIndicatorDiv) {
        typingIndicatorDiv.remove();
        typingIndicatorDiv = null;
    }
}

function handleAction(arg1, arg2, arg3) {
    let btnData;
    let event = null;

    // Check if the last argument is an Event object (simulated overloading)
    // When called from onclick: handleAction(btn, event)
    if (arguments.length === 2 && arguments[1] instanceof Event) {
        btnData = arg1;
        event = arg2;
    }
    // Legacy/Direct calls
    else if (typeof arg1 === 'object' && arg1 !== null) {
        btnData = arg1;
    } else {
        btnData = { action: arg1, payload: arg2, label: arg3 };
    }

    // Disable clicked button group
    // CHANGED: Do NOT disable if it's a persistent action like 'open_menu' or 'link' (if we want that)
    // The user specifically wants 'open_menu' (Main Button) to be reusable.
    const isPersistent = btnData.action === 'open_menu' || btnData.action === 'link';

    if (event && event.target && !isPersistent) {
        const btn = event.target.closest('button');
        if (btn) {
            const container = btn.parentElement;
            if (container && container.classList.contains('generated-buttons')) {
                const siblings = container.querySelectorAll('button');
                siblings.forEach(b => {
                    b.disabled = true;
                    b.classList.add('opacity-50', 'cursor-not-allowed');
                });
            }
        }
    }

    if (btnData.action === 'link' && btnData.payload) {
        // Generic Overlay Check
        if (btnData.open_in_overlay) {
            openWebview(btnData.payload);
        } else {
            window.open(btnData.payload, '_blank');
        }
        return;
    }

    // === DYNAMIC MENU ROUTING ===
    if (btnData.action === 'open_menu' || btnData.payload === '_DYNAMIC_MENU_LINK_') {
        const menuUrl = `/menu/${typeof CLIENT_PUBLIC_ID !== 'undefined' ? CLIENT_PUBLIC_ID : 'error'}`;
        openWebview(menuUrl);
        return;
    }

    if (btnData.action === 'main_menu') {
        appendMessage(btnData.label, 'user');
        showTypingIndicator();
        setTimeout(() => {
            hideTypingIndicator();
            const text = btnData.response_text || btnData.payload || "Here are the main options:";
            const botMsgDiv = appendMessage(text, 'bot');
            const btnContainer = botMsgDiv.querySelector('.generated-buttons');
            // Re-render original starters
            if (typeof STARTERS_DATA !== 'undefined' && btnContainer) {
                renderInlineButtons(STARTERS_DATA, btnContainer);
            }
            scrollToBottom();
        }, 600);
        return;
    }

    if (btnData.action === 'back_to_menu_chips') {
        appendMessage(btnData.label, 'user');
        showTypingIndicator();
        setTimeout(() => {
            hideTypingIndicator();
            const text = btnData.response_text || "Here are the menu options:";
            const botMsgDiv = appendMessage(text, 'bot');
            const btnContainer = botMsgDiv.querySelector('.generated-buttons');

            // Logic: Find the Global Menu Button (usually first starter) and render its sub-buttons (Chips)
            if (typeof STARTERS_DATA !== 'undefined' && STARTERS_DATA.length > 0) {
                const menuBtn = STARTERS_DATA[0];
                if (menuBtn && menuBtn.sub_buttons) {
                    renderInlineButtons(menuBtn.sub_buttons, btnContainer); // Only Chips, NO Back Button
                } else {
                    // Fallback if no chips found
                    renderInlineButtons(STARTERS_DATA, btnContainer);
                }
            }
            scrollToBottom();
        }, 600);
        return;
    }

    if (btnData.action === 'menu') {
        appendMessage(btnData.label, 'user');
        showTypingIndicator();
        setTimeout(() => {
            hideTypingIndicator();
            if (typeof MENU_DATA === 'undefined' || MENU_DATA.length === 0) {
                appendMessage("Sorry, the menu is currently not available.", 'bot');
                return;
            }

            // Extract unique categories
            const categories = [...new Set(MENU_DATA.map(item => item.category).filter(c => c))];

            if (categories.length === 0) {
                // No categories, show all items directly? Or just say empty.
                appendMessage("No menu categories found.", 'bot');
                return;
            }

            const header = (typeof MENU_CONFIG !== 'undefined' && MENU_CONFIG.message) ? MENU_CONFIG.message : (btnData.response_text || "Please select a category:");
            const botMsgDiv = appendMessage(header, 'bot');
            const btnContainer = botMsgDiv.querySelector('.generated-buttons');

            const catButtons = categories.map(cat => ({
                label: cat,
                action: 'menu_category',
                payload: cat
            }));

            // Add Custom Menu Buttons
            if (typeof MENU_CONFIG !== 'undefined' && MENU_CONFIG.buttons && MENU_CONFIG.buttons.length > 0) {
                catButtons.push(...MENU_CONFIG.buttons);
            } else {
                // Default Fallback
                catButtons.push({ label: 'Main Menu', action: 'main_menu', response_text: 'Returning to main menu...' });
            }

            renderInlineButtons(catButtons, btnContainer);
            scrollToBottom();
        }, 600);
        return;
    }

    if (btnData.action === 'menu_category') {
        appendMessage(btnData.payload, 'user');
        showTypingIndicator();
        setTimeout(() => {
            hideTypingIndicator();
            const category = btnData.payload;
            const items = MENU_DATA.filter(item => item.category === category);

            if (items.length === 0) {
                appendMessage(`No items found in ${category}.`, 'bot');
                return;
            }

            const botMsgDiv = appendMessage(`Here are our ${category} items:`, 'bot');
            const btnContainer = botMsgDiv.querySelector('.generated-buttons');

            const itemButtons = items.map(item => ({
                label: `${item.name} (${MENU_CURRENCY || '$'}${item.price})`,
                action: 'menu_item',
                payload: item.id
            }));

            itemButtons.push({ label: '⬅ Back to Categories', action: 'menu', label_override: 'Back to Categories' });

            // Add Custom Menu Buttons
            if (typeof MENU_CONFIG !== 'undefined' && MENU_CONFIG.buttons && MENU_CONFIG.buttons.length > 0) {
                itemButtons.push(...MENU_CONFIG.buttons);
            } else {
                itemButtons.push({ label: 'Main Menu', action: 'main_menu', response_text: 'Returning to main menu...' });
            }

            renderInlineButtons(itemButtons, btnContainer);
            scrollToBottom();
        }, 600);
        return;
    }

    if (btnData.action === 'menu_item') {
        // Find item by ID
        const itemId = parseInt(btnData.payload);
        const item = MENU_DATA.find(i => i.id === itemId);

        if (!item) return;

        appendMessage(item.name, 'user');
        showTypingIndicator();
        setTimeout(() => {
            hideTypingIndicator();

            // Create rich card for item
            const currency = typeof MENU_CURRENCY !== 'undefined' ? MENU_CURRENCY : '$';
            const botMsgDiv = document.createElement('div');
            botMsgDiv.className = 'flex flex-col items-start w-full animate-fade-in-up mb-4';

            // Reuse avatar logic (simplified)
            const themeStyle = typeof CLIENT_THEME !== 'undefined' ? `style="background-color: ${CLIENT_THEME}; color: white;"` : 'class="bg-blue-900/50 text-blue-400"';
            const avatar = `<div class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs border border-[var(--border-color)] shadow-sm" ${themeStyle}>${typeof CLIENT_INITIAL !== 'undefined' ? CLIENT_INITIAL : 'B'}</div>`; // Logic usually handles image vs text better but this is quick access

            botMsgDiv.innerHTML = `
                <div class="flex items-end gap-2 mb-1">
                    ${avatar}
                    <div class="px-4 py-3 rounded-2xl rounded-tl-none shadow-sm text-sm border transition-colors duration-300 max-w-[85%] bg-white border-gray-200">
                        ${item.image_url ? `<img src="/static/uploads/menu/${item.image_url}" class="w-full h-32 object-cover rounded-md mb-2">` : ''}
                        <h3 class="font-bold text-gray-800 text-lg">${item.name}</h3>
                        <p class="text-blue-600 font-semibold mb-1">${currency}${item.price}</p>
                        <p class="text-gray-600 text-xs mb-2">${item.description || 'No description available.'}</p>
                    </div>
                </div>
                <div class="generated-buttons flex flex-wrap gap-2 mt-2 ml-10 justify-start"></div>
             `;

            conversationArea.appendChild(botMsgDiv);

            // Add "Back" button and Custom Buttons
            const btnContainer = botMsgDiv.querySelector('.generated-buttons');
            let detailButtons = [
                { label: `⬅ Back to ${item.category}`, action: 'menu_category', payload: item.category }
            ];

            if (typeof MENU_CONFIG !== 'undefined' && MENU_CONFIG.buttons && MENU_CONFIG.buttons.length > 0) {
                detailButtons.push(...MENU_CONFIG.buttons);
            } else {
                detailButtons.push({ label: 'Main Menu', action: 'main_menu', response_text: 'Returning to main menu...' });
            }

            renderInlineButtons(detailButtons, btnContainer);

            scrollToBottom();
        }, 600);
        return;
    }

    appendMessage(btnData.label, 'user');
    showTypingIndicator(); // UX: Show bot is "thinking"

    setTimeout(async () => { // Async for sequencing
        hideTypingIndicator(); // UX: Remove before showing response

        // Priority: Blocks > Legacy
        if (btnData.blocks && Array.isArray(btnData.blocks) && btnData.blocks.length > 0) {
            for (let i = 0; i < btnData.blocks.length; i++) {
                const block = btnData.blocks[i];
                // Render block (Universal: Text + Optional Image)
                const msgPayload = { text: block.text || '', image: block.url || null };
                const botMsgDiv = appendMessage(msgPayload, 'bot');

                // Attach Sub-Buttons only to LAST block
                if (i === btnData.blocks.length - 1) {
                    const btnContainer = botMsgDiv.querySelector('.generated-buttons');

                    // 1. Nested Follow-up Buttons (Specific to this item)
                    if (btnData.sub_buttons && btnData.sub_buttons.length > 0) {
                        renderInlineButtons(btnData.sub_buttons, btnContainer);
                    }

                    // 2. Persistent Menu Chips (Sibling Navigation)
                    // If this is a defined flow (has blocks) but NOT the Main Menu itself (which owns the chips)
                    if (typeof STARTERS_DATA !== 'undefined' && STARTERS_DATA.length > 0) {
                        const menuBtn = STARTERS_DATA[0];
                        // Avoid duplication if we are actually clicking the Menu Button itself
                        if (btnData !== menuBtn && menuBtn.sub_buttons && menuBtn.sub_buttons.length > 0) {
                            // Append 'Back' button to these persistent chips to allow exiting the flow
                            const backLabel = menuBtn.back_label || '⬅ Back';
                            const backResponse = menuBtn.back_response;

                            // Filter out existing Back/MainMenu buttons to avoid duplicates
                            const safeChips = menuBtn.sub_buttons.filter(b => b.action !== 'main_menu' && b.action !== 'back_to_menu_chips');

                            const chipsWithBack = [...safeChips, {
                                label: backLabel,
                                action: 'back_to_menu_chips', // CHANGED: Special action for Menu Chips Back
                                response_text: backResponse
                            }];
                            renderInlineButtons(chipsWithBack, btnContainer);
                        }
                    }

                    if (btnData.include_main_menu && typeof STARTERS_DATA !== 'undefined') {
                        renderInlineButtons(STARTERS_DATA, btnContainer);
                    }
                }
                // Small delay between blocks for realism
                if (i < btnData.blocks.length - 1) await new Promise(r => setTimeout(r, 400));
            }
            scrollToBottom();
        }
        else if (btnData.response_text) {
            const messageData = btnData.image_url ? { text: btnData.response_text, image: btnData.image_url } : btnData.response_text;
            const botMsgDiv = appendMessage(messageData, 'bot');
            if (btnData.sub_buttons && btnData.sub_buttons.length > 0) {
                const btnContainer = botMsgDiv.querySelector('.generated-buttons');
                renderInlineButtons(btnData.sub_buttons, btnContainer);
            }
            // Auto-render Main Menu if configured
            if (btnData.include_main_menu && typeof STARTERS_DATA !== 'undefined') {
                const btnContainer = botMsgDiv.querySelector('.generated-buttons');
                renderInlineButtons(STARTERS_DATA, btnContainer);
            }
            scrollToBottom();
        }
    }, 600);
}

function renderInlineButtons(buttons, container) {
    if (!container) return;
    buttons.forEach(btn => {
        if (!btn.label) return;

        const btnEl = document.createElement('button');

        // Match index.html <button> classes: dynamic-btn px-4 py-2 rounded-2xl text-xs font-medium border shadow-sm whitespace-normal h-auto leading-tight text-center max-w-[200px]
        btnEl.className = 'dynamic-btn px-4 py-2 rounded-2xl text-xs font-medium border shadow-sm whitespace-normal h-auto leading-tight text-center max-w-[200px]';

        // CSS Variable for Theme Color (matches index.html logic)
        const themeColor = typeof CLIENT_THEME !== 'undefined' ? CLIENT_THEME : '#2563EB';
        btnEl.style.setProperty('--btn-color', themeColor);

        btnEl.innerText = btn.label;
        btnEl.onclick = (e) => handleAction(btn, e);
        container.appendChild(btnEl);
    });
}

function handleUserSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    input.value = '';
    showTypingIndicator();

    // Prepare Payload
    const payload = {
        public_id: typeof CLIENT_PUBLIC_ID !== 'undefined' ? CLIENT_PUBLIC_ID : '',
        type: 'text_input',
        message: text
    };

    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            hideTypingIndicator();
            if (data.error) {
                appendMessage("⚠️ " + (data.message || "An error occurred."), 'bot'); // Show error gracefully
            } else {
                appendMessage(data.response, 'bot');
            }
        })
        .catch(error => {
            hideTypingIndicator();
            console.error('Chat Error:', error);
            appendMessage("I'm having trouble connecting to the server. Please try again.", 'bot');
        });
}
