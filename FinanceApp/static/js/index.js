// Allows button to toggle menu windows ON/OFF with responsive button behavior
const menuButtons = document.querySelectorAll('.menu button');
menuButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Toggle button ON/OFF
        button.classList.toggle('active');
        // Toggle icon ON/OFF
        button.childNodes[1].classList.toggle('active');
        // Show/hide windows corresponding to a given button
        const menuWindow = document.getElementsByClassName(button.id);
        menuWindow[0].classList.toggle('hidden');
    })
});


const toggleCollapsible = function (node) {
    if (node.style.maxHeight) {
        node.style.maxHeight = null;
    } else {
        node.style.maxHeight = node.scrollHeight + 'px';
    }
}

// Allows filtering buttons to extend FILTER menu to make it responsive
const filterButtons = document.querySelectorAll('.filter-button-list button');
filterButtons.forEach(button => {
    button.addEventListener('click', () => {
        button.classList.toggle('active');

        // If button is switched OFF, hide corresponding FILTER menu
        // If button is switched ON, show corresponding FILTER menu
        const content = document.getElementsByName(button.id.substring(6))[0];
        content.classList.toggle('active');
        if (content.style.maxHeight) content.style.maxHeight = null;
        else content.style.maxHeight = content.scrollHeight + 'px';

        //  If any of FilterButtons is OFF, hide the SUBMIT button
        //  If any of FilterButtons is ON, show the SUBMIT button
        let isActive = false;
        for (let node of [...button.parentNode.children]) {
            if (node.classList.contains('active')) {
                isActive = true;
                break;
            };
        };
        const submitButton = document.getElementById('submitContent');
        if (isActive === true) {
            submitButton.classList.add('active');
            submitButton.style.maxHeight = submitButton.scrollHeight + 'px';
        } else {
            submitButton.classList.remove('active');
            submitButton.style.maxHeight = null;
        };
    })
});

// submit multiple forms and send request with JSONified input
const filterSubmit = document.getElementById('filterSubmit');
filterSubmit.addEventListener("click", (e) => {
    let inputs = {};

    // loop over all filter forms and extract inputs from each one
    const filterForms = document.querySelectorAll('form.filter-input');
    [...filterForms].forEach(form => {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const formData = new FormData(form);

            // Crate object for input values
            if (form.name === ('Amount' || 'Date')) {
                let localInputs = {};
                formData.forEach((value, key) => localInputs[key] = value);
                inputs[form.name] = localInputs;
            } else { // Create array for checkbox values
                let localInputs = [];
                formData.forEach((value, key) => localInputs.push(key));
                inputs[form.name] = localInputs;
            }
        });
        form.requestSubmit();
    });

    postData('./index.html', inputs);
});

// Example POST method implementation:
async function postData(url = '', data = {}) {
    // Default options are marked with *
    const response = await fetch(url, {
        method: 'POST', // *GET, POST, PUT, DELETE, etc.
        mode: 'cors', // no-cors, *cors, same-origin
        cache: 'default', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: { 'Content-Type': 'application/json' },
        redirect: 'follow', // manual, *follow, error
        referrerPolicy: 'no-referrer-when-downgrade', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
        body: JSON.stringify(data) // body data type must match "Content-Type" header
    });
    return response.json(); // parses JSON response into native JavaScript objects
}

new gridjs.Grid({
    search: true,
    columns: [{
        name: "Name",
        sort: {
            enabled: false
        },

    }, {
        name: "Title",
        sort: {
            enabled: false
        },
        search: {
            enabled: false
        }
    }, {
        name: "Amount",
    }, {
        name: "Currency",
    }, {
        name: "Category",
    }, {
        name: "Date"
    }, {
        name: "Bank"
    }],
    data: [
        ["John", "john@example.com", "(353) 01 222 3333", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Mark", "mark@gmail.com", "(01) 22 888 4444", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Eoin", "eoin@gmail.com", "0097 22 654 00033", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Sarah", "sarahcdd@gmail.com", "+322 876 1233", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Afshin", "afshin@mail.com", "(353) 22 87 8356", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["John", "john@example.com", "(353) 01 222 3333", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Mark", "mark@gmail.com", "(01) 22 888 4444", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Eoin", "eoin@gmail.com", "0097 22 654 00033", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Sarah", "sarahcdd@gmail.com", "+322 876 1233", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Afshin", "afshin@mail.com", "(353) 22 87 8356", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["John", "john@example.com", "(353) 01 222 3333", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Mark", "mark@gmail.com", "(01) 22 888 4444", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Eoin", "eoin@gmail.com", "0097 22 654 00033", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Sarah", "sarahcdd@gmail.com", "+322 876 1233", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"],
        ["Afshin", "afshin@mail.com", "(353) 22 87 8356", "Afshin", "afshin@mail.com", "(353) 22 87 8356", "(353) 22 87 8356"]
    ],
    sort: true,
    pagination: {
        enabled: true,
        limit: 10
    },
    className: {
        container: 'custom-container',
        table: 'custom-table',
        tbody: 'custom-tbody',
        thead: 'custom-thead',
        header: 'custom-header',
        footer: 'custom-footer',
        td: 'custom-td',
        th: 'custom-th',
        paginationSummary: 'custom-pagination-summary',
        paginationButton: 'custom-pagination-button',
        paginationButtonNext: 'custom-pagination-button-next',
        paginationButtonCurrent: 'custom-pagination-button-current',
        paginationButtonPrev: 'custom-pagination-button-prev',
    }
}).render(document.getElementById("poop"));
