// Navbar menu — shared by index.html and docs.html (called from onclick="menuOnClick()").
function menuSetOpen(open) {
    var bar = document.getElementById("menu-bar");
    var nav = document.getElementById("nav");
    var bg = document.getElementById("menu-bg");
    if (!bar || !nav) return;
    bar.classList.toggle("change", open);
    nav.classList.toggle("change", open);
    if (bg) bg.classList.toggle("change-bg", open);
    bar.setAttribute("aria-expanded", open ? "true" : "false");
    bar.setAttribute("aria-label", open ? "Fechar menu" : "Abrir menu");
    var navbar = bar.closest(".navbar");
    if (navbar) navbar.classList.toggle("is-open", open);
}

function menuOnClick() {
    var nav = document.getElementById("nav");
    menuSetOpen(!(nav && nav.classList.contains("change")));
}

(function () {
    function init() {
        var bar = document.getElementById("menu-bar");
        var nav = document.getElementById("nav");
        var bg = document.getElementById("menu-bg");
        if (!bar || !nav) return;

        // docs-template.html predates these attributes; add them here.
        if (!bar.hasAttribute("role")) bar.setAttribute("role", "button");
        if (!bar.hasAttribute("tabindex")) bar.setAttribute("tabindex", "0");
        if (!bar.hasAttribute("aria-controls")) bar.setAttribute("aria-controls", "nav");
        if (!bar.hasAttribute("aria-expanded")) bar.setAttribute("aria-expanded", "false");
        if (!bar.hasAttribute("aria-label")) bar.setAttribute("aria-label", "Abrir menu");

        bar.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                menuOnClick();
            }
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && nav.classList.contains("change")) {
                menuSetOpen(false);
                bar.focus();
            }
        });

        nav.addEventListener("click", function (e) {
            if (e.target.closest("a")) menuSetOpen(false);
        });

        if (bg) bg.addEventListener("click", function () { menuSetOpen(false); });

        // Leaving the mobile layout closes the panel.
        if (window.matchMedia) {
            var mq = window.matchMedia("(min-width: 901px)");
            var onChange = function () { if (mq.matches) menuSetOpen(false); };
            if (mq.addEventListener) mq.addEventListener("change", onChange);
            else if (mq.addListener) mq.addListener(onChange);
        }
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
})();
