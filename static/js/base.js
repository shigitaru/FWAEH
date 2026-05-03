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
        function closeAll(except) {
            document.querySelectorAll(".custom-select.is-open").forEach(function (root) {
                if (root !== except) {
                    root.classList.remove("is-open");
                    var btn = root.querySelector(".custom-select-btn");
                    if (btn) btn.setAttribute("aria-expanded", "false");
                }
            });
        }
        function enhanceSelect(select) {
            if (!select || select.dataset.customSelectReady === "1" || select.multiple) return;
            select.dataset.customSelectReady = "1";
            select.classList.add("native-select-hidden");
            var root = document.createElement("div");
            root.className = "custom-select";
            var btn = document.createElement("button");
            btn.type = "button";
            btn.className = "custom-select-btn";
            btn.setAttribute("aria-haspopup", "listbox");
            btn.setAttribute("aria-expanded", "false");
            var label = document.createElement("span");
            label.className = "custom-select-label";
            var icon = document.createElement("span");
            icon.className = "custom-select-icon";
            icon.setAttribute("aria-hidden", "true");
            btn.appendChild(label);
            btn.appendChild(icon);
            var list = document.createElement("div");
            list.className = "custom-select-list";
            list.setAttribute("role", "listbox");
            Array.prototype.forEach.call(select.options, function (opt) {
                var item = document.createElement("button");
                item.type = "button";
                item.className = "custom-select-option";
                item.setAttribute("role", "option");
                item.dataset.value = opt.value;
                item.textContent = opt.textContent;
                item.disabled = opt.disabled;
                item.addEventListener("click", function () {
                    select.value = opt.value;
                    select.dispatchEvent(new Event("change", { bubbles: true }));
                    root.classList.remove("is-open");
                    btn.setAttribute("aria-expanded", "false");
                    sync();
                    btn.focus();
                });
                list.appendChild(item);
            });
            function sync() {
                var selected = select.options[select.selectedIndex];
                label.textContent = selected ? selected.textContent : "";
                Array.prototype.forEach.call(list.children, function (item) {
                    var active = selected && item.dataset.value === selected.value;
                    item.classList.toggle("is-selected", !!active);
                    item.setAttribute("aria-selected", active ? "true" : "false");
                });
            }
            select.parentNode.insertBefore(root, select.nextSibling);
            root.appendChild(btn);
            root.appendChild(list);
            sync();
            select.addEventListener("change", sync);
            btn.addEventListener("click", function () {
                var open = root.classList.contains("is-open");
                closeAll(root);
                root.classList.toggle("is-open", !open);
                btn.setAttribute("aria-expanded", open ? "false" : "true");
            });
            btn.addEventListener("keydown", function (e) {
                if (e.key === "Escape") {
                    root.classList.remove("is-open");
                    btn.setAttribute("aria-expanded", "false");
                }
            });
        }
        function initCustomSelects() {
            document.querySelectorAll("select").forEach(enhanceSelect);
        }
        document.addEventListener("click", function (e) {
            if (!e.target.closest(".custom-select")) closeAll(null);
        });
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") closeAll(null);
        });
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", initCustomSelects);
        } else {
            initCustomSelects();
        }
    })();

    (function () {
        var input = document.querySelector("[data-search-suggest]");
        var box = document.querySelector("[data-search-suggestions]");
        if (!input || !box || !window.fetch) return;
        var timer = 0;
        function hide() {
            box.hidden = true;
            box.innerHTML = "";
        }
        function render(items) {
            if (!items || !items.length) {
                hide();
                return;
            }
            box.innerHTML = "";
            items.forEach(function (item) {
                var a = document.createElement("a");
                a.href = item.url || "#";
                a.className = "search-suggestion-item";
                var label = document.createElement("span");
                label.textContent = item.label || "";
                var meta = document.createElement("small");
                meta.textContent = item.meta || item.type || "";
                a.appendChild(label);
                a.appendChild(meta);
                box.appendChild(a);
            });
            box.hidden = false;
        }
        input.addEventListener("input", function () {
            var q = input.value.trim();
            if (timer) clearTimeout(timer);
            if (q.length < 2) {
                hide();
                return;
            }
            timer = setTimeout(function () {
                fetch("/api/search-suggestions?q=" + encodeURIComponent(q), { headers: { Accept: "application/json" } })
                    .then(function (r) { return r.ok ? r.json() : null; })
                    .then(function (data) { render(data && data.ok ? data.suggestions : []); })
                    .catch(hide);
            }, 160);
        });
        document.addEventListener("click", function (e) {
            if (!e.target.closest(".search-form")) hide();
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
        var split = document.getElementById("pa-drawer-split");
        var flyout = document.getElementById("pa-drawer-flyout");
        var drawerPanel = document.getElementById("pa-nav-drawer");
        if (!root || !openBtn) return;
        var nav = root.querySelector(".pa-drawer-nav");
        var fineHover = window.matchMedia("(hover: hover) and (pointer: fine)");
        var peekTeaseId = null;
        var peekLeaveTimer = null;

        function cancelPeekLeave() {
            if (peekLeaveTimer != null) {
                clearTimeout(peekLeaveTimer);
                peekLeaveTimer = null;
            }
        }

        function peekLeaveShouldHold() {
            if (flyout && flyout.matches(":hover")) return true;
            if (root.querySelector(".pa-nav-tease:hover")) return true;
            var ax = document.activeElement;
            if (ax && flyout && flyout.contains(ax)) return true;
            if (ax && typeof ax.closest === "function" && ax.closest(".pa-nav-tease")) return true;
            return false;
        }

        function schedulePeekClear() {
            if (!fineHover.matches) return;
            cancelPeekLeave();
            peekLeaveTimer = window.setTimeout(function () {
                peekLeaveTimer = null;
                if (peekLeaveShouldHold()) return;
                peekTeaseId = null;
                syncFlyoutState();
            }, 220);
        }

        /** Активная карточка: тач — только по стрелке (.is-expanded); десктоп — наведение на строку (peek) или тот же .is-expanded */
        function syncFlyoutState() {
            if (!split) return;
            var expanded = root.querySelector(".pa-nav-tease.is-expanded");
            var idExpanded = expanded && expanded.getAttribute("data-tease-id");
            var id = fineHover.matches ? peekTeaseId || idExpanded : idExpanded;
            if (id) {
                split.setAttribute("data-active-tease", id);
                if (flyout) flyout.setAttribute("aria-hidden", "false");
                if (drawerPanel) drawerPanel.classList.add("pa-drawer-panel--tease-open");
            } else {
                split.removeAttribute("data-active-tease");
                if (flyout) flyout.setAttribute("aria-hidden", "true");
                if (drawerPanel) drawerPanel.classList.remove("pa-drawer-panel--tease-open");
            }
        }

        function collapseAllTeases() {
            peekTeaseId = null;
            cancelPeekLeave();
            document.querySelectorAll(".pa-nav-tease.is-expanded").forEach(function (tease) {
                tease.classList.remove("is-expanded");
                var tb = tease.querySelector(".pa-nav-tease-toggle");
                if (tb) tb.setAttribute("aria-expanded", "false");
            });
            syncFlyoutState();
        }

        function setOpen(on) {
            root.classList.toggle("is-open", on);
            root.setAttribute("aria-hidden", on ? "false" : "true");
            openBtn.setAttribute("aria-expanded", on ? "true" : "false");
            document.documentElement.classList.toggle("pa-drawer-open", on);
            document.body.style.overflow = on ? "hidden" : "";
            if (!on) {
                collapseAllTeases();
            }
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
            if (e.key !== "Escape" || !root.classList.contains("is-open")) return;
            if (split && split.getAttribute("data-active-tease")) {
                collapseAllTeases();
                e.preventDefault();
                return;
            }
            setOpen(false);
        });

        document.querySelectorAll(".pa-nav-tease-toggle").forEach(function (btn) {
            btn.addEventListener("click", function (e) {
                e.preventDefault();
                e.stopPropagation();
                var wrap = btn.closest(".pa-nav-tease");
                if (!wrap) return;
                var next = !wrap.classList.contains("is-expanded");
                document.querySelectorAll(".pa-nav-tease.is-expanded").forEach(function (o) {
                    if (o !== wrap) {
                        o.classList.remove("is-expanded");
                        var t = o.querySelector(".pa-nav-tease-toggle");
                        if (t) t.setAttribute("aria-expanded", "false");
                    }
                });
                wrap.classList.toggle("is-expanded", next);
                btn.setAttribute("aria-expanded", next ? "true" : "false");
                syncFlyoutState();
            });
        });

        root.querySelectorAll(".pa-nav-tease").forEach(function (tease) {
            tease.addEventListener("mouseenter", function () {
                if (!fineHover.matches) return;
                peekTeaseId = tease.getAttribute("data-tease-id");
                cancelPeekLeave();
                syncFlyoutState();
            });
            tease.addEventListener("mouseleave", function () {
                if (!fineHover.matches) return;
                schedulePeekClear();
            });
            tease.addEventListener("focusin", function () {
                if (!fineHover.matches) return;
                peekTeaseId = tease.getAttribute("data-tease-id");
                cancelPeekLeave();
                syncFlyoutState();
            });
            tease.addEventListener("focusout", function (e) {
                if (!fineHover.matches) return;
                var r = e.relatedTarget;
                if (r && (tease.contains(r) || (flyout && flyout.contains(r)))) return;
                schedulePeekClear();
            });
        });
        if (flyout) {
            flyout.addEventListener("click", function (e) {
                var al = e.target.closest("a");
                if (al) setOpen(false);
            });
            flyout.addEventListener("mouseenter", function () {
                cancelPeekLeave();
            });
            flyout.addEventListener("mouseleave", function () {
                if (!fineHover.matches) return;
                schedulePeekClear();
            });
            flyout.addEventListener("focusout", function (e) {
                if (!fineHover.matches) return;
                var r = e.relatedTarget;
                if (r && flyout.contains(r)) return;
                if (r && typeof r.closest === "function" && r.closest(".pa-nav-tease")) return;
                schedulePeekClear();
            });
        }
        try {
            if (typeof fineHover.addEventListener === "function") {
                fineHover.addEventListener("change", function () {
                    peekTeaseId = null;
                    cancelPeekLeave();
                    syncFlyoutState();
                });
            }
        } catch (eM) {}
    })();

    (function () {
        var root = document.getElementById("pa-measure-drawer");
        if (!root) return;
        var panelBody = document.getElementById("pa-measure-drawer-body");
        var productEl = document.getElementById("pa-measure-drawer-product");
        var i18n = {};
        try {
            var ij = document.getElementById("pa-measure-i18n");
            if (ij && ij.textContent) i18n = JSON.parse(ij.textContent);
        } catch (e1) {
            i18n = {};
        }
        var lang = (i18n.lang || "en").toLowerCase();

        function setOpen(on) {
            root.classList.toggle("is-open", !!on);
            root.setAttribute("aria-hidden", on ? "false" : "true");
            document.documentElement.classList.toggle("pa-measure-open", !!on);
        }

        function cellText(v) {
            if (v === null || v === undefined || v === "") return "—";
            return String(v);
        }

        function renderGarment(m) {
            var kick = document.createElement("p");
            kick.className = "pa-measure-kicker";
            kick.textContent = i18n.garmentKicker || "";
            var wrap = document.createElement("div");
            wrap.className = "pa-measure-table-wrap";
            var table = document.createElement("table");
            table.className = "pa-measure-table";
            var thead = document.createElement("thead");
            var trh = document.createElement("tr");
            var th0 = document.createElement("th");
            th0.textContent = "";
            trh.appendChild(th0);
            (m.columns || []).forEach(function (c) {
                var th = document.createElement("th");
                th.textContent = c;
                trh.appendChild(th);
            });
            thead.appendChild(trh);
            table.appendChild(thead);
            var tbody = document.createElement("tbody");
            (m.rows || []).forEach(function (row) {
                var tr = document.createElement("tr");
                var td0 = document.createElement("td");
                td0.textContent = lang === "ru" ? (row.ru || row.en || "") : (row.en || row.ru || "");
                tr.appendChild(td0);
                (row.values || []).forEach(function (v) {
                    var td = document.createElement("td");
                    td.textContent = cellText(v);
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            wrap.appendChild(table);
            panelBody.appendChild(kick);
            panelBody.appendChild(wrap);
        }

        function renderFootwear(m) {
            var kick = document.createElement("p");
            kick.className = "pa-measure-kicker";
            kick.textContent = i18n.footwearKicker || "";
            var wrap = document.createElement("div");
            wrap.className = "pa-measure-table-wrap";
            var table = document.createElement("table");
            table.className = "pa-measure-table";
            var thead = document.createElement("thead");
            var trh = document.createElement("tr");
            var th1 = document.createElement("th");
            th1.textContent = i18n.colEu || "EU";
            var th2 = document.createElement("th");
            th2.textContent = i18n.colInsole || "";
            trh.appendChild(th1);
            trh.appendChild(th2);
            thead.appendChild(trh);
            table.appendChild(thead);
            var tbody = document.createElement("tbody");
            (m.rows || []).forEach(function (row) {
                var tr = document.createElement("tr");
                var td1 = document.createElement("td");
                td1.textContent = cellText(row.eu);
                var td2 = document.createElement("td");
                td2.textContent = cellText(row.insole_cm);
                tr.appendChild(td1);
                tr.appendChild(td2);
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);
            wrap.appendChild(table);
            panelBody.appendChild(kick);
            panelBody.appendChild(wrap);
        }

        function openMeasure(name, data) {
            if (!panelBody || !productEl) return;
            panelBody.innerHTML = "";
            productEl.textContent = name || "";
            if (!data || typeof data !== "object") return;
            if (data.kind === "footwear") renderFootwear(data);
            else if (data.kind === "garment") renderGarment(data);
            setOpen(true);
        }

        document.addEventListener("click", function (e) {
            var btn = e.target.closest("[data-pa-measure-open]");
            if (!btn) return;
            e.preventDefault();
            var name = btn.getAttribute("data-product-name") || "";
            var raw = btn.getAttribute("data-measurements");
            var data = null;
            try {
                data = raw ? JSON.parse(raw) : null;
            } catch (e2) {
                data = null;
            }
            if (!data) return;
            openMeasure(name, data);
        });

        root.addEventListener("click", function (e) {
            if (e.target.closest("[data-pa-measure-close]")) setOpen(false);
        });
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && root.classList.contains("is-open")) setOpen(false);
        });
    })();
})();
