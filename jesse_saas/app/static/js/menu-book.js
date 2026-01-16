/**
 * JESSE.01 Menu Book Engine
 * Handles 3D page flipping, visibility logic, lightbox, and scroll monitoring.
 */

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // 1. Initialization & Core State
    // -------------------------------------------------------------------------
    const book = document.getElementById('book');
    const totalPagesInput = document.getElementById('totalPages');

    // Fail safe if elements are missing (e.g. empty menu)
    if (!book || !totalPagesInput) return;

    const totalPages = parseInt(totalPagesInput.value);
    let currentPage = 0; // 0 = Cover
    const pages = document.querySelectorAll('.page');
    let isFlipping = false;

    // -------------------------------------------------------------------------
    // 2. Visibility & Stacking Logic
    // -------------------------------------------------------------------------
    function updateVisibility() {
        pages.forEach((page, index) => {
            // Reset basic properties
            page.style.display = 'block';
            page.style.visibility = 'visible';

            if (index < currentPage) {
                // Left stack (already flipped)
                page.classList.add('flipped');
                page.style.zIndex = index;
                page.style.pointerEvents = 'none';
            } else if (index === currentPage) {
                // Active page (centered)
                page.classList.remove('flipped');
                page.style.zIndex = 100;
                page.style.pointerEvents = isFlipping ? 'none' : 'auto';
            } else if (index === currentPage + 1) {
                // Peek next
                page.classList.remove('flipped');
                page.style.zIndex = 50;
                page.style.pointerEvents = 'none';
            } else {
                // Hidden future pages
                page.style.display = 'none';
                page.style.pointerEvents = 'none';
            }
        });
    }

    // Initial call
    updateVisibility();

    // -------------------------------------------------------------------------
    // 3. Navigation (Flip) Logic
    // -------------------------------------------------------------------------
    window.flipNext = function () { // Exposed to global window for onclick handlers
        if (currentPage < pages.length - 1 && !isFlipping) {
            const currentEl = document.getElementById(`page-${currentPage}`);
            if (currentEl) {
                isFlipping = true;
                currentEl.classList.add('flipped');
                currentEl.style.zIndex = 150; // Ensure it's on top DURING flip

                setTimeout(() => {
                    currentPage++;
                    isFlipping = false;
                    updateVisibility();
                }, 800); // 0.8s Match CSS transition duration
            }
        }
    };

    window.flipPrev = function () { // Exposed to global window
        if (currentPage > 0 && !isFlipping) {
            isFlipping = true;
            currentPage--;
            const prevEl = document.getElementById(`page-${currentPage}`);
            if (prevEl) {
                prevEl.style.zIndex = 150; // Bring it back to top
                // Trigger animation by removing class
                setTimeout(() => {
                    prevEl.classList.remove('flipped');
                    setTimeout(() => {
                        isFlipping = false;
                        updateVisibility();
                    }, 800);
                }, 10);
            }
        }
    };

    // -------------------------------------------------------------------------
    // 4. Click Navigation (Desktop)
    // -------------------------------------------------------------------------
    pages.forEach((page, index) => {
        page.addEventListener('click', (e) => {
            e.stopPropagation();

            // Only navigate on the current active centered page
            if (index !== currentPage) return;

            const rect = page.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const width = rect.width;

            if (x > width / 2) {
                window.flipNext();
            } else {
                window.flipPrev();
            }
        });
    });

    // -------------------------------------------------------------------------
    // 5. Touch / Swipe Logic
    // -------------------------------------------------------------------------
    // Note: Swipe is currently disabled for debugging mobile scroll issues.
    // Uncomment below if swipe navigation is desired.

    /*
    let touchStartX = 0;
    let touchEndX = 0;
    let touchStartY = 0;

    document.addEventListener('touchstart', e => {
        // CRITICAL: If touching menu grid, let browser handle native scroll. DO NOT INTERFERE.
        if (e.target.closest('.menu-grid')) return;

        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    document.addEventListener('touchend', e => {
        // CRITICAL: Ignore interaction if it started/ended in grid
        if (e.target.closest('.menu-grid')) return;
        if (touchStartX === 0 && touchStartY === 0) return; // touches ignored by start

        touchEndX = e.changedTouches[0].screenX;
        let touchEndY = e.changedTouches[0].screenY;

        // Calculate differences
        let xDiff = touchEndX - touchStartX;
        let yDiff = touchEndY - touchStartY;

        // If vertical scroll is significant, IGNORE (it was a scroll, not a swap)
        if (Math.abs(yDiff) > Math.abs(xDiff)) return;

        if (xDiff < -50) window.flipNext();
        if (xDiff > 50) window.flipPrev();

        // Reset
        touchStartX = 0;
        touchStartY = 0;
    }, { passive: true });
    */

    // -------------------------------------------------------------------------
    // 6. Jump To Category Logic
    // -------------------------------------------------------------------------
    window.jumpToCategory = function (categoryName) {
        const headers = document.querySelectorAll('h2');
        let targetHeader = null;
        for (let h of headers) {
            if (h.innerText.trim() === categoryName) {
                targetHeader = h;
                break;
            }
        }
        if (!targetHeader) return;
        const parentPage = targetHeader.closest('.page');
        if (!parentPage) return;

        const pageId = parentPage.id;
        const targetIndex = parseInt(pageId.split('-')[1]);

        if (targetIndex === currentPage) return;

        // Fast Sequential Flip (No Blackout)
        const direction = targetIndex > currentPage ? 1 : -1;
        isFlipping = true; // Lock interaction

        function step() {
            if (currentPage === targetIndex) {
                isFlipping = false;
                updateVisibility(); // Restore clicks
                return;
            }
            currentPage += direction;
            updateVisibility();

            // Speed depends on distance? Fixed 150ms is good for "riffling" effect
            setTimeout(step, 150);
        }
        step();
    };

    // -------------------------------------------------------------------------
    // 7. Lightbox Logic
    // -------------------------------------------------------------------------
    window.openLightbox = function (src) {
        const lb = document.getElementById('lightbox');
        const img = document.getElementById('lightbox-img');
        if (lb && img) {
            img.src = src;
            lb.style.display = 'flex';
            setTimeout(() => {
                lb.classList.add('show');
            }, 10);
            // Hide parent's close button (if in iframe)
            if (window.parent) {
                window.parent.postMessage({ type: 'TOGGLE_CLOSE_BUTTON', show: false }, '*');
            }
        }
    };

    window.closeLightbox = function () {
        const lb = document.getElementById('lightbox');
        if (lb) {
            lb.classList.remove('show');
            setTimeout(() => {
                lb.style.display = 'none';
            }, 300);
            // Show parent's close button
            if (window.parent) {
                window.parent.postMessage({ type: 'TOGGLE_CLOSE_BUTTON', show: true }, '*');
            }
        }
    };

    // -------------------------------------------------------------------------
    // 8. Auto-Link & Scroll Monitoring Utilities
    // -------------------------------------------------------------------------

    // Linkify Function
    const linkify = (text) => {
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        return text.replace(urlRegex, (url) => {
            const cleanUrl = url.replace(/[.,;!]$/, '');
            return `<a href="${cleanUrl}" target="_blank" class="underline decoration-white/50 hover:decoration-white transition-colors break-all relative z-50 pointer-events-auto cursor-pointer" onclick="event.stopPropagation(); window.open('${cleanUrl}', '_blank'); return false;">${cleanUrl}</a>`;
        });
    };

    // Apply to specific content
    document.querySelectorAll('.autolink-content').forEach(el => {
        el.innerHTML = linkify(el.innerHTML);
    });

    // Smart Scroll Indicator Logic
    const menuGrids = document.querySelectorAll('.menu-grid');
    const checkScroll = (grid) => {
        const indicator = grid.nextElementSibling;
        if (!indicator || !indicator.classList.contains('scroll-indicator')) return;

        // Threshold: only show if content is significantly larger (>20px) to avoid false positives
        const isScrollable = (grid.scrollHeight - grid.clientHeight) > 10;

        // Check if user is near bottom
        const isAtBottom = Math.ceil(grid.scrollTop + grid.clientHeight) >= (grid.scrollHeight - 5);

        if (!isScrollable) {
            indicator.style.display = 'none'; // Safe to hide if content is short
            indicator.style.opacity = '0';
        } else if (isAtBottom) {
            indicator.style.opacity = '0'; // Only fade out
        } else {
            indicator.style.display = 'flex'; // Ensure visible
            // Force reflow
            void indicator.offsetWidth;
            indicator.style.opacity = '0.5'; // Fade in
        }
    };

    const initScrollMonitors = () => {
        menuGrids.forEach(grid => {
            // 1. Initial Check
            checkScroll(grid);

            // 2. Scroll Listener
            grid.addEventListener('scroll', () => {
                const indicator = grid.nextElementSibling;
                if (indicator && indicator.classList.contains('scroll-indicator')) {
                    indicator.style.display = 'flex'; // Ensure generic display before opacity transition
                }
                checkScroll(grid);
            });

            // 3. Resize Observer (Detects image loads / content changes)
            const resizeObserver = new ResizeObserver(() => checkScroll(grid));
            resizeObserver.observe(grid);
            Array.from(grid.children).forEach(child => resizeObserver.observe(child));
        });
    };

    // Run Monitors
    initScrollMonitors();

    // Run again on Window Load (ensure all images loaded)
    window.addEventListener('load', () => {
        menuGrids.forEach(checkScroll);
    });
});
