document.addEventListener("DOMContentLoaded", function () {

    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");

    if (!sidebar || !sidebarToggle) {
        return;
    }

    sidebarToggle.addEventListener("click", function () {

        document.body.classList.toggle("sidebar-collapsed");

    });

});
document.addEventListener("DOMContentLoaded", function () {
    console.log("Dashboard loaded successfully.");

    // البحث عن العناصر الأساسية (الزرار والـ Sidebar)
    const sidebar = document.getElementById("sidebar") || document.querySelector("aside") || document.querySelector(".sidebar");
    const toggleBtn = document.getElementById("sidebarToggle") || document.querySelector(".topbar button") || document.querySelector(".menu-btn");

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", function (e) {
            e.preventDefault();
            
            // إضافة/إزالة كلاسات الفتح والتسكير المشهورة
            sidebar.classList.toggle("active");
            sidebar.classList.toggle("show");
            sidebar.classList.toggle("open");
            
            console.log("تم الضغط على زر القائمة بنجاح!");
        });
    } else {
        console.warn("لم يتم العثور على زر القائمة أو الـ Sidebar في ملف الـ HTML.");
    }
});