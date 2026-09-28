document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("registerForm");
    const password1 = document.getElementById("id_password1");
    const password2 = document.getElementById("id_password2");
    const strengthBox = document.querySelector(".password-strength");
    const strengthText = document.getElementById("strengthText");
    const matchMessage = document.getElementById("matchMessage");
    const registerButton = document.getElementById("registerButton");
    const terms = document.getElementById("terms");


    /* =========================================
       PASSWORD VISIBILITY
    ========================================= */

    document.querySelectorAll(".password-toggle").forEach(button => {

        button.addEventListener("click", () => {

            const targetId = button.dataset.target;
            const input = document.getElementById(targetId);

            if (!input) {
                return;
            }

            const isPassword = input.type === "password";

            input.type = isPassword ? "text" : "password";

            button.classList.toggle("visible", isPassword);

            button.setAttribute(
                "aria-label",
                isPassword ? "Hide password" : "Show password"
            );

        });

    });


    /* =========================================
       PASSWORD STRENGTH
    ========================================= */

    function calculatePasswordStrength(password) {

        let score = 0;

        if (password.length >= 8) {
            score++;
        }

        if (password.length >= 12) {
            score++;
        }

        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) {
            score++;
        }

        if (/\d/.test(password)) {
            score++;
        }

        if (/[^A-Za-z0-9]/.test(password)) {
            score++;
        }

        if (score >= 4) {
            return 4;
        }

        if (score === 3) {
            return 3;
        }

        if (score === 2) {
            return 2;
        }

        if (score === 1) {
            return 1;
        }

        return 0;
    }


    function updatePasswordStrength() {

        const password = password1.value;

        const strength = calculatePasswordStrength(password);

        strengthBox.dataset.strength = strength;

        const labels = {
            0: "—",
            1: "Weak",
            2: "Fair",
            3: "Good",
            4: "Strong"
        };

        strengthText.textContent = labels[strength];

    }


    password1.addEventListener("input", updatePasswordStrength);


    /* =========================================
       PASSWORD MATCH
    ========================================= */

    function updatePasswordMatch() {

        const first = password1.value;
        const second = password2.value;

        matchMessage.className = "match-message";

        if (!second) {
            matchMessage.textContent = "";
            return;
        }

        if (first === second) {

            matchMessage.textContent = "Passwords match.";
            matchMessage.classList.add("match");

        } else {

            matchMessage.textContent = "Passwords do not match.";
            matchMessage.classList.add("no-match");

        }

    }


    password1.addEventListener("input", updatePasswordMatch);
    password2.addEventListener("input", updatePasswordMatch);


    /* =========================================
       INPUT STATUS
    ========================================= */

    document.querySelectorAll(".input-wrapper input").forEach(input => {

        input.addEventListener("blur", () => {

            const wrapper = input.closest(".input-wrapper");

            if (!wrapper) {
                return;
            }

            if (input.value.trim()) {
                wrapper.classList.add("has-value");
            } else {
                wrapper.classList.remove("has-value");
            }

        });

    });


    /* =========================================
       FORM SUBMIT
    ========================================= */

    form.addEventListener("submit", event => {

        const passwordsMatch =
            password1.value === password2.value;

        if (!passwordsMatch) {

            event.preventDefault();

            password2.focus();

            matchMessage.textContent =
                "Passwords do not match.";

            matchMessage.className =
                "match-message no-match";

            return;
        }


        if (!terms.checked) {

            event.preventDefault();

            terms.focus();

            return;
        }


        /*
         * Do not prevent the form submission.
         * Django must perform the real validation.
         */

        registerButton.classList.add("loading");

    });


    /* =========================================
       INITIAL STATE
    ========================================= */

    updatePasswordStrength();
    updatePasswordMatch();

});