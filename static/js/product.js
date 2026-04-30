(function () {
    var cfgEl = document.getElementById("product-page-config");
    if (!cfgEl) return;

    var cfg = null;
    try {
        cfg = JSON.parse(cfgEl.textContent || "{}");
    } catch (e) {
        cfg = null;
    }
    if (!cfg) return;

    var p = Number(cfg.price_per_day || 0);
    var mx = Number(cfg.max_days || 1);
    var inp = document.getElementById("days-input");
    var total = document.getElementById("total-display");
    var btns = document.querySelectorAll(".step-btn");
    var startDateInp = document.getElementById("start-date-input");
    var availabilityText = document.getElementById("availability-text");
    var mainImg = document.getElementById("main-product-image");
    var thumbs = Array.prototype.slice.call(document.querySelectorAll(".product-thumb"));
    var thumbsRail = document.getElementById("product-thumbs-rail");
    var prevBtn = document.getElementById("gallery-prev");
    var nextBtn = document.getElementById("gallery-next");
    var images = thumbs.length ? thumbs.map(function (t) { return t.dataset.src; }) : [mainImg ? mainImg.src : ""];
    var currentIndex = 0;

    function clampDays(raw) {
        var d = parseInt(String(raw).trim(), 10);
        if (isNaN(d) || d < 1) d = 1;
        if (d > mx) d = mx;
        return d;
    }
    function setTotalForDays(d) {
        if (total) total.innerText = String(p * d);
    }
    function setAvailabilityState(available, startDate, endDate) {
        if (!availabilityText) return;
        var label = available ? cfg.available_text : cfg.unavailable_text;
        availabilityText.textContent = label + " (" + startDate + " - " + endDate + ")";
        availabilityText.classList.toggle("is-available", !!available);
        availabilityText.classList.toggle("is-unavailable", !available);
    }
    function refreshAvailability() {
        if (!startDateInp || !availabilityText || !window.fetch || !inp) return;
        var payload = { start_date: startDateInp.value, days: clampDays(inp.value) };
        fetch(cfg.availability_url, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            credentials: "same-origin",
            body: JSON.stringify(payload),
        })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (!data || !data.ok) return;
                setAvailabilityState(data.available, data.start_date, data.end_date);
            })
            .catch(function () {});
    }
    function setDays(v) {
        if (!inp) return;
        var d = clampDays(v);
        inp.value = d;
        setTotalForDays(d);
        refreshAvailability();
    }
    function onDaysInput() {
        if (!inp) return;
        var raw = inp.value;
        if (raw === "" || raw === "-") return;
        var d = parseInt(raw, 10);
        if (isNaN(d)) return;
        var c = Math.min(Math.max(d, 1), mx);
        setTotalForDays(c);
    }
    function normalizeDaysField() {
        if (!inp) return;
        var d = clampDays(inp.value);
        inp.value = d;
        setTotalForDays(d);
    }
    function setImage(index) {
        if (!images.length || !mainImg) return;
        if (index < 0) index = images.length - 1;
        if (index >= images.length) index = 0;
        currentIndex = index;
        mainImg.classList.add("is-fading");
        mainImg.src = images[currentIndex];
        thumbs.forEach(function (t) { t.classList.remove("active"); });
        if (thumbs[currentIndex]) {
            thumbs[currentIndex].classList.add("active");
            if (thumbsRail) {
                var thumbEl = thumbs[currentIndex];
                var railTop = thumbsRail.scrollTop;
                var railBottom = railTop + thumbsRail.clientHeight;
                var thumbTop = thumbEl.offsetTop;
                var thumbBottom = thumbTop + thumbEl.offsetHeight;
                if (thumbTop < railTop) thumbsRail.scrollTop = thumbTop - 8;
                else if (thumbBottom > railBottom) thumbsRail.scrollTop = thumbBottom - thumbsRail.clientHeight + 8;
            }
        }
    }

    if (inp) {
        inp.addEventListener("input", onDaysInput);
        inp.addEventListener("blur", normalizeDaysField);
    }
    if (startDateInp) {
        startDateInp.addEventListener("change", function () {
            if (!startDateInp.value) startDateInp.value = cfg.selected_start_date;
            refreshAvailability();
        });
    }
    btns.forEach(function (btn) {
        btn.addEventListener("click", function () {
            setDays((parseInt(inp.value, 10) || 1) + parseInt(this.dataset.step, 10));
        });
    });

    if (mainImg) {
        mainImg.addEventListener("load", function () {
            this.classList.remove("is-fading");
        });
    }
    thumbs.forEach(function (thumb) {
        thumb.addEventListener("click", function () {
            setImage(parseInt(this.dataset.index, 10) || 0);
        });
    });
    if (prevBtn) prevBtn.addEventListener("click", function () { setImage(currentIndex - 1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { setImage(currentIndex + 1); });

    if (inp) setDays(inp.value);
    setImage(0);
    refreshAvailability();

    var form = document.getElementById("add-to-bag-form");
    if (!form || !window.fetch) return;
    form.addEventListener("submit", function (e) {
        e.preventDefault();
        var daysInp = document.getElementById("days-input");
        if (daysInp) {
            var maxD = parseInt(daysInp.getAttribute("max"), 10) || 9999;
            var d = parseInt(daysInp.value, 10);
            if (isNaN(d) || d < 1) d = 1;
            if (d > maxD) d = maxD;
            daysInp.value = d;
            var td = document.getElementById("total-display");
            if (td) td.textContent = String((cfg.price_per_day || 0) * d);
        }
        var fd = new FormData(form);
        fetch(form.action, {
            method: "POST",
            body: fd,
            headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
            credentials: "same-origin",
        })
            .then(function (r) {
                if (!r.ok) throw new Error("bad");
                return r.json();
            })
            .then(function (data) {
                if (data && data.ok) {
                    if (window.paSetCartCount) window.paSetCartCount(data.cart_count);
                    if (window.paShowCartToast) window.paShowCartToast(data.product_name);
                }
            })
            .catch(function () {
                form.submit();
            });
    });
})();
