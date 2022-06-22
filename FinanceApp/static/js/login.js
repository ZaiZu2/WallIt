// show specified submenu while hiding the rest
const showSubmenu = function (submenuId) {
  const submenuNodes = document.getElementsByClassName('sub-menu');

  [...submenuNodes].forEach(submenuNode => {
    if (submenuNode.id === submenuId) {
      submenuNode.classList.remove('hidden');
      // save last open submenu
      sessionStorage.setItem('lastOpenSubmenu', submenuNode.id);
    }
    else submenuNode.classList.add('hidden');
  })
}

const backButtons = document.getElementsByClassName('back-button');
[...backButtons].forEach((button) => {
  button.addEventListener('click', () => showSubmenu('login'));
});

const resetPassButton = document.getElementById('reset-password-button');
resetPassButton.addEventListener('click', () => showSubmenu('reset-password'));

const signUpButton = document.getElementById('sign-up-button');
signUpButton.addEventListener('click', () => showSubmenu('sign-up'));

// Load last open submenu if available else open login menu
if (sessionStorage.getItem('lastOpenSubmenu'))
  showSubmenu(sessionStorage.getItem('lastOpenSubmenu'));
else showSubmenu('login');
