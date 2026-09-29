/* =========================================
   CODE NEST — BASE JAVASCRIPT
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    const menuButton = document.querySelector(".mobile-menu-button");
    const mobileNavigation =
        document.querySelector(".mobile-navigation");

    if (!menuButton || !mobileNavigation) {
        return;
    }

    menuButton.addEventListener("click", () => {

        const isOpen =
            mobileNavigation.classList.toggle("is-open");

        menuButton.setAttribute(
            "aria-expanded",
            String(isOpen)
        );

    });

});