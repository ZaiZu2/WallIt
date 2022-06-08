const menuButtons = document.querySelectorAll('.menu button');
menuButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Toggle button ON/OFF
        button.classList.toggle('active-menu-button');
        // Toggle icon ON/OFF
        button.childNodes[1].classList.toggle('active-menu-button');
        // Show/hide windows corresponding to a given button
        const menuWindow = document.getElementsByClassName(button.id);
        menuWindow[0].classList.toggle('hidden');
    })
});

const filterButtons = document.querySelectorAll('.filter-button-list button');
filterButtons.forEach(button => {
    button.addEventListener('click', () => {
        button.classList.toggle('active');

        const content = document.getElementById(button.id + 'Content');
        if (content.style.maxHeight) {
            content.style.maxHeight = null;
            content.style.border = null;
        } else {
            content.style.borderTop = '1px solid rgba(110, 110, 110, 1)'
            content.style.maxHeight = content.scrollHeight + 'px';
        }

        // Check if any of FilterButtons is ON to toggle on the SUBMIT button
        let isActive = false;
        for (let node of [...button.parentNode.children]) {
            if (node.classList.contains('active')) isActive = true;
        };

        const submitButton = document.getElementById('submitContent');
        if (isActive === true) {
            submitButton.style.borderTop = '1px solid rgba(110, 110, 110, 1)'
            submitButton.style.maxHeight = submitButton.scrollHeight + 'px';
        } else {
            submitButton.style.maxHeight = null;
            submitButton.style.border = null;
        };
    })
});
