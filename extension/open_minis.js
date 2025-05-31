document.addEventListener("DOMContentLoaded", function() {
    const open_limit = document.getElementById("open_limit");
    if (open_limit) {
        open_limit.addEventListener("click", () => {
            window.location.href = "main_popups/hit_limit.html";
        });
    }

    const open_analogy = document.getElementById("open_analogy");
    if (open_analogy) {
        open_analogy.addEventListener("click", () => {
            window.location.href = "main_popups/analogy.html";
        });
    }

    const open_not_enough = document.getElementById("open_not_enough");
    if (open_not_enough) {
        open_not_enough.addEventListener("click", () => {
            window.location.href = "main_popups/not_enough.html";
        });
    }

    const open_successfully = document.getElementById("open_successfully");
    if (open_successfully) {
        open_successfully.addEventListener("click", () => {
            window.location.href = "main_popups/successfully.html";
        });
    }
});