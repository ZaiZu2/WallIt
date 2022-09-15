import { Grid, h } from "https://unpkg.com/gridjs?module";
import {
  html,
  render,
} from "https://unpkg.com/htm/preact/standalone.module.js";
import {
  categoryChart,
  reloadCategoryChart,
  monthlyChart,
  reloadMonthlyChart,
} from "./chartjs.js";
import {
  addTransaction,
  deleteTransaction,
  modifyTransaction,
} from "./utils.js";

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

        let formattedTransactions = structuredClone(user.transactions);

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

function TableDropdown(props) {
  return html`
    <form name="${props.name + "_change"}" onsubmit=${() => preventDefault()}>
      <select
        id=${props.name}
        name=${props.name}
        onInput=${async (event) => {
          const formData = new FormData(event.target.parentNode);
          await modifyTransaction({
            id: props.transactionId,
            [props.name]:
              formData.get(props.name) === "" ? null : formData.get(props.name),
          });
          reloadCategoryChart(categoryChart);
        }}
      >
        ${Object.values(props.items).map((item) => {
          return html`<option
            value=${item.id}
            selected=${item.name === props.startingItem ? true : false}
          >
            ${item.name}
          </option>`;
        })}
      </select>
    </form>
  `;
}

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

const undoDeletionButton = document.getElementById("undo_deletion");
undoDeletionButton.addEventListener("click", async () => {
  if (user.deletedTransactions.length > 0) {
    const transaction =
      user.deletedTransactions[user.deletedTransactions.length - 1];

    // Find table cells corresponding to the last deleted transaction
    const transactionDataCells = document.querySelectorAll(
      `td[data-id="${transaction.id}"]`
    );

    const newTransactionId = await addTransaction(transaction);
    user.deletedTransactions.pop();

    // Change data-attributes to correct transactionId
    [...transactionDataCells].forEach((dataCell) => {
      dataCell.setAttribute("data-id", newTransactionId);
    });
    // Show the table row corresponding to transaction dataCells
    const transactionRow = transactionDataCells[0].closest("tr");
    transactionRow.classList.remove("hidden");

    reloadCategoryChart(categoryChart);
  }

  if (user.deletedTransactions.length == 0)
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
      const transactionId = parseInt(event.target.dataset.id);
      const columnName = event.target.dataset.columnId;
      const columnValue = event.target.textContent;

      modifyTransaction({
        id: transactionId,
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
      // formatter: createCategoryDropdown,
      formatter: (cell, row) => {
        const noCategory = { empty: { id: "", name: "" } };

        return html`<${TableDropdown}
          name="category"
          items=${{ ...user.categories, ...noCategory }}
          startingItem=${row.cells[6].data ? row.cells[6].data : ""}
          transactionId=${row.cells[0].data}
        />`;
      },
    },
    { id: "date", name: "Date", search: { enabled: false } },
    {
      id: "place",
      name: "Place",
      sort: { enabled: false },
      attributes: editableCellAttributes,
    },
    {
      id: "bank",
      name: "Bank",
      formatter: (cell, row) => {
        const noBank = { empty: { id: "", name: "" } };

        return html`<${TableDropdown}
          name="bank"
          items=${{ ...session.banks, ...noBank }}
          startingItem=${row.cells[9].data ? row.cells[9].data : ""}
          transactionId=${row.cells[0].data}
        />`;
      },
    },
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
