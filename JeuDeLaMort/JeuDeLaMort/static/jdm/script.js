
document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menu-toggle");
    const mobileMenu = document.getElementById("mobile-menu");
    const closeMenu = document.getElementById("close-menu");

    menuToggle.addEventListener("click", function () {
        mobileMenu.classList.add("active");
    });

    closeMenu.addEventListener("click", function () {
        mobileMenu.classList.remove("active");
    });

    var swiperResume = new Swiper("#resume", {
      spaceBetween: 30,
      loop: true,
      effect: 'ease',
      navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",}
    });

    var swiperFavoris = new Swiper("#favoris", {
      spaceBetween: 30,
      loop: true,
      effect: 'ease',
      pagination: {
        el: '.swiper-pagination',
        type: 'bullets',
        clickable: true,
        },
      navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",}
    });

    var swiperCandidats = new Swiper("#candidats", {
      spaceBetween: 30,
      loop: true,
      effect: 'ease',
      pagination: {
        el: '.swiper-pagination',
        type: 'bullets',
        clickable: true,
        },
      navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",}
    });

        var swiperDecedes = new Swiper("#decedes", {
      spaceBetween: 30,
      loop: true,
      effect: 'ease',
      navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",}
    });
});

