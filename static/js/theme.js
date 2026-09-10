document.addEventListener("DOMContentLoaded", function () {

    const themeToggle =
        document.getElementById("themeToggle");

    const themeIcon =
        document.getElementById("themeIcon");

    const savedTheme =
        localStorage.getItem("dashboard-theme");


    function applyTheme(theme) {

        if (theme === "dark") {

            document.body.classList.add("dark-mode");

            if (themeIcon) {
                themeIcon.className =
                    "bi bi-sun-fill";
            }

        } else {

            document.body.classList.remove("dark-mode");

            if (themeIcon) {
                themeIcon.className =
                    "bi bi-moon-fill";
            }

        }

    }


    // تحميل الثيم المحفوظ

    if (savedTheme) {

        applyTheme(savedTheme);

    } else {

        applyTheme("light");

    }


    // تغيير الثيم

    if (themeToggle) {

        themeToggle.addEventListener("click", function () {

            const isDark =
                document.body.classList.contains("dark-mode");

            const newTheme =
                isDark ? "light" : "dark";

            localStorage.setItem(
                "dashboard-theme",
                newTheme
            );

            applyTheme(newTheme);

        });

    }

});