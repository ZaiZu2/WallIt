import {
  html,
  render,
} from "https://unpkg.com/htm/preact/standalone.module.js";
import { Fragment } from "https://unpkg.com/preact?module";

function DynamicDropdown(props) {
  return html`
    <select id="${props.name}" name="${props.name}">
      ${props.items.map((item) => html`<option value=${item}>${item}</option>`)}
    </select>
  `;
}

export function renderDropdowns(
  items,
  dropdownName,
  parentClass,
  startingItem = ""
) {
  // If starting item was given, rearrange the array so the array
  // (and so the generated dropdown) starts with it
  if (startingItem != "" && items.includes(startingItem)) {
    const startIndex = items.indexOf(startingItem);
    const itemsCopy = [...items];
    for (let i = 0; i < itemsCopy.length; i++) {
      // Rotate array indexes so the startIndex is a new 0 index
      items[i] = itemsCopy[(startIndex + i) % items.length];
    }
  }

  const parentNodes = document.getElementsByClassName(parentClass);
  for (let parentNode of parentNodes)
    render(
      html`<${DynamicDropdown} name=${dropdownName} items=${items} />`,
      parentNode
    );
}

function DynamicCheckboxes(props) {
  return html`
      <${Fragment}>
        ${props.items.map((item, id) => {
          return html`
            <input
              type="checkbox"
              name=${item}
              id=${props.form + "_" + item + "_" + id}
            />
            <label for=${props.form + "_" + item + "_" + id}>${item}</label>
          `;
        })}
      </${Fragment}>
    `;
}

export function renderCheckboxes(items, parentClass) {
  const parentNodes = document.getElementsByClassName(parentClass);

  for (let i = 0; i < parentNodes.length; i++)
    render(
      html`<${DynamicCheckboxes} form=${`form_${i}`} items=${items} />`,
      parentNodes[i]
    );
}

export async function deleteTransaction(id) {
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
    for (let i = 0; i < user.transactions.length; i++) {
      if (user.transactions[i].id == id)
        user.deletedTransactions.push(user.transactions.splice(i, 1)[0]);
    }
  });
}

export async function addTransaction(transaction) {
  const transactionId = await fetch("/api/transactions/add", {
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

  return transactionId;
}

export async function modifyTransaction({ id, ...modifiedColumns }) {
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

  const modifiedTransaction = user.transactions.find(
    (transaction) => transaction.id == id
  );

  for (let [columnName, columnValue] of Object.entries(modifiedColumns))
    modifiedTransaction[columnName] = columnValue;
}

export async function addCategory(category) {
  const newCategory = await fetch("/api/category/add", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(category),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => data);

  user.categories[newCategory.name] = newCategory;
  renderDropdowns(
    Object.keys(user.categories),
    "category",
    "category-dynamic-dropdown"
  );
  renderCheckboxes(Object.keys(user.categories), "category-dynamic-checkboxes");
}

export async function deleteCategories(categoryNames) {
  const deletedCategories = await fetch(`/api/category/delete`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(categoryNames),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => data);

  for (let deletedCategory of deletedCategories)
    delete user.categories[deletedCategory.name];

  renderDropdowns(
    Object.keys(user.categories),
    "category",
    "category-dynamic-dropdown"
  );
  renderCheckboxes(Object.keys(user.categories), "category-dynamic-checkboxes");
}
