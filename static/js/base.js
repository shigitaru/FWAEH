(function () {
    function formatClock(n, mode) {
        var hh = String(n.getHours()).padStart(2, "0");
        var mm = String(n.getMinutes()).padStart(2, "0");
        var ss = String(n.getSeconds()).padStart(2, "0");
        var ms = String(n.getMilliseconds()).padStart(3, "0");
        if (mode === "short") return hh + ":" + mm;
        if (mode === "medium") return hh + ":" + mm + ":" + ss;
        return hh + ":" + mm + ":" + ss + "." + ms;
    }

    var paClockLastSlow = 0;
    function updateClock() {
        if (document.hidden) return;
        var n = new Date();
        var now = n.getTime();
        if (document.documentElement.classList.contains("refine-open")) {
            if (now - paClockLastSlow < 500) return;
            paClockLastSlow = now;
        } else {
            paClockLastSlow = 0;
        }
        var header = document.getElementById("live-clock");
        if (header) header.textContent = formatClock(n, "full");
        document.querySelectorAll("[data-live-clock]").forEach(function (el) {
            var mode = el.getAttribute("data-live-clock") || "medium";
            el.textContent = formatClock(n, mode);
        });
    }

    setInterval(updateClock, 37);
    updateClock();

    (function initThemeToggle() {
        var t = document.getElementById("theme-toggle");
        var root = document.documentElement;
        var s = null;
        try {
            s = localStorage.getItem("theme");
        } catch (e) {}
        if (s === "dark") {
            root.setAttribute("data-theme", "dark");
            if (t) t.textContent = "\u263E";
        }
        if (t)
            t.addEventListener("click", function () {
                var dark = root.getAttribute("data-theme") === "dark";
                if (dark) {
                    root.removeAttribute("data-theme");
                    try {
                        localStorage.setItem("theme", "light");
                    } catch (e) {}
                    t.textContent = "\u2600";
                } else {
                    root.setAttribute("data-theme", "dark");
                    try {
                        localStorage.setItem("theme", "dark");
                    } catch (e) {}
                    t.textContent = "\u263E";
                }
            });
    })();

    window.addEventListener("pagehide", function () {
        document.documentElement.style.overflow = "";
        document.body.style.overflow = "";
    });

    (function () {
        function paWidth() {
            var w = document.documentElement.clientWidth || window.innerWidth || 0;
            if (w <= 0 && window.visualViewport) w = Math.round(window.visualViewport.width) || 0;
            return w;
        }
        function syncPaLayout() {
            var w = paWidth();
            var root = document.documentElement;
            if (w <= 0) return;
            root.classList.add("pa-js-layout");
            root.classList.toggle("pa-wide-store", w >= 1024);
            root.classList.toggle("pa-store-1col", w <= 768);
            root.classList.toggle("pa-compact-header", w <= 1100);
            root.classList.toggle("pa-tiny-header", w <= 420);
            if (w <= 420) root.style.setProperty("--site-header-offset", "138px");
            else if (w <= 1100) root.style.setProperty("--site-header-offset", "132px");
            else root.style.removeProperty("--site-header-offset");
        }
        var paLayoutRoRaf = 0;
        function syncPaLayoutFromRo() {
            if (paLayoutRoRaf) return;
            paLayoutRoRaf = requestAnimationFrame(function () {
                paLayoutRoRaf = 0;
                syncPaLayout();
            });
        }
        function armResizeObserver() {
            if (!window.ResizeObserver || !document.body) return;
            try {
                var ro = new ResizeObserver(syncPaLayoutFromRo);
                ro.observe(document.body);
            } catch (e) {}
        }
        window.addEventListener("resize", syncPaLayout, { passive: true });
        if (window.visualViewport) {
            window.visualViewport.addEventListener("resize", syncPaLayout, { passive: true });
        }
        window.addEventListener("pageshow", function (e) {
            if (e.persisted) {
                document.documentElement.style.overflow = "";
                document.body.style.overflow = "";
            }
            syncPaLayout();
        });
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", function () {
                syncPaLayout();
                armResizeObserver();
            });
        } else {
            syncPaLayout();
            armResizeObserver();
        }
        window.addEventListener("load", syncPaLayout);
        [0, 32, 100, 300, 750].forEach(function (ms) {
            setTimeout(syncPaLayout, ms);
        });
    })();

    (function () {
        var root = document.documentElement;
        var TH_ON = 56;
        var TH_OFF = 28;
        var HERO_BAR_ON = 72;
        var HERO_BAR_OFF = 36;
        var raf = 0;
        function y() {
            return window.scrollY || root.scrollTop || 0;
        }
        function tick() {
            raf = 0;
            var scrollY = y();
            var compact = root.classList.contains("pa-brand-scroll");
            if (compact) {
                if (scrollY <= TH_OFF) root.classList.remove("pa-brand-scroll");
            } else if (scrollY >= TH_ON) {
                root.classList.add("pa-brand-scroll");
            }
            var hero = root.classList.contains("pa-hero-home");
            var lux = root.classList.contains("pa-lux-site");
            var barSolid = root.classList.contains("pa-header-solid");
            if (hero || lux) {
                if (barSolid) {
                    if (scrollY <= HERO_BAR_OFF) root.classList.remove("pa-header-solid");
                } else if (scrollY >= HERO_BAR_ON) {
                    root.classList.add("pa-header-solid");
                }
            } else if (barSolid) {
                root.classList.remove("pa-header-solid");
            }
        }
        function onScroll() {
            if (!raf) raf = requestAnimationFrame(tick);
        }
        window.addEventListener("scroll", onScroll, { passive: true });
        tick();
        window.addEventListener("pageshow", function () {
            tick();
        });
    })();

    (function () {
        var i18nEl = document.getElementById("pa-cart-toast-i18n");
        try {
            if (i18nEl) window.paCartToastI18n = JSON.parse(i18nEl.textContent);
        } catch (e) {}
        function paBindCartToastDismissal(el) {
            if (!el) return;
            var hideTimer;
            function close() {
                if (hideTimer) clearTimeout(hideTimer);
                el.classList.add("cart-added-toast--hide");
                setTimeout(function () {
                    if (el.parentNode) el.parentNode.removeChild(el);
                }, 320);
            }
            var btn = el.querySelector(".cart-added-toast-close");
            if (btn) btn.addEventListener("click", close);
            hideTimer = setTimeout(close, 5200);
        }
        document.querySelectorAll("[data-cart-toast]").forEach(function (el) {
            paBindCartToastDismissal(el);
        });
        window.paSetCartCount = function (n) {
            var c = document.getElementById("header-cart-count");
            if (c) c.textContent = String(n);
        };
        window.paSetWishlistCount = function (n) {
            var w = document.getElementById("header-wish-count");
            if (w) w.textContent = String(n);
        };
        window.paShowCartToast = function (productName) {
            var i18n = window.paCartToastI18n;
            if (!i18n) return;
            document.querySelectorAll("[data-cart-toast]").forEach(function (n) {
                n.remove();
            });
            var wrap = document.createElement("div");
            wrap.className = "cart-added-toast";
            wrap.setAttribute("role", "status");
            wrap.setAttribute("aria-live", "polite");
            wrap.setAttribute("data-cart-toast", "");
            var inner = document.createElement("div");
            inner.className = "cart-added-toast-inner";
            var icon = document.createElement("span");
            icon.className = "cart-added-toast-icon";
            icon.setAttribute("aria-hidden", "true");
            icon.textContent = "\u2713";
            var text = document.createElement("div");
            text.className = "cart-added-toast-text";
            var title = document.createElement("span");
            title.className = "cart-added-toast-title";
            title.textContent = i18n.title;
            var nameEl = document.createElement("span");
            nameEl.className = "cart-added-toast-name";
            nameEl.textContent = productName || "";
            text.appendChild(title);
            text.appendChild(nameEl);
            var link = document.createElement("a");
            link.href = i18n.cartHref;
            link.className = "cart-added-toast-link";
            link.textContent = i18n.viewBag;
            var btn = document.createElement("button");
            btn.type = "button";
            btn.className = "cart-added-toast-close";
            btn.setAttribute("aria-label", i18n.close);
            btn.textContent = "\u00D7";
            inner.appendChild(icon);
            inner.appendChild(text);
            inner.appendChild(link);
            inner.appendChild(btn);
            wrap.appendChild(inner);
            document.body.appendChild(wrap);
            paBindCartToastDismissal(wrap);
        };
    })();

    (function () {
        var cfgEl = document.getElementById("pa-wishlist-i18n");
        var cfg = null;
        try {
            if (cfgEl) cfg = JSON.parse(cfgEl.textContent);
        } catch (e) {}
        if (!cfg || !cfg.toggleUrl || !window.fetch) return;
        function setWishAria(btn, active) {
            btn.setAttribute("aria-pressed", active ? "true" : "false");
            btn.setAttribute("aria-label", active ? cfg.remove : cfg.add);
        }
        document.addEventListener("click", function (e) {
            var btn = e.target.closest(".wishlist-toggle");
            if (!btn) return;
            e.preventDefault();
            e.stopPropagation();
            var id = parseInt(btn.getAttribute("data-product-id"), 10);
            if (isNaN(id)) return;
            fetch(cfg.toggleUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({ product_id: id }),
            })
                .then(function (r) {
                    if (!r.ok) throw new Error("bad");
                    return r.json();
                })
                .then(function (data) {
                    if (!data || !data.ok) return;
                    btn.classList.toggle("is-active", data.in_wishlist);
                    setWishAria(btn, data.in_wishlist);
                    if (window.paSetWishlistCount) window.paSetWishlistCount(data.count);
                })
                .catch(function () {});
        });
    })();

    (function () {
        var root = document.getElementById("pa-drawer-root");
        var openBtn = document.getElementById("pa-menu-open");
        var closeBtn = document.getElementById("pa-menu-close");
        var backdrop = document.getElementById("pa-drawer-backdrop");
        if (!root || !openBtn) return;
        var nav = root.querySelector(".pa-drawer-nav");
        function setOpen(on) {
            root.classList.toggle("is-open", on);
            root.setAttribute("aria-hidden", on ? "false" : "true");
            openBtn.setAttribute("aria-expanded", on ? "true" : "false");
            document.documentElement.classList.toggle("pa-drawer-open", on);
            document.body.style.overflow = on ? "hidden" : "";
            if (on) {
                try {
                    closeBtn && closeBtn.focus();
                } catch (e) {}
            } else {
                try {
                    openBtn.focus();
                } catch (e) {}
            }
        }
        openBtn.addEventListener("click", function () {
            setOpen(true);
        });
        if (closeBtn) closeBtn.addEventListener("click", function () { setOpen(false); });
        if (backdrop) backdrop.addEventListener("click", function () { setOpen(false); });
        if (nav) {
            nav.addEventListener("click", function (e) {
                var a = e.target.closest("a");
                if (a) setOpen(false);
            });
        }
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && root.classList.contains("is-open")) {
                setOpen(false);
            }
        });
    })();
})();
