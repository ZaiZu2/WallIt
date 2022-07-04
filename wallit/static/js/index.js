let transactions = [];

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

const toggleCollapsible = function (node) {
  if (node.style.maxHeight) {
    node.style.maxHeight = null;
  } else {
    node.style.maxHeight = node.scrollHeight + "px";
  }
};

// Allows filtering buttons to extend FILTER menu to make it responsive
const filterButtons = document.querySelectorAll(".filter-button-list button");
filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    button.classList.toggle("active");

    // If button is switched OFF, hide corresponding FILTER menu
    // If button is switched ON, show corresponding FILTER menu
    const content = document.getElementsByName(button.id.substring(6))[0];
    content.classList.toggle("active");
    if (content.style.maxHeight) content.style.maxHeight = null;
    else content.style.maxHeight = content.scrollHeight + "px";

    //  If any of FilterButtons is OFF, hide the SUBMIT button
    //  If any of FilterButtons is ON, show the SUBMIT button
    let isActive = false;
    for (const node of [...button.parentNode.children]) {
      if (node.classList.contains("active")) {
        isActive = true;
        break;
      }
    }
    const submitButton = document.getElementById("submitContent");
    if (isActive === true) {
      submitButton.classList.add("active");
      submitButton.style.maxHeight = submitButton.scrollHeight + "px";
    } else {
      submitButton.classList.remove("active");
      submitButton.style.maxHeight = null;
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
const filterSubmit = document.getElementById("filterSubmit");
filterSubmit.addEventListener("click", async function updateTransactions() {
  // Object which will be filled with filter parameters and passed in the request
  const inputs = {};

  // loop over all filter forms and extract inputs from each one
  const filterForms = document.querySelectorAll("form.filter-input");
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
  transactions = await fetch("/api/filters/apply", {
    method: "POST", // *GET, POST, PUT, DELETE, etc.
    mode: "cors", // no-cors, *cors, same-origin
    credentials: "same-origin", // include, *same-origin, omit
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(inputs), // body data type must match "Content-Type" header
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    })
    .catch((error) => console.error(error));

  transactions = transactions.transactions;
  for (let transaction of transactions) {
    transaction.date = new Date(transaction.date);
  }

  reloadWindows(transactions);
});

async function updateFilters() {
  // Fetch filter data based on user's transactions from server
  const filters = await fetch((url = "/api/filters/fetch"), {
    method: "GET", // *GET, POST, PUT, DELETE, etc.
    mode: "cors", // no-cors, *cors, same-origin
    credentials: "same-origin", // include, *same-origin, omit
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    })
    .catch((error) => console.error(error));

  // Find all filter forms with checkboxes
  targetDivs = document.querySelectorAll(".filter-input .filter-set");
  // Define filter categories which should display and in what order
  renderOrder = ["base_currency", "category", "bank"];

  // Dynamically create checkboxes for all the found filter categories
  for (let [i, filterCategory] of Object.entries(renderOrder)) {
    for (let parameter of filters[filterCategory]) {
      const input = document.createElement("input");
      input.setAttribute("type", "checkbox");
      input.setAttribute("name", parameter);
      input.setAttribute("id", parameter);

      const label = document.createElement("label");
      label.setAttribute("for", parameter);
      label.textContent = parameter;

      targetDivs[i].appendChild(input);
      targetDivs[i].appendChild(label);
    }
  }
}

// Format Transaction data into structure used by Category Chart
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
          "category",
          "date",
          "place",
          "bank",
        ];
        // Deep copy of queried transactions
        formattedTransactions = structuredClone(transactions);

        // Delete keys which are not used
        for (let transaction of formattedTransactions) {
          for (let key of Object.keys(transaction)) {
            if (!keysNeeded.includes(key)) delete transaction[key];
            if (transaction[key] instanceof Date)
              transaction.date = `${transaction.date.getFullYear()}/${
                transaction.date.getMonth() + 1
              }/${transaction.date.getDate()}`;
          }
        }
        return formattedTransactions;
      },
    })
    .forceRender();
}

const transactionsTable = new gridjs.Grid({
  columns: [
    {
      id: "info",
      name: "Name",
      search: { enabled: true },
      sort: { enabled: false },
    },
    {
      id: "title",
      name: "Title",
      search: { enabled: true },
      sort: { enabled: false },
    },
    {
      id: "amount",
      name: "Amount",
      formatter: (cell) => {
        return `${cell} CZK`;
      },
    },
    { id: "category", name: "Category" },
    { id: "date", name: "Date" },
    { id: "place", name: "Place" },
    { id: "bank", name: "Bank" },
  ],
  data: [],
  width: "1000px",
  autoWidth: false,
  search: {
    enabled: true,
  },
  sort: {
    enabled: true,
    multiColumn: true,
  },
  fixedHeader: true,
  height: "350px",
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
      {
        label: "Spendings",
        data: calculateCategoryWeights(transactions),
        backgroundColor: [
          "rgba(255, 99, 132, 0.4)",
          "rgba(54, 162, 235, 0.4)",
          "rgba(255, 206, 86, 0.4)",
          "rgba(75, 192, 192, 0.4)",
          "rgba(153, 102, 255, 0.4)",
          "rgba(255, 159, 64, 0.4)",
        ],
        borderColor: [
          "rgba(255, 99, 132, 1)",
          "rgba(54, 162, 235, 1)",
          "rgba(255, 206, 86, 1)",
          "rgba(75, 192, 192, 1)",
          "rgba(153, 102, 255, 1)",
          "rgba(255, 159, 64, 1)",
        ],
        borderWidth: 2,
      },
    ],
  },
  options: {
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

updateFilters();

function reloadWindows(transactions) {
  categoryData = calculateCategoryWeights(transactions);
  reloadChart(categoryChart, categoryData);

  reloadTable(transactions);
}
