(function () {
    var checkoutForm = document.querySelector('form[action*="/cart/checkout"]');
    if (!checkoutForm) return;
    checkoutForm.addEventListener("submit", function () {
        var btn = checkoutForm.querySelector('button[type="submit"]');
        if (!btn) return;
        btn.disabled = true;
        btn.classList.add("is-loading");
    });
})();
