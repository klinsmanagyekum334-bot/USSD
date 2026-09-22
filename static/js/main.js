/* =========================================================
   Dr. Isaac Frimpong — main.js
   Dropdown menu • Slider • Search • Lively Emoji Strip
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

    /* ---------- DROPDOWN MENU ---------- */
    const menuBtn = document.getElementById('menuBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');

    function openMenu() {
        if (!dropdownMenu || !menuBtn) return;
        dropdownMenu.classList.add('open');
        menuBtn.classList.add('active');
        menuBtn.setAttribute('aria-expanded', 'true');
    }
    function closeMenu() {
        if (!dropdownMenu || !menuBtn) return;
        dropdownMenu.classList.remove('open');
        menuBtn.classList.remove('active');
        menuBtn.setAttribute('aria-expanded', 'false');
    }
    function toggleMenu(e) {
        e.stopPropagation();
        if (dropdownMenu.classList.contains('open')) closeMenu();
        else openMenu();
    }

    if (menuBtn) menuBtn.addEventListener('click', toggleMenu);

    // Close dropdown when clicking anywhere else
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.menu-wrap')) closeMenu();
    });

    // Close dropdown when a link inside it is clicked
    if (dropdownMenu) {
        dropdownMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMenu);
        });
    }

    // Close on ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeMenu();
    });


    /* ---------- AUTO-ROTATING SLIDER ---------- */
    const slides = document.querySelectorAll('.slide');
    const dotsContainer = document.querySelector('.slider-dots');

    if (slides.length > 0) {
        let currentIndex = 0;
        const intervalTime = 4000;

        if (dotsContainer) {
            slides.forEach((_, i) => {
                const dot = document.createElement('button');
                dot.setAttribute('aria-label', 'Go to slide ' + (i + 1));
                if (i === 0) dot.classList.add('active');
                dot.addEventListener('click', () => goToSlide(i));
                dotsContainer.appendChild(dot);
            });
        }

        const dots = dotsContainer ? dotsContainer.querySelectorAll('button') : [];

        function goToSlide(index) {
            slides[currentIndex].classList.remove('active');
            if (dots[currentIndex]) dots[currentIndex].classList.remove('active');
            currentIndex = index;
            slides[currentIndex].classList.add('active');
            if (dots[currentIndex]) dots[currentIndex].classList.add('active');
        }
        function nextSlide() {
            goToSlide((currentIndex + 1) % slides.length);
        }

        let sliderTimer = setInterval(nextSlide, intervalTime);
        const sliderEl = document.querySelector('.slider');
        if (sliderEl) {
            sliderEl.addEventListener('mouseenter', () => clearInterval(sliderTimer));
            sliderEl.addEventListener('mouseleave', () => {
                sliderTimer = setInterval(nextSlide, intervalTime);
            });
        }
    }


    /* ---------- SMOOTH SCROLL FOR HASH LINKS ---------- */
    document.querySelectorAll('a[href*="#"]').forEach(link => {
        link.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            const hashIndex = href.indexOf('#');
            if (hashIndex === -1) return;
            const targetId = href.substring(hashIndex + 1);
            if (!targetId) return;
            const target = document.getElementById(targetId);
            if (target) {
                e.preventDefault();
                const offset = 90;
                const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
                window.scrollTo({ top: top, behavior: 'smooth' });
            }
        });
    });


    /* =========================================================
       SITE-WIDE SEARCH
       ========================================================= */

    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const searchGo = document.getElementById('searchGo');

    if (searchInput && searchResults) {

        const siteIndex = [
            { title: 'Anxiety or constant worry',   url: '/#s-anxiety',     category: 'Home' },
            { title: 'Depression or low mood',      url: '/#s-depression',  category: 'Home' },
            { title: 'Relationship strain or conflict', url: '/#s-relationship', category: 'Home' },
            { title: 'Grief and loss',              url: '/#s-grief',       category: 'Home' },
            { title: 'Stress and burnout',          url: '/#s-stress',      category: 'Home' },
            { title: 'Low self-esteem or confidence', url: '/#s-selfesteem', category: 'Home' },
            { title: 'Life transitions or big decisions', url: '/#s-transitions', category: 'Home' },
            { title: 'Trauma, fear or past hurt',   url: '/#s-trauma',      category: 'Home' },
            { title: 'A space where you are heard', url: '/#intro',         category: 'Home' },
            { title: 'What clients say — testimonials', url: '/#testimonials', category: 'Home' },
            { title: 'Contact Dr. Isaac — email or WhatsApp', url: '/#contact', category: 'Home' },
            { title: "You don't have to carry it alone", url: '/#',         category: 'Home' },
            { title: 'Meet Dr. Isaac Frimpong',     url: '/about',          category: 'About' },
            { title: 'About — 15 years of experience', url: '/about',       category: 'About' },
            { title: 'Credentials and trust',       url: '/about',          category: 'About' },
            { title: 'Why clients trust Dr. Isaac', url: '/about',          category: 'About' },
            { title: 'How it works — 3 simple steps', url: '/about',        category: 'About' },
            { title: 'Licensed professional counselor', url: '/about',      category: 'About' },
            { title: 'Confidential and ethical practice', url: '/about',    category: 'About' },
            { title: 'Culturally sensitive care',   url: '/about',          category: 'About' },
            { title: 'Crisis support available',    url: '/about',          category: 'About' },
            { title: 'Individual Counseling',       url: '/services',       category: 'Services' },
            { title: 'Relationship Therapy',        url: '/services',       category: 'Services' },
            { title: 'Grief and Transitions',       url: '/services',       category: 'Services' },
            { title: 'Personal Growth',             url: '/services',       category: 'Services' },
            { title: 'Anxiety, stress, depression support', url: '/services', category: 'Services' },
            { title: 'Couples and family therapy',  url: '/services',       category: 'Services' },
            { title: 'CBT and mindfulness',         url: '/services',       category: 'Services' },
            { title: 'Strength-based counseling',   url: '/services',       category: 'Services' },
            { title: 'Book a session',              url: '/#contact',       category: 'Services' },
            { title: 'Books by Dr. Isaac Frimpong', url: '/books',          category: 'Books' },
            { title: 'Buy a Book',                  url: '/books',          category: 'Books' },
            { title: 'Books and resources — coming soon', url: '/books',    category: 'Books' },
            { title: 'Phone 0027 73091 8737',       url: '/#contact',       category: 'Contact' },
            { title: 'Email frimpongisaac331@gmail.com', url: '/#contact',   category: 'Contact' },
            { title: 'KwaZulu-Natal, South Africa', url: '/#contact',       category: 'Contact' },
            { title: 'Hours Mon–Sat 8am–8pm',       url: '/#contact',       category: 'Contact' }
        ];

        function buildSnippet(text, query) {
            const lower = text.toLowerCase();
            const idx = lower.indexOf(query.toLowerCase());
            if (idx === -1) return text;
            const start = Math.max(0, idx - 25);
            const end = Math.min(text.length, idx + query.length + 40);
            let snip = (start > 0 ? '…' : '') +
                       text.substring(start, end) +
                       (end < text.length ? '…' : '');
            const re = new RegExp('(' + query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig');
            return snip.replace(re, '<strong>$1</strong>');
        }

        function renderResults(query) {
            searchResults.innerHTML = '';
            if (!query || query.length < 2) {
                searchResults.classList.remove('open');
                return;
            }

            const matches = siteIndex.filter(item =>
                item.title.toLowerCase().includes(query.toLowerCase()) ||
                item.category.toLowerCase().includes(query.toLowerCase())
            ).slice(0, 8);

            if (matches.length === 0) {
                searchResults.innerHTML = '<div class="search-empty">No matches found.</div>';
                searchResults.classList.add('open');
                return;
            }

            matches.forEach(item => {
                const row = document.createElement('button');
                row.type = 'button';
                row.className = 'search-result';
                row.innerHTML =
                    '<span class="sr-cat">' + item.category + '</span>' +
                    '<span class="sr-title">' + buildSnippet(item.title, query) + '</span>';
                row.addEventListener('click', () => goToResult(item.url));
                searchResults.appendChild(row);
            });

            searchResults.classList.add('open');
        }

        function goToResult(url) {
            if (url.startsWith('/#')) {
                const id = url.substring(2);
                const target = document.getElementById(id);
                if (target) {
                    const offset = 90;
                    const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
                    window.scrollTo({ top: top, behavior: 'smooth' });
                    searchResults.classList.remove('open');
                    return;
                }
            }
            window.location.href = url;
        }

        searchInput.addEventListener('input', (e) => {
            renderResults(e.target.value.trim());
        });

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const first = searchResults.querySelector('.search-result');
                if (first) first.click();
            }
        });

        if (searchGo) {
            searchGo.addEventListener('click', () => {
                const first = searchResults.querySelector('.search-result');
                if (first) first.click();
                else renderResults(searchInput.value.trim());
            });
        }

        document.addEventListener('click', (e) => {
            if (!e.target.closest('#searchWrap')) {
                searchResults.classList.remove('open');
            }
        });
    }


    /* =========================================================
       LIVELY EMOJI STRIP
       ========================================================= */

    const emojiStrip = document.getElementById('emojiStrip');

    if (emojiStrip) {
        const emojis = emojiStrip.querySelectorAll('.emoji');

        emojis.forEach(el => {
            el.style.cursor = 'pointer';

            el.addEventListener('click', () => {
                el.classList.remove('pop');
                void el.offsetWidth;
                el.classList.add('pop');

                const swapTo = el.getAttribute('data-swap');
                if (swapTo) {
                    const original = el.textContent;
                    el.textContent = swapTo;
                    el.setAttribute('data-swap', original);
                }

                spawnParticles(el);
            });
        });

        function spawnParticles(sourceEl) {
            const rect = sourceEl.getBoundingClientRect();
            const chars = ['✨', '💫', '⭐', '🌟'];
            for (let i = 0; i < 4; i++) {
                const p = document.createElement('span');
                p.className = 'emoji-particle';
                p.textContent = chars[Math.floor(Math.random() * chars.length)];
                p.style.left = (rect.left + rect.width / 2) + 'px';
                p.style.top = (rect.top + rect.height / 2) + 'px';
                p.style.setProperty('--dx', (Math.random() * 80 - 40) + 'px');
                p.style.setProperty('--dy', (-Math.random() * 70 - 30) + 'px');
                document.body.appendChild(p);
                setTimeout(() => p.remove(), 1200);
            }
        }
    }

});