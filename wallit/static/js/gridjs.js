export function reloadTable(table, transactions) {
  table
    .updateConfig({
      data: () => {
        // Keys to be retained in a new array passed to the Table
        const keysNeeded = [
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

export const editableCellAttributes = (data, row, col) => {
  if (row) {
    return { contentEditable: "true", "data-element-id": row.cells[0].data };
  } else {
    return {};
  }
};

export const transactionsTable = new gridjs.Grid({
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
    {
      id: "base_amount",
      name: "Base amount",
      search: { enabled: false },
      formatter: (cell, row) => {
        return `${cell} ${row.cells[4].data}`;
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
