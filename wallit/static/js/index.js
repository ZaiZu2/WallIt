let transactions = [];

const modalButton = document.getElementById("modal-button");
modalButton.addEventListener("click", () => {
  modal = document.getElementsByClassName("modal")[0];
  modal.classList.add("inactive");
  backgroundDim = document.getElementsByClassName("dim-background")[0];
  backgroundDim.classList.add("inactive");
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

  // Request from server
  transactions = await fetch("/api/transactions/fetch", {
    method: "POST", // *GET, POST, PUT, DELETE, etc.
    mode: "cors", // no-cors, *cors, same-origin
    credentials: "same-origin", // include, *same-origin, omit
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(inputs), // body data type must match "Content-Type" header
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    })
    .then((data) => {
      for (let transaction of data.transactions) {
        transaction.date = new Date(transaction.date);
        transaction.creation_date = new Date(transaction.creation_date);
      }
      return data.transactions;
    })
    .catch((error) => console.error(error));

  reloadWindows(transactions);
});

// Submit multiple forms and send request with JSONified input
const uploadSubmit = document.getElementById("import_submit_button");
uploadSubmit.addEventListener("click", async function updateTransactions() {
  // Object which will be filled with filter parameters and passed in the request
  let allData = new FormData();

  // loop over all filter forms and extract inputs from each one
  const importForms = document.querySelectorAll("form.import");
  [...importForms].forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();

      const importData = new FormData(form);
      for ([key, file] of importData) {
        allData.append(key, file);
      }
    });
    form.requestSubmit();
  });

  // Request from server
  responseStatus = 0;
  uploadResults = await fetch("/api/transactions/upload", {
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
    .then((data) => data)
    .catch((error) => console.error(error));

  showUploadModal(responseStatus, uploadResults);
});

async function updateFilters() {
  // Fetch filter data based on user's transactions from server
  const filters = await fetch((url = "/api/transactions/filters"), {
    method: "GET", // *GET, POST, PUT, DELETE, etc.
    mode: "cors", // no-cors, *cors, same-origin
    credentials: "same-origin", // include, *same-origin, omit
    headers: {
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    })
    .catch((error) => console.error(error));

  // Find all filter forms with checkboxes
  checkboxFields = document.querySelectorAll(".filter > .form-set");
  // Define filter categories which should display and in what order
  renderOrder = ["base_currency", "category", "bank"];

  // Dynamically create checkboxes for all the found filter categories
  for (let [i, filterCategory] of Object.entries(renderOrder)) {
    temporaryFields = [];

    for (let parameter of filters[filterCategory]) {
      const input = document.createElement("input");
      input.setAttribute("type", "checkbox");
      input.setAttribute("name", parameter);
      input.setAttribute("id", parameter);

      const label = document.createElement("label");
      label.setAttribute("for", parameter);
      label.textContent = parameter;

      temporaryFields.push(input);
      temporaryFields.push(label);
    }
    if (temporaryFields.length == false) {
      const message = document.createElement("p");
      message.textContent = "No filters available";
      temporaryFields.push(message);
    }
    checkboxFields[i].append(...temporaryFields);
  }
}

// Format Transaction (structure used by Category Chart
function calculateCategoryWeights(transactions) {
  let categoryWeights = {};

  for (let transaction of transactions) {
    if (!Object.keys(categoryWeights).includes(transaction.category)) {
      categoryWeights[transaction.category] = transaction.amount;
    } else {
      categoryWeights[transaction.category] += transaction.amount;
    }
  }

  // Round up any floating point errors
  for (let [categoryName, categoryWeight] of Object.entries(categoryWeights)) {
    categoryWeights[categoryName] = Math.round(categoryWeight * 100) / 100;
  }

  return categoryWeights;
}

function reloadTable(transactions) {
  transactionsTable
    .updateConfig({
      data: () => {
        // Keys to be retained in a new array passed to the Table
        keysNeeded = [
          "info",
          "title",
          "amount",
          "base_amount",
          "category",
          "date",
          "place",
          "bank",
          "creation_date",
        ];

        formattedTransactions2 = structuredClone(transactions);

        for (let transaction of formattedTransactions2) {
          for (let key of Object.keys(transaction)) {
            if (!keysNeeded.includes(key)) delete transaction[key];
            if (transaction[key] instanceof Date)
              transaction[key] = transaction[key].toISOString().split("T")[0];
            if (key == "base_amount")
              transaction[key] =
                transaction[key] + " " + transaction["base_currency"];
          }
        }

        return formattedTransactions2;
      },
    })
    .forceRender();
}

const editableCellAttributes = (data, row, col) => {
  if (row) {
    return { contentEditable: "true", "data-element-id": row.cells[0].data };
  } else {
    return {};
  }
};

const transactionsTable = new gridjs.Grid({
  columns: [
    {
      id: "info",
      name: "Name",
      search: { enabled: true },
      sort: { enabled: false },
      attributes: editableCellAttributes,
    },
    {
      id: "title",
      name: "Title",
      search: { enabled: true },
      sort: { enabled: false },
      attributes: editableCellAttributes,
    },
    {
      id: "amount",
      name: "Amount",
      formatter: (cell) => {
        return `${cell} CZK`;
      },
    },
    { id: "base_amount", name: "Base amount", search: { enabled: false } },
    { id: "category", name: "Category" },
    { id: "date", name: "Date", search: { enabled: false } },
    {
      id: "place",
      name: "Place",
      sort: { enabled: false },
      attributes: editableCellAttributes,
    },
    { id: "bank", name: "Bank" },
    { id: "creation_date", name: "Creation date", search: { enabled: false } },
  ],
  data: [],
  width: "auto",
  autoWidth: false,
  search: {
    enabled: true,
  },
  sort: {
    enabled: true,
    multiColumn: true,
  },
  fixedHeader: true,
  height: "400px",
  className: {
    container: "custom-container",
    table: "custom-table",
    tbody: "custom-tbody",
    thead: "custom-thead",
    header: "custom-header",
    footer: "custom-footer",
    td: "custom-td",
    th: "custom-th",
    paginationSummary: "custom-pagination-summary",
    paginationButton: "custom-pagination-button",
    paginationButtonNext: "custom-pagination-button-next",
    paginationButtonCurrent: "custom-pagination-button-current",
    paginationButtonPrev: "custom-pagination-button-prev",
    loading: "custom-loading",
  },
}).render(document.getElementById("transactionTable"));

const ctx = document.getElementById("categoryChart").getContext("2d");
const categoryChart = new Chart(ctx, {
  type: "bar",
  data: {
    labels: [],
    datasets: [
      {
        label: "Spendings",
        data: calculateCategoryWeights(transactions),
        backgroundColor: ["rgba(255, 99, 132, 0.4)"],
        borderColor: ["rgba(255, 99, 132, 1)"],
        borderWidth: 2,
      },
      // {
      //   label: "Spendings",
      //   data: calculateCategoryWeights(transactions),
      //   backgroundColor: [
      //     "rgba(255, 99, 132, 0.4)",
      //     "rgba(54, 162, 235, 0.4)",
      //     "rgba(255, 206, 86, 0.4)",
      //     "rgba(75, 192, 192, 0.4)",
      //     "rgba(153, 102, 255, 0.4)",
      //     "rgba(255, 159, 64, 0.4)",
      //   ],
      //   borderColor: [
      //     "rgba(255, 99, 132, 1)",
      //     "rgba(54, 162, 235, 1)",
      //     "rgba(255, 206, 86, 1)",
      //     "rgba(75, 192, 192, 1)",
      //     "rgba(153, 102, 255, 1)",
      //     "rgba(255, 159, 64, 1)",
      //   ],
      //   borderWidth: 2,
      // },
    ],
  },
  options: {
    responsive: false,
    scales: {
      x: {
        stacked: true,
      },
      y: {
        beginAtZero: true,
      },
    },
  },
});

function reloadChart(chart, dataObj) {
  const labels = Object.keys(arguments[1]);
  chart.data.labels = labels;

  for (let i = 1; i < arguments.length; i++) {
    const data = Object.values(arguments[i]);
    chart.data.datasets[i - 1].data = data;
  }
  chart.update();
}

function showUploadModal(responseStatus, uploadResults) {
  backgroundDim = document.getElementsByClassName("dim-background")[0];
  backgroundDim.classList.remove("inactive");
  modal = document.getElementsByClassName("modal")[0];
  modal.classList.remove("inactive");

  modalHeader = modal.getElementsByClassName("modal-header")[0];
  modalHeader.textContent = "Statement upload results";
  modalContent = modal.getElementsByClassName("modal-content")[0];

  while (modalContent.firstChild) {
    modalContent.removeChild(modalContent.lastChild);
  }

  if (uploadResults.amount) {
    p = document.createElement("p");
    p.textContent = `${uploadResults.amount} transactions were loaded successfully.`;
    modalContent.append(p);
  }

  // Print any attached messages from server
  if (uploadResults.info) {
    p = document.createElement("p");
    p.textContent = uploadResults.info;

    modalContent.append(p);
  }

  if (responseStatus == 201 || responseStatus == 206) {
    p = document.createElement("p");
    p.textContent =
      "Following statements were uploaded and converted succesfully:";

    ul = document.createElement("ul");
    for ([statementFilename, bank] of Object.entries(uploadResults.success)) {
      li = document.createElement("li");
      li.textContent = `${bank}: ${statementFilename}`;
      ul.append(li);
    }
    modalContent.append(p, ul);
  }
  if (responseStatus == 206 || responseStatus == 415) {
    p = document.createElement("p");
    p.textContent = "Following statements were discarded due to an error:";

    ul = document.createElement("ul");
    for ([statementFilename, bank] of Object.entries(uploadResults.failed)) {
      li = document.createElement("li");
      li.textContent = `${bank}: ${statementFilename}`;
      ul.append(li);
    }
    modalContent.append(p, ul);
  }
}

updateFilters();

function reloadWindows(transactions) {
  categoryData = calculateCategoryWeights(transactions);
  reloadChart(categoryChart, categoryData);

  reloadTable(transactions);
}
