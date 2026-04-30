(function () {
    var items = Array.prototype.slice.call(document.querySelectorAll(".about-faq-item"));
    if (!items.length) return;
    items.forEach(function (item) {
        item.addEventListener("toggle", function () {
            if (!item.open) return;
            items.forEach(function (other) {
                if (other !== item) other.open = false;
            });
        });
    });
})();
