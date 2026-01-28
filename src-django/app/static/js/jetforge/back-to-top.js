(() => {
    // Back to Top Button
    const backToTop = document.getElementById("backToTop");
    window.onscroll = function () {
        if (document.body.scrollTop > 200 || document.documentElement.scrollTop > 200) {
            backToTop.style.display = "block";
        } else {
            backToTop.style.display = "none";
        }
    };
})();