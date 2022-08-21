import { Grid, h } from "https://unpkg.com/gridjs?module";
import {
  categoryChart,
  reloadCategoryChart,
  monthlyChart,
  reloadMonthlyChart,
} from "./chartjs.js";

export function reloadTable(table) {
  table
    .updateConfig({
      data: () => {
        // Keys to be retained in a new array passed to the Table
        const keysNeeded = [
          "id",
          "info",
          "title",
          "amount",
          "base_amount",
          "base_currency",
          "category",
          "date",
          "place",
          "bank",
          "creation_date",
        ];

        let formattedTransactions = structuredClone(transactions);

        for (let transaction of formattedTransactions) {
          for (let key of Object.keys(transaction)) {
            if (!keysNeeded.includes(key)) delete transaction[key];
            if (key.includes("date"))
              transaction[key] = transaction[key].split("T")[0];
          }
        }

        return formattedTransactions;
      },
    })
    .forceRender();
}

const editableCellAttributes = (cell, row, column) => {
  if (row) {
    return { contentEditable: "true", "data-id": row.cells[0].data };
  } else {
    return {};
  }
};

const createCategoryDropdown = (cell, row, column) => {
  // Disgustingly ugly, but works.
  let options = [];

  let currentCategory = h(
    "option",
    { value: row.cells[6].data },
    row.cells[6].data
  );
  options.push(currentCategory);

  // Delete duplicate corresponding to above option element from temporary category array
  const tempCategories = [...categories];
  const index = tempCategories.indexOf(row.cells[6].data);
  if (index > -1) tempCategories.splice(index, 1);

  // Create the rest of possible categories
  for (let category of tempCategories) {
    let option = h("option", { value: category }, category);
    options.push(option);
  }

  const select = h(
    "select",
    {
      name: "category",
      onchange: async (event) => {
        const formData = new FormData(event.target.parentNode);
        await modifyTransaction({
          id: row.cells[0].data,
          category:
            formData.get("category") === "" ? null : formData.get("category"),
        });
        reloadCategoryChart(categoryChart);
      },
    },
    options
  );

  const form = h(
    "form",
    {
      name: "category_change",
      onsubmit: () => {
        preventDefault();
      },
    },
    select
  );

  return form;
};

const createActionButtons = () => {
  const span = h(
    "span",
    {
      className: "material-symbols-rounded custom-small-icon",
    },
    "delete_forever"
  );

  const deletionButton = h(
    "button",
    {
      className: "button-table",
      title: "Delete transaction",
      onClick: async (event) => {
        const transactionId = event.target
          .closest("td")
          .getAttribute("data-id");

        await deleteTransaction(transactionId);
        reloadCategoryChart(categoryChart);
        event.target.closest("tr").classList.add("hidden");

        const undoDeletionButton = document.getElementById("undo_deletion");
        undoDeletionButton.classList.remove("hidden");
      },
    },
    span
  );

  const secondButton = h(
    "button",
    {
      className: "button-table",
      onClick: () => alert(`Transaction 2nd operation`),
    },
    h(
      "span",
      {
        className: "material-symbols-rounded custom-small-icon",
      },
      "sync"
    )
  );

  return [deletionButton, secondButton];
};

async function deleteTransaction(id) {
  await fetch(`/api/transactions/${id}/delete`, {
    method: "DELETE",
    mode: "cors", // no-cors, *cors, same-origin
    credentials: "same-origin", // include, *same-origin, omit
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
  }).then((response) => {
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

    // Pop the transactions element with specified id into a deletedTransactions array
    for (let i = 0; i < transactions.length; i++) {
      if (transactions[i].id == id)
        deletedTransactions.push(transactions.splice(i, 1)[0]);
    }
  });
}

async function addTransaction(transaction) {
  const newTransactionId = await fetch("/api/transactions/add", {
    method: "POST",
    mode: "cors", // no-cors, *cors, same-origin
    credentials: "same-origin", // include, *same-origin, omit
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(transaction),
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    })
    .then((data) => {
      return data.id;
    });

  return newTransactionId;
}

async function modifyTransaction({ id, ...modifiedColumns }) {
  await fetch(`/api/transactions/${id}/modify`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(modifiedColumns),
  }).then((response) => {
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
  });

  const modifiedTransaction = transactions.find(
    (transaction) => transaction.id == id
  );

  for (let [columnName, columnValue] of Object.entries(modifiedColumns))
    modifiedTransaction[columnName] = columnValue;
}

const undoDeletionButton = document.getElementById("undo_deletion");
undoDeletionButton.addEventListener("click", async () => {
  if (deletedTransactions.length > 0) {
    const transaction = deletedTransactions[deletedTransactions.length - 1];

    // Find table cells corresponding to the last deleted transaction
    const transactionDataCells = document.querySelectorAll(
      `td[data-id="${transaction.id}"]`
    );

    // Send request to insert transaction
    const newTransactionId = await addTransaction(transaction);
    // Server responds with a new Id for transaction after successful insertion
    transaction.id = newTransactionId;

    transactions.push(transaction);
    deletedTransactions.pop();

    // Change data-attributes to correct transactionId
    [...transactionDataCells].forEach((dataCell) => {
      dataCell.setAttribute("data-id", newTransactionId);
    });
    // Show the table row corresponding to transaction dataCells
    const transactionRow = transactionDataCells[0].closest("tr");
    transactionRow.classList.remove("hidden");

    reloadCategoryChart(categoryChart);
  }

  if (deletedTransactions.length == 0)
    undoDeletionButton.classList.add("hidden");
});

let oldValue;

const tableBody = document.getElementById("transactionTable");
tableBody.addEventListener("focusin", (event) => {
  if (event.target.contentEditable == "true")
    oldValue = event.target.textContent;
});

tableBody.addEventListener("focusout", async (event) => {
  if (event.target.contentEditable == "true") {
    if (event.target.textContent != oldValue) {
      const transactionId = event.target.dataset.id;
      const columnName = event.target.dataset.columnId;
      const columnValue = event.target.textContent;

      modifyTransaction({
        id: event.target.dataset.id,
        [columnName]: columnValue,
      });
    }
  }
  oldValue = undefined;
});

tableBody.addEventListener("keydown", (event) => {
  if (event.target.contentEditable == "true") {
    if (event.key == "Escape") {
      event.target.textContent = oldValue;
      event.target.blur();
    } else if (event.key === "Enter" || event.key === "Tab") {
      event.preventDefault();
      event.target.blur();
    }
  }
});

export const transactionsTable = new Grid({
  columns: [
    { id: "id", hidden: true, search: { enabled: true } },
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
    {
      id: "base_amount",
      name: "Base amount",
      search: { enabled: false },
      formatter: (cell, row) => {
        return `${cell} ${row.cells[5].data}`;
      },
    },
    { id: "base_currency", name: "Base currency", hidden: true },
    {
      id: "category",
      name: "Category",
      sort: { enabled: false },
      formatter: createCategoryDropdown,
    },
    { id: "date", name: "Date", search: { enabled: false } },
    {
      id: "place",
      name: "Place",
      sort: { enabled: false },
      attributes: editableCellAttributes,
    },
    { id: "bank", name: "Bank" },
    { id: "creation_date", name: "Creation date", search: { enabled: false } },
    {
      id: "actions",
      name: "Actions",
      search: { enabled: false },
      sort: { enabled: false },
      attributes: (cell, row) => {
        if (row) {
          return { "data-id": row.cells[0].data };
        } else {
          return {};
        }
      },
      formatter: createActionButtons,
    },
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
    td: "custom-td",
    th: "custom-th",
    loading: "custom-loading",
  },
}).render(document.getElementById("transactionTable"));
