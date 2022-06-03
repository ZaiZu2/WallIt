const menuButtons = document.querySelectorAll('.menu button');
menuButtons.forEach(button => {
    button.addEventListener('click', () => {
        button.classList.toggle('active-menu-button');
        button.childNodes[1].classList.toggle('active-menu-button');
    })
});
