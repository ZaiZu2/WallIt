import { Grid, h } from "https://unpkg.com/gridjs?module";

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

const editableCellAttributes = (cell, row, col) => {
  if (row) {
    return { contentEditable: "true", "data-id": row.cells[0].data };
  } else {
    return {};
  }
};

async function deleteTransaction(id) {
  await fetch(`/api/transactions/delete/${id}`, {
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
      formatter: () => {
        return [
          h(
            "button",
            {
              className: "button-table",
              title: "Delete transaction",
              onClick: async (event) => {
                const transactionId = event.target
                  .closest("td")
                  .getAttribute("data-id");
                await deleteTransaction(transactionId);
                event.target.closest("tr").classList.add("hidden");
              },
            },
            h(
              "span",
              {
                className: "material-symbols-rounded custom-small-icon",
              },
              "delete_forever"
            )
          ),
          h(
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
          ),
        ];
      },
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
  }
});
