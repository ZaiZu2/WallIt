import { transactionsTable, reloadTable } from "./gridjs.js";
import {
  categoryChart,
  reloadCategoryChart,
  monthlyChart,
  reloadMonthlyChart,
} from "./chartjs.js";
import { renderDropdowns, renderCheckboxes } from "./utils.js";

const logOutButton = document.getElementById("log-out");
logOutButton.addEventListener("click", logOut);

const modalButton = document.getElementById("modal-button");
modalButton.addEventListener("click", () => {
  const modal = document.getElementsByClassName("modal")[0];
  modal.classList.add("inactive");
  const backgroundDim = document.getElementsByClassName("dim-background")[0];
  backgroundDim.classList.add("inactive");
});

const selectionButtons = document.querySelectorAll(
  ".selection-button-list button"
);
selectionButtons.forEach((button) => {
  button.addEventListener("click", (event) => {
    if (!event.target.classList.contains("active")) {
      button.classList.add("active");
      const buttonMenu = document.getElementById(
        button.id.replace("_button", "")
      );
      buttonMenu.classList.remove("hidden");

      const siblingButtons = button.parentNode.childNodes;
      siblingButtons.forEach((siblingButton) => {
        if (
          siblingButton.nodeType != Node.TEXT_NODE &&
          siblingButton != event.target
        ) {
          siblingButton.classList.remove("active");
          const siblingMenu = document.getElementById(
            siblingButton.id.replace("_button", "")
          );
          siblingMenu.classList.add("hidden");
        }
      });
    } else {
      button.classList.remove("active");
      const selectionMenu = document.getElementById(
        button.id.replace("_button", "")
      );
      selectionMenu.classList.add("hidden");
    }
  });
});

// Allows button to toggle menu windows ON/OFF with responsive button behavior
const menuButtons = document.querySelectorAll(".menu button");
menuButtons.forEach((button) => {
  button.addEventListener("click", () => {
    // Toggle button ON/OFF
    button.classList.toggle("active");
    // Toggle icon ON/OFF
    button.childNodes[1].classList.toggle("active");
    // Show/hide windows corresponding to a given button
    const menuWindow = document.getElementsByClassName(button.id);
    menuWindow[0].classList.toggle("hidden");
  });
});

// Allows filtering buttons to extend FILTER menu to make it responsive
const allFormButtons = document.querySelectorAll(".button-list button");
allFormButtons.forEach((button) => {
  button.addEventListener("click", () => {
    button.classList.toggle("active");

    // If button is switched ON/OFF, show/hide corresponding menu
    // Distinct forms here have a distinct class assigned, only for their location
    const formField = document.getElementsByName(button.id)[0];
    formField.classList.toggle("active");
    if (formField.style.maxHeight) formField.style.maxHeight = null;
    else formField.style.maxHeight = formField.scrollHeight + "px";

    //  Check if any form buttons are active (pressed)...
    let isActive = false;
    for (const node of [...button.parentNode.children]) {
      if (node.classList.contains("active")) {
        isActive = true;
        break;
      }
    }
    // ... Find a submit button responsible for a specific form
    // and hide it in case all form buttons are inactive.
    const formSubmitButton = document.getElementById(
      `${button.classList[1]}_submit`
    );
    if (isActive === true) {
      formSubmitButton.classList.add("active");
      formSubmitButton.style.maxHeight = formSubmitButton.scrollHeight + "px";
    } else {
      formSubmitButton.classList.remove("active");
      formSubmitButton.style.maxHeight = null;
    }
  });
});

// Custom filter input validators
// Check that minAmount is always smaller than maxAmount (if both exist)
const minAmount = document.getElementById("minAmount");
const maxAmount = document.getElementById("maxAmount");
const amountInputs = [minAmount, maxAmount];
amountInputs.forEach((input) => {
  input.addEventListener("input", () => {
    if (maxAmount.value && minAmount.value) {
      minAmount.setAttribute("max", maxAmount.value);
      minAmount.checkValidity();
      maxAmount.setAttribute("min", minAmount.value);
      maxAmount.checkValidity();
    } else {
      minAmount.removeAttribute("max");
      minAmount.checkValidity();
      maxAmount.removeAttribute("min");
      maxAmount.checkValidity();
    }
  });
});
// Check that minDate is always before than maxDate (if both exist)
const minDate = document.getElementById("minDate");
const maxDate = document.getElementById("maxDate");
const dateInputs = [minDate, maxDate];
dateInputs.forEach((input) => {
  input.addEventListener("change", () => {
    if (maxDate.value && minDate.value) {
      minDate.setAttribute("max", maxDate.value);
      minDate.checkValidity();
      maxDate.setAttribute("min", minDate.value);
      maxDate.checkValidity();
    } else {
      minDate.removeAttribute("max");
      minDate.checkValidity();
      maxDate.removeAttribute("min");
      maxDate.checkValidity();
    }
  });
});

// Submit multiple forms and send request with JSONified input
const filterSubmit = document.getElementById("filter_submit_button");
filterSubmit.addEventListener("click", async function updateTransactions() {
  // Object which will be filled with filter parameters and passed in the request
  const inputs = {};

  // loop over all filter forms and extract inputs from each one
  const filterForms = document.querySelectorAll("form.filter");
  [...filterForms].forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const formData = new FormData(form);

      // Crate object for input values
      if (form.name === "amount" || form.name === "date") {
        const localInputs = {};
        formData.forEach((value, key) => (localInputs[key] = value));
        inputs[form.name] = localInputs;
        // Create an array for checkbox values
      } else {
        const localInputs = [];
        formData.forEach((value, key) => localInputs.push(key));
        inputs[form.name] = localInputs;
      }
    });
    form.requestSubmit();
  });

  user.transactions = await fetch("/api/transactions/fetch", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(inputs),
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    })
    .then((data) => data.transactions);

  reloadWindows();
});

// Submit multiple forms and send request with JSONified input
const uploadSubmit = document.getElementById("import_submit_button");
uploadSubmit.addEventListener("click", async function uploadStatements() {
  // Object which will be filled with filter parameters and passed in the request
  let allData = new FormData();

  // loop over all filter forms and extract inputs from each one
  const importForms = document.querySelectorAll("form.import");
  [...importForms].forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();

      const importData = new FormData(form);
      for (let [key, file] of importData) {
        allData.append(key, file);
      }
    });
    form.requestSubmit();
  });

  let responseStatus = 0;
  const uploadResults = await fetch("/api/transactions/upload", {
    method: "POST", // *GET, POST, PUT, DELETE, etc.
    mode: "cors", // no-cors, *cors, same-origin
    credentials: "same-origin", // include, *same-origin, omit
    headers: {
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: allData, // body data type must match "Content-Type" header
  })
    .then((response) => {
      if (!response.ok && response.status != 400 && response.status != 415)
        throw new Error(`HTTP error! Status: ${response.status}`);
      responseStatus = response.status;
      return response.json();
    })
    .then((data) => data);

  showUploadModal(responseStatus, uploadResults);
});

async function updateFilters() {
  // Fetch filter data based on user's transactions from server
  const filters = await fetch("/api/transactions/filters", {
    method: "GET", // *GET, POST, PUT, DELETE, etc.
    mode: "cors", // no-cors, *cors, same-origin
    credentials: "same-origin", // include, *same-origin, omit
    headers: {
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
  }).then((response) => {
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    return response.json();
  });

  // Save filters into a global variable with additional 'empty' category
  user.categories = [...filters.category, null];
  user.banks = filters.bank;
  user.currencies = filters.base_currency;
}

function showUploadModal(responseStatus, uploadResults) {
  const backgroundDim = document.getElementsByClassName("dim-background")[0];
  backgroundDim.classList.remove("inactive");
  const modal = document.getElementsByClassName("modal")[0];
  modal.classList.remove("inactive");

  const modalHeader = modal.getElementsByClassName("modal-header")[0];
  modalHeader.textContent = "Statement upload results";
  const modalContent = modal.getElementsByClassName("modal-content")[0];

  while (modalContent.firstChild) {
    modalContent.removeChild(modalContent.lastChild);
  }

  if (uploadResults.amount) {
    const p = document.createElement("p");
    p.textContent = `${uploadResults.amount} transactions were loaded successfully.`;
    modalContent.append(p);
  }

  // Print any attached messages from server
  if (uploadResults.info) {
    const p = document.createElement("p");
    p.textContent = uploadResults.info;

    modalContent.append(p);
  }

  if (responseStatus == 201 || responseStatus == 206) {
    const p = document.createElement("p");
    p.textContent =
      "Following statements were uploaded and converted succesfully:";

    const ul = document.createElement("ul");
    for (let [statementFilename, bank] of Object.entries(
      uploadResults.success
    )) {
      const li = document.createElement("li");
      li.textContent = `${bank}: ${statementFilename}`;
      ul.append(li);
    }
    modalContent.append(p, ul);
  }
  if (responseStatus == 206 || responseStatus == 415) {
    const p = document.createElement("p");
    p.textContent = "Following statements were discarded due to an error:";

    const ul = document.createElement("ul");
    for (let [statementFilename, bank] of Object.entries(
      uploadResults.failed
    )) {
      const li = document.createElement("li");
      li.textContent = `${bank}: ${statementFilename}`;
      ul.append(li);
    }
    modalContent.append(p, ul);
  }
}

function reloadWindows() {
  reloadForms();
  reloadTable(transactionsTable);
  reloadCategoryChart(categoryChart);
  reloadMonthlyChart(monthlyChart);
}

async function reloadForms() {
  await updateFilters();

  renderDropdowns(user.categories, "category", "category-dynamic-dropdown");
  renderDropdowns(user.banks, "bank", "bank-dynamic-dropdown");

  renderCheckboxes(user.categories, "category-dynamic-checkboxes");
  renderCheckboxes(user.banks, "bank-dynamic-checkboxes");
  renderCheckboxes(user.currencies, "currency-dynamic-checkboxes");
}

function logOut() {
  window.location.href = "/logout";
  sessionStorage.clear();
}

window.addEventListener("load", async () => {
  // Load storage into temporary arrays
  if (sessionStorage.getItem("transactions") != null)
    user.transactions = JSON.parse(sessionStorage.getItem("transactions"));
  if (sessionStorage.getItem("deletedTransactions") != null)
    user.deletedTransactions = JSON.parse(
      sessionStorage.getItem("deletedTransactions")
    );

  await updateFilters();
  reloadWindows();
});

window.addEventListener("beforeunload", () => {
  // Update session storage
  sessionStorage.setItem("transactions", JSON.stringify(user.transactions));
  sessionStorage.setItem(
    "deletedTransactions",
    JSON.stringify(user.deletedTransactions)
  );
});
