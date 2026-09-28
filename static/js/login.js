(function () {
    "use strict";

    const toggleButtons = document.querySelectorAll(".toggle-password");

    toggleButtons.forEach(function (button) {
        const targetSelector = button.dataset.target;
        const input = document.querySelector(targetSelector);

        if (!input) {
            return;
        }

        button.addEventListener("click", function () {
            const isPassword = input.type === "password";

            input.type = isPassword ? "text" : "password";

            button.classList.toggle("is-visible", isPassword);

            button.setAttribute(
                "aria-label",
                isPassword ? "Hide password" : "Show password"
            );

            button.setAttribute(
                "aria-pressed",
                String(isPassword)
            );
        });
    });

})();