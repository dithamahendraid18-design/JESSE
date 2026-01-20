/**
 * JESSE.01 Masonry Menu Engine
 * Lightweight logic for Pinterest-style grid.
 */

document.addEventListener('DOMContentLoaded', () => {

    // -------------------------------------------------------------------------
    // 1. Sticky Navigation & Scroll Spy (Optimized)
    // -------------------------------------------------------------------------
    const navLinks = document.querySelectorAll('.category-nav-link');
    const sections = document.querySelectorAll('.menu-category-section');
    const navContainer = document.querySelector('.category-nav-container');
    const header = document.querySelector('header');

    // Helper: Debounce function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Dynamic Offset Calculation
    const getHeaderOffset = () => header ? header.offsetHeight + 20 : 160;

    // Scroll Spy Logic
    const onScroll = () => {
        let current = '';
        const offset = getHeaderOffset();

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            // Activate when section is slightly below the header line
            if (scrollY >= (sectionTop - offset - 50)) {
                current = section.getAttribute('id');
            }
        });

        // Special check: if at bottom of page, activate last link
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 50) {
            current = sections[sections.length - 1].getAttribute('id');
        }

        navLinks.forEach(link => {
            link.classList.remove('active-pill');
            if (link.getAttribute('href').includes(`#${current}`)) {
                link.classList.add('active-pill');

                // Smooth Center Active Pill
                link.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
            }
        });
    };

    // Use debounced scroll listener (10ms is fast enough for visual but saves CPU)
    window.addEventListener('scroll', debounce(onScroll, 10));

    // Smooth Scroll for Links
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);

            if (targetSection) {
                const headerOffset = getHeaderOffset();
                const elementPosition = targetSection.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: "smooth"
                });
            }
        });
    });

    // -------------------------------------------------------------------------
    // 2. Lightbox Logic
    // -------------------------------------------------------------------------
    window.openLightbox = function (imgUrl, title, desc, price) {
        const lb = document.getElementById('lightbox');
        const lbImg = document.getElementById('lightbox-img');
        const lbTitle = document.getElementById('lightbox-title');
        const lbDesc = document.getElementById('lightbox-desc');
        const lbPrice = document.getElementById('lightbox-price');

        if (lb && lbImg) {
            lbImg.src = imgUrl;
            if (lbTitle) lbTitle.textContent = title || '';
            if (lbDesc) lbDesc.textContent = desc || '';
            if (lbPrice) lbPrice.textContent = price || '';

            lb.classList.remove('hidden');
            // Small delay to allow display flex to apply before opacity transition
            requestAnimationFrame(() => {
                lb.classList.add('opacity-100');
                lb.querySelector('div[class*="transform"]').classList.remove('scale-95');
                lb.querySelector('div[class*="transform"]').classList.add('scale-100');
            });
            // Hide Main Close Button
            window.parent.postMessage({ type: 'TOGGLE_CLOSE_BUTTON', show: false }, '*');
        }
    };

    window.closeLightbox = function () {
        const lb = document.getElementById('lightbox');
        if (lb) {
            lb.classList.remove('opacity-100');
            lb.querySelector('div[class*="transform"]').classList.remove('scale-100');
            lb.querySelector('div[class*="transform"]').classList.add('scale-95');
            setTimeout(() => {
                lb.classList.add('hidden');
            }, 300);
            // Show Main Close Button
            window.parent.postMessage({ type: 'TOGGLE_CLOSE_BUTTON', show: true }, '*');
        }
    };

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') window.closeLightbox();
    });

    // -------------------------------------------------------------------------
    // 3. Search Logic (Mobile & Desktop)
    // -------------------------------------------------------------------------
    const searchInput = document.getElementById('menuSearch');
    if (searchInput) {
        const sections = document.querySelectorAll('.menu-category-section');

        const filterMenu = (e) => {
            const term = e.target.value.toLowerCase().trim();

            sections.forEach(section => {
                let hasVisibleItems = false;
                // Select item cards
                const items = section.querySelectorAll('.group.relative');

                items.forEach(item => {
                    const title = (item.dataset.title || '').toLowerCase();
                    const desc = (item.dataset.desc || '').toLowerCase();

                    // Check match
                    const isMatch = title.includes(term) || desc.includes(term);

                    // Toggle visibility of the PARENT wrapper (grid column)
                    const wrapper = item.closest('.w-full');
                    if (wrapper) {
                        if (isMatch) {
                            wrapper.style.display = 'block';
                            hasVisibleItems = true;
                        } else {
                            wrapper.style.display = 'none';
                        }
                    }
                });

                // Toggle Section visibility
                if (hasVisibleItems) {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        };

        // Listen to 'input' (standard) and 'keyup' (fallback for some mobile keyboards)
        searchInput.addEventListener('input', filterMenu);
        searchInput.addEventListener('keyup', filterMenu);
    }
});
