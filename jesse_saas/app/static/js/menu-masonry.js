/**
 * JESSE.01 Masonry Menu Engine
 * Lightweight logic for Pinterest-style grid.
 */

document.addEventListener('DOMContentLoaded', () => {

    // -------------------------------------------------------------------------
    // 1. Sticky Navigation & Scroll Spy
    // -------------------------------------------------------------------------
    const navLinks = document.querySelectorAll('.category-nav-link');
    const sections = document.querySelectorAll('.menu-category-section');
    const navContainer = document.querySelector('.category-nav-container');

    // Scroll Spy
    window.addEventListener('scroll', () => {
        let current = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            // Offset for sticky header (approx 150px)
            if (scrollY >= (sectionTop - 180)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active-pill');
            if (link.getAttribute('href').includes(current)) {
                link.classList.add('active-pill');

                // Auto-scroll nav container to keep active pill in view
                const linkRect = link.getBoundingClientRect();
                const containerRect = navContainer.getBoundingClientRect();

                if (linkRect.left < containerRect.left || linkRect.right > containerRect.right) {
                    link.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                }
            }
        });
    });

    // Smooth Scroll for Links
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                const offset = 160; // Header height
                const bodyRect = document.body.getBoundingClientRect().top;
                const elementRect = targetSection.getBoundingClientRect().top;
                const elementPosition = elementRect - bodyRect;
                const offsetPosition = elementPosition - offset;

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
            setTimeout(() => {
                lb.classList.add('opacity-100');
                lb.querySelector('div[class*="transform"]').classList.remove('scale-95');
                lb.querySelector('div[class*="transform"]').classList.add('scale-100');
            }, 10);
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
        }
    };

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') window.closeLightbox();
    });
});
