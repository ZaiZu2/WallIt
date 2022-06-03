const toggleWindow = function (divId) {
  const menuNode = document.querySelector(divId);
  menuNode.classList.toggle('hidden');
}

const backButtons = document.querySelectorAll('#back');
backButtons.forEach((button) => {
  button.addEventListener('click', () => {
    toggleWindow('#login');

    let buttonParent = button.parentElement;
    while (true) {
      if (buttonParent.id === 'reset-password')
      {
        toggleWindow('#reset-password');
        break;
      } else if (buttonParent.id === 'sign-up') {
        toggleWindow('#sign-up');
        break;
      };
      buttonParent = buttonParent.parentElement;
    };
  });
});

const resetPassButton = document.querySelector('#reset-password-menu');
resetPassButton.addEventListener('click', () => {
    toggleWindow('#login');
    toggleWindow('#reset-password');
});

const signUpButton = document.querySelector('#sign-up-menu');
signUpButton.addEventListener('click', () => {
    toggleWindow('#login');
    toggleWindow('#sign-up');
});
