document.addEventListener("DOMContentLoaded", function () {

    // --- 1. التمرير التلقائي لأسفل صندوق المحادثة ---
    const chatBox = document.querySelector(".chat-box");
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- 2. البحث والفلترة في جدول الطلبات ---
    const searchInput = document.getElementById("orderSearch");
    const statusFilter = document.getElementById("statusFilter");
    const rows = document.querySelectorAll(".order-row");

    function filterOrders() {
        const search = searchInput
            ? searchInput.value.toLowerCase().trim()
            : "";

        const status = statusFilter
            ? statusFilter.value
            : "all";

        rows.forEach(function (row) {
            const rowText = row.textContent.toLowerCase();
            const rowStatus = row.dataset.status || "";

            const matchesSearch = rowText.includes(search);
            const matchesStatus =
                status === "all" || rowStatus === status;

            if (matchesSearch && matchesStatus) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterOrders);
    }

    if (statusFilter) {
        statusFilter.addEventListener("change", filterOrders);
    }

});
