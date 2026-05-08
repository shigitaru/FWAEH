(function () {
    function readI18n() {
        var out = {
            dragToReorder: "Drag to reorder",
            mainBadge: "Main",
            remove: "Remove",
        };
        try {
            var el = document.getElementById("admin-i18n-json");
            if (!el) return out;
            var parsed = JSON.parse(el.textContent || "{}");
            if (parsed && typeof parsed === "object") {
                out.dragToReorder = parsed.dragToReorder || out.dragToReorder;
                out.mainBadge = parsed.mainBadge || out.mainBadge;
                out.remove = parsed.remove || out.remove;
            }
        } catch (e) {}
        return out;
    }
    function readBrands() {
        var brands = [];
        try {
            var brandsJsonEl = document.getElementById("admin-brands-json");
            brands = JSON.parse(brandsJsonEl ? brandsJsonEl.textContent : "[]") || [];
        } catch (e) {
            brands = [];
        }
        return brands;
    }

    function escapeHtml(text) {
        return String(text).replace(/[&<>"']/g, function (ch) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
        });
    }

    function initBrandAutocomplete(brands) {
        var brandInput = document.querySelector('input[name="brand"]');
        var panel = document.getElementById("brand-suggestions");
        if (!brandInput || !panel) return;
        var activeIndex = -1;
        var visibleItems = [];

        function hidePanel() {
            panel.hidden = true;
            panel.innerHTML = "";
            activeIndex = -1;
            visibleItems = [];
        }
        function setActive(index) {
            visibleItems.forEach(function (item, idx) {
                item.classList.toggle("is-active", idx === index);
            });
            activeIndex = index;
        }
        function applyValue(value) {
            brandInput.value = value;
            hidePanel();
        }
        function buildRows(query) {
            var q = (query || "").trim().toLowerCase();
            var source = brands.slice();
            var matched = source
                .filter(function (name) {
                    if (!q) return true;
                    return name.toLowerCase().indexOf(q) !== -1;
                })
                .sort(function (a, b) {
                    var aStarts = q && a.toLowerCase().indexOf(q) === 0;
                    var bStarts = q && b.toLowerCase().indexOf(q) === 0;
                    if (aStarts && !bStarts) return -1;
                    if (!aStarts && bStarts) return 1;
                    return a.localeCompare(b);
                })
                .slice(0, 7);
            if (!matched.length) {
                hidePanel();
                return;
            }
            panel.innerHTML = matched
                .map(function (name) {
                    return '<button type="button" class="brand-suggestion-item" data-value="' + escapeHtml(name) + '">' + escapeHtml(name) + "</button>";
                })
                .join("");
            panel.hidden = false;
            visibleItems = Array.prototype.slice.call(panel.querySelectorAll(".brand-suggestion-item"));
            setActive(-1);
        }

        brandInput.addEventListener("focus", function () { buildRows(brandInput.value); });
        brandInput.addEventListener("input", function () { buildRows(brandInput.value); });
        brandInput.addEventListener("keydown", function (e) {
            if (panel.hidden || !visibleItems.length) return;
            if (e.key === "ArrowDown") {
                e.preventDefault();
                var next = activeIndex + 1;
                if (next >= visibleItems.length) next = 0;
                setActive(next);
                return;
            }
            if (e.key === "ArrowUp") {
                e.preventDefault();
                var prev = activeIndex - 1;
                if (prev < 0) prev = visibleItems.length - 1;
                setActive(prev);
                return;
            }
            if (e.key === "Enter" && activeIndex >= 0) {
                e.preventDefault();
                applyValue(visibleItems[activeIndex].dataset.value || visibleItems[activeIndex].textContent);
                return;
            }
            if (e.key === "Escape") hidePanel();
        });
        panel.addEventListener("mousedown", function (e) {
            var item = e.target.closest(".brand-suggestion-item");
            if (!item) return;
            e.preventDefault();
            applyValue(item.dataset.value || item.textContent);
        });
        document.addEventListener("mousedown", function (e) {
            if (!e.target.closest(".brand-autocomplete")) hidePanel();
        });
    }

    function initCategoryPicker() {
        var picker = document.querySelector(".category-picker");
        if (!picker) return;
        var input = picker.querySelector('input[name="category"]');
        var pills = Array.prototype.slice.call(picker.querySelectorAll(".category-pill"));
        if (!input || !pills.length) return;
        function setActive(value) {
            input.value = value;
            pills.forEach(function (btn) {
                btn.classList.toggle("is-active", btn.dataset.value === value);
            });
        }
        pills.forEach(function (btn) {
            btn.addEventListener("click", function () { setActive(btn.dataset.value); });
        });
        setTimeout(function () { setActive(input.value || "rtw"); }, 0);
    }

    function isMedia(file) {
        return file && file.type && (file.type.indexOf("image/") === 0 || file.type.indexOf("video/") === 0);
    }

    function assignDroppedFiles(inp, droppedFiles) {
        var dt = new DataTransfer();
        var isMultiple = inp.hasAttribute("multiple");
        if (isMultiple && inp.files && inp.files.length) {
            Array.prototype.slice.call(inp.files).forEach(function (file) {
                if (isMedia(file)) dt.items.add(file);
            });
        }
        Array.prototype.slice.call(droppedFiles || []).forEach(function (file) {
            if (isMedia(file)) dt.items.add(file);
        });
        if (!isMultiple && dt.files.length > 1) {
            var single = new DataTransfer();
            single.items.add(dt.files[0]);
            inp.files = single.files;
        } else {
            inp.files = dt.files;
        }
    }

    function renderPreview(inp, preview, i18n) {
        if (!preview) return;
        preview.innerHTML = "";
        var files = Array.prototype.slice.call(inp.files || []);
        var dragIndex = -1;

        function setInputFiles(nextFiles) {
            var dt = new DataTransfer();
            Array.prototype.slice.call(nextFiles || []).forEach(function (f) {
                if (isMedia(f)) dt.items.add(f);
            });
            inp.files = dt.files;
        }
        function moveFile(fromIdx, toIdx) {
            var current = Array.prototype.slice.call(inp.files || []);
            if (fromIdx < 0 || toIdx < 0 || fromIdx >= current.length || toIdx >= current.length) return;
            if (fromIdx === toIdx) return;
            var moved = current.splice(fromIdx, 1)[0];
            current.splice(toIdx, 0, moved);
            setInputFiles(current);
            renderPreview(inp, preview, i18n);
            inp.dispatchEvent(new Event("change", { bubbles: true }));
        }

        files.forEach(function (file, idx) {
            if (!isMedia(file)) return;
            var card = document.createElement("div");
            card.className = "upload-preview-item";
            card.draggable = true;
            card.setAttribute("data-preview-index", String(idx));
            card.title = i18n.dragToReorder;
            card.addEventListener("dragstart", function (e) {
                dragIndex = idx;
                card.classList.add("is-dragging");
                if (e.dataTransfer) {
                    e.dataTransfer.effectAllowed = "move";
                    try {
                        e.dataTransfer.setData("text/plain", String(idx));
                    } catch (err) {}
                }
            });
            card.addEventListener("dragend", function () {
                dragIndex = -1;
                card.classList.remove("is-dragging");
                preview.querySelectorAll(".upload-preview-item").forEach(function (el) {
                    el.classList.remove("is-drag-over");
                });
            });
            card.addEventListener("dragover", function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (e.dataTransfer) e.dataTransfer.dropEffect = "move";
                card.classList.add("is-drag-over");
            });
            card.addEventListener("dragleave", function () { card.classList.remove("is-drag-over"); });
            card.addEventListener("drop", function (e) {
                e.preventDefault();
                e.stopPropagation();
                card.classList.remove("is-drag-over");
                moveFile(dragIndex, idx);
            });

            if (file.type.indexOf("video/") === 0) {
                var vid = document.createElement("video");
                vid.muted = true;
                vid.controls = true;
                vid.preload = "metadata";
                vid.src = URL.createObjectURL(file);
                vid.onloadeddata = function () { URL.revokeObjectURL(vid.src); };
                card.appendChild(vid);
            } else {
                var img = document.createElement("img");
                img.alt = file.name;
                img.src = URL.createObjectURL(file);
                img.onload = function () { URL.revokeObjectURL(img.src); };
                card.appendChild(img);
            }
            if (idx === 0) {
                var mainBadge = document.createElement("div");
                mainBadge.className = "admin-media-main-badge";
                mainBadge.textContent = i18n.mainBadge;
                card.appendChild(mainBadge);
            }
            var controls = document.createElement("div");
            controls.className = "admin-media-controls";
            var removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "admin-media-btn";
            removeBtn.textContent = i18n.remove;
            removeBtn.addEventListener("click", function () {
                var current = Array.prototype.slice.call(inp.files || []);
                var next = current.filter(function (_, currentIdx) { return currentIdx !== idx; });
                setInputFiles(next);
                renderPreview(inp, preview, i18n);
                inp.dispatchEvent(new Event("change", { bubbles: true }));
            });
            controls.appendChild(removeBtn);
            card.appendChild(controls);
            preview.appendChild(card);
        });
    }

    function getClipboardImageFiles(e) {
        var out = [];
        var cd = e && e.clipboardData ? e.clipboardData : null;
        if (!cd || !cd.items || !cd.items.length) return out;
        Array.prototype.slice.call(cd.items).forEach(function (item) {
            if (!item || item.kind !== "file") return;
            if (item.type && item.type.indexOf("image/") !== 0) return;
            var f = item.getAsFile ? item.getAsFile() : null;
            if (f) out.push(f);
        });
        return out;
    }

    function initUploadZones(i18n) {
        document.querySelectorAll('.upload-dropzone input[type="file"]').forEach(function (inp) {
            var zone = inp.closest(".upload-dropzone");
            var preview = zone.querySelector(".upload-preview-list");
            var beforePickerFiles = [];
            function fileKey(f) {
                if (!f) return "";
                return [f.name, f.size, f.lastModified].join("::");
            }
            function mergeFileLists(a, b) {
                var dt = new DataTransfer();
                var seen = {};
                Array.prototype.slice.call(a || []).forEach(function (f) {
                    if (!isMedia(f)) return;
                    var k = fileKey(f);
                    if (!k || seen[k]) return;
                    seen[k] = true;
                    dt.items.add(f);
                });
                Array.prototype.slice.call(b || []).forEach(function (f) {
                    if (!isMedia(f)) return;
                    var k = fileKey(f);
                    if (!k || seen[k]) return;
                    seen[k] = true;
                    dt.items.add(f);
                });
                return dt.files;
            }
            ["dragenter", "dragover"].forEach(function (evt) {
                zone.addEventListener(evt, function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
                    zone.classList.add("is-drag");
                });
            });
            zone.addEventListener("dragleave", function (e) {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove("is-drag");
            });
            zone.addEventListener("drop", function (e) {
                e.preventDefault();
                e.stopPropagation();
                zone.classList.remove("is-drag");
                var files = e.dataTransfer && e.dataTransfer.files ? e.dataTransfer.files : null;
                if (!files || !files.length) return;
                assignDroppedFiles(inp, files);
                renderPreview(inp, preview, i18n);
                inp.dispatchEvent(new Event("change", { bubbles: true }));
            });
            zone.addEventListener("paste", function (e) {
                var files = getClipboardImageFiles(e);
                if (!files || !files.length) return;
                e.preventDefault();
                e.stopPropagation();
                assignDroppedFiles(inp, files);
                renderPreview(inp, preview, i18n);
                inp.dispatchEvent(new Event("change", { bubbles: true }));
            });
            inp.addEventListener("click", function () {
                if (!inp.hasAttribute("multiple")) return;
                beforePickerFiles = Array.prototype.slice.call(inp.files || []);
            });
            inp.addEventListener("change", function () {
                if (inp.hasAttribute("multiple") && beforePickerFiles && beforePickerFiles.length) {
                    var merged = mergeFileLists(beforePickerFiles, inp.files);
                    inp.files = merged;
                    beforePickerFiles = [];
                }
                renderPreview(inp, preview, i18n);
            });
        });
    }

    function initAdminImageSort() {
        var list = document.getElementById("admin-image-sort-list");
        if (!list) return;
        var dragEl = null;
        function clearDrag() {
            if (dragEl) dragEl.classList.remove("is-dragging");
            dragEl = null;
        }
        list.querySelectorAll(".admin-image-drag-handle").forEach(function (handle) {
            handle.addEventListener("dragstart", function (e) {
                dragEl = handle.closest("[data-sort-tile]");
                if (dragEl) dragEl.classList.add("is-dragging");
                if (e.dataTransfer) {
                    e.dataTransfer.effectAllowed = "move";
                    try {
                        e.dataTransfer.setData("text/plain", "sort");
                    } catch (err) {}
                }
            });
            handle.addEventListener("dragend", clearDrag);
        });
        list.querySelectorAll("[data-sort-tile]").forEach(function (tile) {
            tile.addEventListener("dragover", function (e) {
                e.preventDefault();
                if (e.dataTransfer) e.dataTransfer.dropEffect = "move";
            });
            tile.addEventListener("drop", function (e) {
                e.preventDefault();
                if (!dragEl || dragEl === tile) return;
                var rect = tile.getBoundingClientRect();
                var before = e.clientX < rect.left + rect.width / 2;
                if (before) list.insertBefore(dragEl, tile);
                else list.insertBefore(dragEl, tile.nextSibling);
            });
        });
    }

    function initConfirmSubmit() {
        document.querySelectorAll(".js-confirm-submit").forEach(function (formEl) {
            formEl.addEventListener("submit", function (e) {
                var msg = formEl.getAttribute("data-confirm") || "";
                if (msg && !window.confirm(msg)) e.preventDefault();
            });
        });
    }

    function initBrandFontPreview() {
        var fontClassWhitelist = [
            "brand-font-inter",
            "brand-font-instrument-serif",
            "brand-font-cormorant-garamond",
            "brand-font-cinzel",
            "brand-font-bodoni-moda",
            "brand-font-space-grotesk",
            "brand-font-archivo-black",
        ];
        document.querySelectorAll(".admin-brand-font-form").forEach(function (formEl) {
            var select = formEl.querySelector(".admin-brand-font-select");
            if (!select) return;
            var row = formEl.closest(".admin-brand-row");
            if (!row) return;
            var preview = row.querySelector("[data-brand-font-preview]");
            if (!preview) return;
            function syncPreview() {
                fontClassWhitelist.forEach(function (cls) { preview.classList.remove(cls); });
                var key = String(select.value || "inter").trim().toLowerCase();
                preview.classList.add("brand-font-" + key);
            }
            select.addEventListener("change", syncPreview);
            syncPreview();
        });
    }

    function initMeasurementsEditor() {
        var root = document.getElementById("admin-measurements-editor");
        var garmentTbody = document.getElementById("admin-measurements-garment-tbody");
        if (!root || !garmentTbody) return;

        var sizesInput = document.getElementById("admin-product-sizes");
        var panelGarment = document.getElementById("admin-measurements-panel-garment");
        var panelFoot = document.getElementById("admin-measurements-panel-footwear");
        var garmentThead = document.getElementById("admin-measurements-garment-thead");
        var footwearTbody = document.getElementById("admin-measurements-footwear-tbody");
        var addGarmentBtn = document.getElementById("admin-measurements-add-garment");
        var addFootBtn = document.getElementById("admin-measurements-add-footwear");

        try {
            var mij = document.getElementById("admin-measurements-editor-i18n");
            JSON.parse(mij ? mij.textContent : "{}");
        } catch (eIgn) {}

        var snapshot = null;
        try {
            var sj = document.getElementById("admin-measurements-snapshot");
            snapshot = JSON.parse(sj ? sj.textContent : "null");
        } catch (eS) {
            snapshot = null;
        }

        var nextGarmentIx = 0;

        function kindValue() {
            var r = root.querySelector('input[name="measurements_kind"]:checked');
            return r ? r.value : "none";
        }

        function parseSizesCsv() {
            var raw = (sizesInput && sizesInput.value) || "";
            return raw
                .split(",")
                .map(function (s) {
                    return s.trim();
                })
                .filter(Boolean);
        }

        function garmentColumnLabels() {
            var fromSizes = parseSizesCsv();
            if (fromSizes.length) return fromSizes;
            if (snapshot && snapshot.kind === "garment" && Array.isArray(snapshot.columns) && snapshot.columns.length) {
                return snapshot.columns.map(function (x) {
                    return String(x);
                });
            }
            return [];
        }

        function effectiveGarmentCols() {
            var g = garmentColumnLabels();
            return g.length ? g : [""];
        }

        function rebuildGarmentHeader(labels) {
            if (!garmentThead) return;
            garmentThead.innerHTML = "";
            var tr = document.createElement("tr");
            var thP = document.createElement("th");
            thP.setAttribute("scope", "col");
            thP.textContent = root.getAttribute("data-label-parameter") || "";
            tr.appendChild(thP);
            if (labels.length) {
                labels.forEach(function (lbl) {
                    var th = document.createElement("th");
                    th.setAttribute("scope", "col");
                    th.textContent = lbl;
                    tr.appendChild(th);
                });
            } else {
                var th0 = document.createElement("th");
                th0.setAttribute("scope", "col");
                th0.textContent = "…";
                tr.appendChild(th0);
            }
            garmentThead.appendChild(tr);
        }

        function garmentRowIx(tr) {
            var ix = parseInt(tr.getAttribute("data-garment-ix"), 10);
            return isNaN(ix) ? 0 : ix;
        }

        function gatherRowVals(tr) {
            var out = [];
            for (var c = 1; c < tr.cells.length; c++) {
                var inp = tr.cells[c].querySelector("input");
                out.push(inp ? inp.value : "");
            }
            return out;
        }

        function ensureGarmentValueCells(tr, ix, colCount, preset) {
            while (tr.cells.length > 1) {
                tr.deleteCell(1);
            }
            var n = Math.max(1, colCount || 0);
            for (var j = 0; j < n; j++) {
                var td = document.createElement("td");
                var inp = document.createElement("input");
                inp.type = "text";
                inp.className = "search-input";
                inp.autocomplete = "off";
                inp.name = "garment_meas_" + ix + "_v_" + j;
                if (preset && preset[j] !== undefined && preset[j] !== null && preset[j] !== "") {
                    inp.value = String(preset[j]);
                }
                td.appendChild(inp);
                tr.appendChild(td);
            }
        }

        function addGarmentRow(labelRu, valuesPreset) {
            var ix = nextGarmentIx++;
            var tr = document.createElement("tr");
            tr.setAttribute("data-garment-ix", String(ix));

            var tdLb = document.createElement("td");
            var inpLb = document.createElement("input");
            inpLb.type = "text";
            inpLb.className = "search-input";
            inpLb.autocomplete = "off";
            inpLb.name = "garment_meas_" + ix + "_label";
            inpLb.value = labelRu || "";
            tdLb.appendChild(inpLb);
            tr.appendChild(tdLb);

            var cols = effectiveGarmentCols();
            ensureGarmentValueCells(tr, ix, cols.length, valuesPreset || []);
            garmentTbody.appendChild(tr);
        }

        function hydrateGarmentFromSnapshotOnce() {
            if (!snapshot || snapshot.kind !== "garment") return false;
            if (garmentTbody.rows.length) return false;
            var rows = Array.isArray(snapshot.rows) ? snapshot.rows : [];
            if (!rows.length) return false;
            rows.forEach(function (r) {
                if (!r || typeof r !== "object") return;
                var vals = Array.isArray(r.values) ? r.values : [];
                var lab = String(r.label || r.ru || r.en || "");
                addGarmentRow(lab, vals);
            });
            return garmentTbody.rows.length > 0;
        }

        function refreshGarmentGrid() {
            if (kindValue() !== "garment" || !garmentTbody) return;
            var labels = garmentColumnLabels();
            rebuildGarmentHeader(labels.length ? labels : []);
            var colCount = effectiveGarmentCols().length;
            Array.from(garmentTbody.rows).forEach(function (tr) {
                var preset = gatherRowVals(tr);
                var ix = garmentRowIx(tr);
                ensureGarmentValueCells(tr, ix, colCount, preset);
            });
            if (!garmentTbody.rows.length) {
                hydrateGarmentFromSnapshotOnce();
            }
            if (!garmentTbody.rows.length) {
                addGarmentRow("", []);
            }
        }

        function footwearI18n() {
            try {
                var mij = document.getElementById("admin-measurements-editor-i18n");
                return JSON.parse(mij ? mij.textContent : "{}") || {};
            } catch (eFi) {
                return {};
            }
        }

        function addFootwearRow(euVal, insVal) {
            if (!footwearTbody) return;
            var i18nf = footwearI18n();
            var tr = document.createElement("tr");

            var td1 = document.createElement("td");
            var inp1 = document.createElement("input");
            inp1.type = "text";
            inp1.className = "search-input";
            inp1.name = "footwear_meas_eu";
            inp1.autocomplete = "off";
            inp1.placeholder = i18nf.euPlaceholder || "";
            inp1.value = euVal || "";
            td1.appendChild(inp1);

            var td2 = document.createElement("td");
            var inp2 = document.createElement("input");
            inp2.type = "text";
            inp2.className = "search-input";
            inp2.name = "footwear_meas_insole";
            inp2.autocomplete = "off";
            inp2.placeholder = i18nf.insolePlaceholder || "";
            inp2.value = insVal || "";
            td2.appendChild(inp2);

            var td3 = document.createElement("td");
            var rm = document.createElement("button");
            rm.type = "button";
            rm.className = "admin-measurements-rm-row";
            rm.textContent = i18nf.rm || "×";
            rm.addEventListener("click", function () {
                tr.remove();
                if (footwearTbody && !footwearTbody.rows.length) addFootwearRow("", "");
            });
            td3.appendChild(rm);

            tr.appendChild(td1);
            tr.appendChild(td2);
            tr.appendChild(td3);
            footwearTbody.appendChild(tr);
        }

        function hydrateFootwearFromSnapshot() {
            if (!footwearTbody || !snapshot || snapshot.kind !== "footwear") return false;
            var rows = Array.isArray(snapshot.rows) ? snapshot.rows : [];
            footwearTbody.innerHTML = "";
            if (!rows.length) {
                addFootwearRow("", "");
                return true;
            }
            rows.forEach(function (r) {
                if (!r || typeof r !== "object") return;
                addFootwearRow(String(r.eu || ""), String(r.insole_cm || ""));
            });
            return true;
        }

        function refreshFootwearTable() {
            if (kindValue() !== "footwear" || !footwearTbody) return;
            if (!footwearTbody.rows.length) {
                hydrateFootwearFromSnapshot() || addFootwearRow("", "");
            }
        }

        function syncPanels() {
            var k = kindValue();
            if (panelGarment) panelGarment.classList.toggle("is-hidden", k !== "garment");
            if (panelFoot) panelFoot.classList.toggle("is-hidden", k !== "footwear");
            if (k === "garment") refreshGarmentGrid();
            else if (k === "footwear") refreshFootwearTable();
        }

        root.querySelectorAll('input[name="measurements_kind"]').forEach(function (inp) {
            inp.addEventListener("change", syncPanels);
        });
        if (sizesInput) {
            sizesInput.addEventListener("input", function () {
                if (kindValue() === "garment") refreshGarmentGrid();
            });
        }
        if (addGarmentBtn) addGarmentBtn.addEventListener("click", function () { addGarmentRow("", []); });
        if (addFootBtn) addFootBtn.addEventListener("click", function () { addFootwearRow("", ""); });

        syncPanels();
    }

    var brands = readBrands();
    var i18n = readI18n();
    initBrandAutocomplete(brands);
    initCategoryPicker();
    initUploadZones(i18n);
    initAdminImageSort();
    initConfirmSubmit();
    initBrandFontPreview();
    initMeasurementsEditor();
})();
