(function () {
    // 1. Initialization
    const scriptTag = document.currentScript || document.querySelector('script[data-id]');
    if (!scriptTag) {
        console.error("JESSE Widget: Could not find script tag with data-id attribute.");
        return;
    }
    const PUBLIC_ID = scriptTag.getAttribute('data-id');
    const MODE = scriptTag.getAttribute('data-mode') || 'widget'; // 'widget' or 'fullscreen'
    // Remove 'static/widget.js' to get base URL (e.g. http://localhost:5000)
    const API_BASE = scriptTag.src.replace(/\/static\/widget\.js$/, '');

    // 2. Fetch Configuration
    fetch(`${API_BASE}/api/config/${PUBLIC_ID}`)
        .then(response => {
            if (!response.ok) throw new Error("Failed to load widget config");
            return response.json();
        })
        .then(config => {
            initWidget(config);
        })
        .catch(err => {
            console.error("JESSE Widget Error:", err);
            // Fallback Init
            initWidget({ theme_color: '#2563EB' });
        });

    function initWidget(config) {
        const THEME_COLOR = config.theme_color || '#2563EB';
        const AVATAR_URL = config.avatar_url || null;

        // 3. Create Elements
        const bubble = document.createElement('div');
        bubble.id = 'jesse-bubble';

        const container = document.createElement('div');
        container.id = 'jesse-container';

        const iframe = document.createElement('iframe');
        iframe.id = 'jesse-iframe';
        iframe.src = `${API_BASE}/chat/${PUBLIC_ID}?mode=embed`;
        iframe.allow = "clipboard-write";

        // 4. Styles
        const style = document.createElement('style');
        style.innerHTML = `
            :root {
                --j-primary: ${THEME_COLOR};
            }
            #jesse-bubble {
                position: fixed; bottom: 20px; right: 20px;
                width: 60px; height: 60px;
                background-color: var(--j-primary);
                border-radius: 50%;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
                cursor: pointer; z-index: 99999;
                display: flex; align-items: center; justify-content: center;
                transition: transform 0.2s, opacity 0.2s;
            }
            #jesse-bubble:hover { transform: scale(1.05); }
            #jesse-bubble svg { width: 30px; height: 30px; stroke: white; }
            #jesse-bubble img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }

            #jesse-container {
                position: fixed; bottom: 100px; right: 20px;
                width: 380px; height: 650px;
                max-height: 80vh;
                background: transparent;
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                z-index: 99999;
                opacity: 0; pointer-events: none; transform: translateY(20px);
                transition: opacity 0.3s ease, transform 0.3s ease;
                overflow: hidden;
            }
            #jesse-container.open {
                opacity: 1; pointer-events: all; transform: translateY(0);
            }
            
            #jesse-iframe {
                width: 100%; height: 100%;
                border: none;
                background: #121212; /* Match chat bg to avoid white flash, assuming dark default */
            }

            /* Mobile Responsive */
            @media (max-width: 480px) {
                #jesse-container {
                    bottom: 0px; right: 0px;
                    width: 100%; height: 100%;
                    max-height: 100%;
                    border-radius: 0;
                }
            }
        `;
        document.head.appendChild(style);

        // 5. Initial Icon (Avatar or SVG)
        if (AVATAR_URL) {
            bubble.innerHTML = `<img src="${AVATAR_URL}" alt="Chat">`;
        } else {
            bubble.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2-2z"></path></svg>`;
        }

        // 6. Assemble
        container.appendChild(iframe);
        document.body.appendChild(bubble);
        document.body.appendChild(container);

        // 7. Logic
        let isOpen = false;
        function toggleChat() {
            isOpen = !isOpen;
            if (isOpen) {
                container.classList.add('open');
                // Always show Close Icon when open
                bubble.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
            } else {
                container.classList.remove('open');
                // Restore Avatar or Default Icon
                if (AVATAR_URL) {
                    bubble.innerHTML = `<img src="${AVATAR_URL}" alt="Chat">`;
                } else {
                    bubble.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2-2z"></path></svg>`;
                }
            }
        }
        bubble.onclick = toggleChat;

        // Fullscreen Mode override
        if (MODE === 'fullscreen') {
            bubble.style.display = 'none';
            container.style.bottom = '0';
            container.style.right = '0';
            container.style.width = '100%';
            container.style.height = '100%';
            container.style.borderRadius = '0';
            container.style.maxHeight = '100vh';
            container.classList.add('open');
        }
    }

})();
