import {
  html,
  render,
} from "https://unpkg.com/htm/preact/standalone.module.js";
import { Fragment } from "https://unpkg.com/preact?module";

function DynamicObjectDropdown(props) {
  return html`
    <select id=${props.name} name=${props.name}>
      ${Object.values(props.items).map((item) => {
        return html`<option
          value=${item.id}
          selected=${item.name === props.startingItem ? true : false}
        >
          ${item.name}
        </option>`;
      })}
    </select>
  `;
}

export function renderObjectDropdowns(
  items,
  dropdownName,
  parentClass,
  startingItem = ""
) {
  const parentNodes = document.getElementsByClassName(parentClass);
  for (let parentNode of parentNodes)
    render(
      html`<${DynamicObjectDropdown}
        name=${dropdownName}
        items=${items}
        startingItem=${startingItem}
      />`,
      parentNode
    );
}

function DynamicListDropdown(props) {
  return html`
    <select id=${props.name} name=${props.name}>
      ${props.items.map((item) => html`<option value=${item}>${item}</option>`)}
    </select>
  `;
}

export function renderListDropdowns(
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
      html`<${DynamicListDropdown} name=${dropdownName} items=${items} />`,
      parentNode
    );
}

function DynamicObjectCheckboxes(props) {
  return html`
      <${Fragment}>
        ${Object.values(props.items).map((item, id) => {
          return html`
            <input
              type="checkbox"
              name=${item.name}
              value=${item.id}
              id=${props.form + "_" + item.id}
            />
            <label for=${props.form + "_" + item.id}>${item.name}</label>
          `;
        })}
      </${Fragment}>
    `;
}

export function renderObjectCheckboxes(items, parentClass) {
  const parentNodes = document.getElementsByClassName(parentClass);

  for (let i = 0; i < parentNodes.length; i++)
    render(
      html`<${DynamicObjectCheckboxes} form=${`form_${i}`} items=${items} />`,
      parentNodes[i]
    );
}

function DynamicListCheckboxes(props) {
  return html`
      <${Fragment}>
        ${props.items.map((item, id) => {
          return html`
            <input
              type="checkbox"
              name=${item}
              value=${item}
              id=${props.form + "_" + item + "_" + id}
            />
            <label for=${props.form + "_" + item + "_" + id}>${item}</label>
          `;
        })}
      </${Fragment}>
    `;
}

export function renderListCheckboxes(items, parentClass) {
  const parentNodes = document.getElementsByClassName(parentClass);

  for (let i = 0; i < parentNodes.length; i++)
    render(
      html`<${DynamicListCheckboxes} form=${`form_${i}`} items=${items} />`,
      parentNodes[i]
    );
}

export async function deleteTransaction(id) {
  const deletedTransaction = await fetch(`/api/transactions/${id}/delete`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    })
    .then((data) => data);

  // Pop the transactions element with specified id into a deletedTransactions array
  const deletedId = user.transactions.findIndex(
    (transaction) => transaction.id == id
  );
  user.deletedTransactions.push(user.transactions.splice(deletedId, 1)[0]);
}

export async function addTransaction(transaction) {
  const newTransaction = await fetch("/api/transactions/add", {
    method: "POST",
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
    .then((data) => data.transactions);

  user.transactions.unshift(newTransaction);
  return newTransaction.id;
}

export async function modifyTransaction({ id, ...modifiedColumns }) {
  const modifiedTransaction = await fetch(`/api/transactions/${id}/modify`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(modifiedColumns),
  })
    .then((response) => {
      if (!response.ok)
        throw new Error(`HTTP error! Status: ${response.status}`);
      return response.json();
    })
    .then((data) => data.transactions);

  const oldId = user.transactions.findIndex(
    (transaction) => transaction.id === id
  );
  if (oldId != -1) user.transactions[oldId] = modifiedTransaction;
}

export async function addCategory(category) {
  const newCategory = await fetch("/api/categories/add", {
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
  renderListDropdowns(
    Object.keys(user.categories),
    "category",
    "category-dynamic-dropdown"
  );
  renderListCheckboxes(
    Object.keys(user.categories),
    "category-dynamic-checkboxes"
  );
}

export async function modifyCategory(id, ...modifiedColumns) {
  const newCategory = await fetch(`/api/categories/${id}/modify`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(modifiedColumns),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => data);

  user.categories[newCategory.name] = newCategory;

  renderListDropdowns(
    Object.keys(user.categories),
    "category",
    "category-dynamic-dropdown"
  );
  renderListCheckboxes(
    Object.keys(user.categories),
    "category-dynamic-checkboxes"
  );
}

export async function deleteCategories(categoryIds) {
  const deletedCategories = await fetch(`/api/categories/delete`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(categoryIds),
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

  renderObjectDropdowns(
    user.categories,
    "category",
    "category-dynamic-dropdown"
  );
  renderObjectCheckboxes(user.categories, "category-dynamic-checkboxes");
}
