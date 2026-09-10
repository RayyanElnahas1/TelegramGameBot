document.addEventListener("DOMContentLoaded", function () {

    const textarea =
        document.getElementById("chatMessage");

    const sendButton =
        document.getElementById("sendMessage");

    const messagesContainer =
        document.getElementById("chatMessages");


    // النزول لآخر رسالة

    function scrollToBottom() {
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

        if (!messagesContainer) {
            return;
        }

        messagesContainer.scrollTop =
            messagesContainer.scrollHeight;

    }


    scrollToBottom();


    // إرسال الرسالة عند الضغط على Enter

    if (textarea) {

        textarea.addEventListener(
            "keydown",
            function (event) {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    if (sendButton) {
                        sendButton.click();
                    }

                }

            }
        );

    }


    // حاليًا مجرد تجهيز للواجهة.
    // بعد ما نعمل Flask route هنربطه بالباك إند.

    if (sendButton) {

        sendButton.addEventListener(
            "click",
            function () {

                const message =
                    textarea
                        ? textarea.value.trim()
                        : "";

                if (!message) {
                    return;
                }

                console.log(
                    "Message ready to send:",
                    message
                );

            }
        );

    }

});