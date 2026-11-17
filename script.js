// Crescent site script — shared by index.html and docs.html.
// Everything here is progressive enhancement: the page is complete without it.
(function () {
    'use strict';

    var root = document.documentElement;
    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var hasIO = 'IntersectionObserver' in window;

    function sleep(ms) {
        return new Promise(function (resolve) { setTimeout(resolve, ms); });
    }

    // ---------------------------------------------------------------------
    // Navbar: solid background once the page has scrolled
    // ---------------------------------------------------------------------
    function initNavbar() {
        var navbar = document.querySelector('.navbar');
        if (!navbar) return;
        var ticking = false;
        function update() {
            navbar.classList.toggle('is-scrolled', window.scrollY > 24);
            ticking = false;
        }
        window.addEventListener('scroll', function () {
            if (!ticking) {
                ticking = true;
                window.requestAnimationFrame(update);
            }
        }, { passive: true });
        update();
    }

    // ---------------------------------------------------------------------
    // Reveal on scroll (opacity/transform only, never hides content without JS)
    // ---------------------------------------------------------------------
    function initReveal() {
        var items = document.querySelectorAll('.reveal');
        if (!items.length) return;
        if (reduceMotion || !hasIO) {
            items.forEach(function (el) { el.classList.add('is-visible'); });
            return;
        }

        // Gentle stagger inside grids (features)
        document.querySelectorAll('.feature-grid').forEach(function (grid) {
            Array.prototype.forEach.call(grid.children, function (el, i) {
                el.style.setProperty('--reveal-delay', ((i % 3) * 0.12) + 's');
            });
        });

        // Anything already on screen at load is shown at once (no flash)
        var vh = window.innerHeight;
        items.forEach(function (el) {
            var r = el.getBoundingClientRect();
            if (r.top < vh && r.bottom > 0) el.classList.add('is-visible');
        });

        root.classList.add('reveal-ready');

        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

        items.forEach(function (el) {
            if (!el.classList.contains('is-visible')) io.observe(el);
        });
    }

    // ---------------------------------------------------------------------
    // Starfield: a light canvas, ~30 fps, paused off-screen / in background tabs.
    // Under reduced motion it paints a single still frame.
    // ---------------------------------------------------------------------
    function initStarfield() {
        var canvas = document.querySelector('canvas.starfield');
        if (!canvas || !canvas.getContext) return;
        var ctx = canvas.getContext('2d');
        if (!ctx) return;
        var hero = canvas.closest('.hero');

        // Stars live in normalised coordinates so resizing never reshuffles them.
        var MAX = 460;
        var stars = [];
        var seed = 7;
        function rand() { // small deterministic PRNG: same sky on every visit
            seed = (seed * 16807) % 2147483647;
            return (seed - 1) / 2147483646;
        }
        for (var i = 0; i < MAX; i++) {
            var depth = Math.pow(rand(), 2.2); // most stars are far away
            stars.push({
                x: rand(),
                y: Math.pow(rand(), 1.15), // a little denser towards the top
                depth: depth,
                r: 0.35 + depth * 1.05,
                a: 0.25 + rand() * 0.55 + depth * 0.2,
                phase: rand() * Math.PI * 2,
                speed: 0.0004 + rand() * 0.0011
            });
        }

        var w = 0, h = 0, count = 0, dpr = 1, last = 0;
        function resize() {
            dpr = Math.min(window.devicePixelRatio || 1, 2);
            w = canvas.clientWidth;
            h = canvas.clientHeight;
            if (!w || !h) return;
            canvas.width = Math.round(w * dpr);
            canvas.height = Math.round(h * dpr);
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            count = Math.min(MAX, Math.round((w * h) / 3200));
        }

        var DRIFT = 0.0045; // px per ms for the nearest stars: a slow pan
        function draw(t) {
            ctx.clearRect(0, 0, w, h);
            for (var i = 0; i < count; i++) {
                var s = stars[i];
                var x = (s.x * w - t * DRIFT * (0.15 + s.depth)) % w;
                if (x < 0) x += w;
                var y = s.y * h;
                var tw = reduceMotion ? 1 : 0.72 + 0.28 * Math.sin(s.phase + t * s.speed);
                var alpha = Math.min(1, s.a * tw);
                ctx.fillStyle = 'rgba(226, 236, 255,' + alpha.toFixed(3) + ')';
                if (s.r < 0.9) {
                    ctx.fillRect(x, y, s.r * 1.4, s.r * 1.4);
                } else {
                    ctx.beginPath();
                    ctx.arc(x, y, s.r, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
        }

        resize();
        draw(0);
        if (hero) hero.classList.add('has-starfield');

        var resizeTimer;
        window.addEventListener('resize', function () {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function () {
                resize();
                draw(last);
            }, 120);
        });

        if (reduceMotion) return;

        var running = false, visible = true, prev = 0, start = null;
        function frame(now) {
            if (!running) return;
            if (start === null) start = now - last;
            if (now - prev >= 32) { // ~30 fps is plenty for a slow drift
                last = now - start;
                draw(last);
                prev = now;
            }
            window.requestAnimationFrame(frame);
        }
        function setRunning(on) {
            if (on === running) return;
            running = on;
            if (on) {
                start = null;
                window.requestAnimationFrame(frame);
            }
        }
        function sync() { setRunning(visible && !document.hidden); }

        if (hasIO && hero) {
            new IntersectionObserver(function (entries) {
                visible = entries[0].isIntersecting;
                sync();
            }).observe(hero);
        }
        document.addEventListener('visibilitychange', sync);
        sync();
    }

    // ---------------------------------------------------------------------
    // Terminal: types the session once when it scrolls into view.
    // Lines keep their space while hidden and typing is a clip, so nothing moves.
    // ---------------------------------------------------------------------
    function initTerminal() {
        var fig = document.querySelector('[data-terminal]');
        if (!fig || reduceMotion || !hasIO) return;
        var lines = Array.prototype.slice.call(fig.querySelectorAll('.t-line'));
        if (!lines.length) return;

        fig.classList.add('is-armed');
        lines.forEach(function (line) {
            line.classList.add('t-pending');
            var typed = line.querySelector('.t-typed');
            if (typed) {
                typed.classList.add('is-typing');
                typed.style.setProperty('--typed', '0');
            }
        });

        async function play() {
            for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                var typed = line.querySelector('.t-typed');
                var isOut = line.classList.contains('t-out');
                var isNote = line.classList.contains('t-note');

                if (isOut) await sleep(260);
                else if (isNote) await sleep(220);
                line.classList.remove('t-pending');

                if (typed) {
                    await sleep(260);
                    var n = typed.textContent.length;
                    for (var c = 1; c <= n; c++) {
                        typed.style.setProperty('--typed', String(c));
                        await sleep(14 + Math.random() * 30);
                    }
                    typed.classList.remove('is-typing');
                    typed.style.removeProperty('--typed');
                    await sleep(/docker compose/.test(typed.textContent) ? 900 : 320);
                }
            }
            fig.classList.add('is-done');
        }

        var io = new IntersectionObserver(function (entries) {
            if (entries[0].isIntersecting) {
                io.disconnect();
                play();
            }
        }, { threshold: 0.45 });
        io.observe(fig);
    }

    // ---------------------------------------------------------------------
    // Code tabs (WAI-ARIA tabs pattern). Without JS every file is listed.
    // ---------------------------------------------------------------------
    function initTabs() {
        document.querySelectorAll('[data-tabs]').forEach(function (win) {
            var list = win.querySelector('[role="tablist"]');
            var tabs = Array.prototype.slice.call(win.querySelectorAll('[role="tab"]'));
            var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute('aria-controls')); });
            if (!list || !tabs.length || panels.some(function (p) { return !p; })) return;

            function select(index, focus) {
                tabs.forEach(function (tab, j) {
                    var on = j === index;
                    tab.setAttribute('aria-selected', on ? 'true' : 'false');
                    tab.tabIndex = on ? 0 : -1;
                    panels[j].classList.toggle('is-inactive', !on);
                });
                if (focus) tabs[index].focus();
            }

            tabs.forEach(function (tab, i) {
                tab.addEventListener('click', function () { select(i, false); });
                tab.addEventListener('keydown', function (e) {
                    var next = null;
                    if (e.key === 'ArrowRight') next = (i + 1) % tabs.length;
                    else if (e.key === 'ArrowLeft') next = (i - 1 + tabs.length) % tabs.length;
                    else if (e.key === 'Home') next = 0;
                    else if (e.key === 'End') next = tabs.length - 1;
                    if (next !== null) {
                        e.preventDefault();
                        select(next, true);
                    }
                });
            });
            panels.forEach(function (p, j) {
                p.setAttribute('role', 'tabpanel');
                p.setAttribute('aria-labelledby', tabs[j].id);
                p.tabIndex = 0;
            });

            list.hidden = false;
            win.classList.add('has-tabs');
            select(0, false);
        });
    }

    // ---------------------------------------------------------------------
    // Copy buttons on code blocks (home + docs)
    // ---------------------------------------------------------------------
    function initCopy() {
        if (!navigator.clipboard || !navigator.clipboard.writeText) return;
        document.querySelectorAll('.code-block').forEach(function (block) {
            var code = block.querySelector('code') || block.querySelector('pre');
            if (!code || block.querySelector('.copy-btn')) return;
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'copy-btn';
            btn.textContent = 'Copiar';
            btn.setAttribute('aria-label', 'Copiar código');
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                navigator.clipboard.writeText(code.textContent).then(function () {
                    btn.textContent = 'Copiado';
                    btn.classList.add('is-done');
                    setTimeout(function () {
                        btn.textContent = 'Copiar';
                        btn.classList.remove('is-done');
                    }, 1800);
                }, function () {
                    btn.textContent = 'Falhou';
                    setTimeout(function () { btn.textContent = 'Copiar'; }, 1800);
                });
            });
            block.appendChild(btn);
        });
    }

    function init() {
        initNavbar();
        initReveal();
        initStarfield();
        initTerminal();
        initTabs();
        initCopy();
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
