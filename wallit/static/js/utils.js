import {
  html,
  render,
  useState,
} from "https://unpkg.com/htm/preact/standalone.module.js";
import { Fragment } from "https://unpkg.com/preact?module";

const accountSettingsButton = document.getElementById("settings_button");
accountSettingsButton.addEventListener("click", (event) => {
  render(
    html`<${SettingsModal} user=${user} />`,
    document.getElementById("settings")
  );
});

function SettingsModal(props) {
  const [accountConfirmation, setAccountConfirmation] = useState(false);
  const toggleAccount = () => setAccountConfirmation((prev) => !prev);

  const [passwordConfirmation, setPasswordConfirmation] = useState(false);
  const togglePassword = () => setPasswordConfirmation((prev) => !prev);

  const [currentAction, setCurrentAction] = useState(null);
  const [actionConfirmation, setActionConfirmation] = useState(false);
  const toggleAction = () => {
    setActionConfirmation((prev) => !prev);
  };

  const toggleOffDialogs = () => {
    setAccountConfirmation(false);
    setPasswordConfirmation(false);
    setActionConfirmation(false);
  };

  return html`
    <div class="dim-background">
      <div class="modal">
        <div class="modal-header">
          <h5>Settings</h5>
          <span
            class="material-symbols-rounded custom-small-icon"
            onclick=${() => {
              render(null, document.getElementById("settings"));
            }}
            >close</span
          >
        </div>
        <div class="settings">
          <div class="settings-paragraph">
            <div class="settings-subheader">
              <h6>Account details</h6>
            </div>
            <form name="modify_user">
              <div class="settings-subcontent">
                <input
                  id="email"
                  name="email"
                  placeholder=${props.user.user_details.email}
                  type="email"
                  value=""
                  disabled
                />
                <input
                  id="first_name"
                  name="first_name"
                  placeholder=${props.user.user_details.first_name}
                  type="text"
                  value=""
                />
                <input
                  id="surname"
                  name="surname"
                  placeholder=${props.user.user_details.last_name}
                  type="text"
                  value=""
                />
                <${DynamicListDropdown}
                  name=${"main_currency"}
                  items=${session.currencies}
                  startingItem=${props.user.main_currency}
                />
                <div class="button-list-centered">
                  ${!accountConfirmation
                    ? html`<button
                        type="button"
                        class="button-std medium"
                        onclick=${() => {
                          toggleOffDialogs();
                          toggleAccount();
                          setCurrentAction(() => modifyUser);
                        }}
                      >
                        Apply
                      </button>`
                    : null}
                  ${accountConfirmation
                    ? html`<${ConfirmationDialog}
                        toggleConfirmation=${toggleAccount}
                        currentAction=${currentAction}
                      /> `
                    : null}
                </div>
              </div>
            </form>
          </div>
          <div class="settings-paragraph">
            <div class="settings-subheader">
              <h6>Password reset</h6>
            </div>
            <form name="modify_user">
              <div class="settings-subcontent">
                <input
                  id="old_password"
                  name="old_password"
                  placeholder="Old password"
                  type="text"
                  value=""
                />
                <input
                  id="new_password"
                  name="new_password"
                  placeholder="New password"
                  type="text"
                  value=""
                />
                <input
                  id="repeat_password"
                  name="repeat_password"
                  placeholder="Repeat password"
                  type="text"
                  value=""
                />
                <div class="button-list-centered">
                  ${!passwordConfirmation
                    ? html`<button
                        type="button"
                        class="button-std medium"
                        onclick=${() => {
                          toggleOffDialogs();
                          togglePassword();
                          setCurrentAction(() => modifyUser);
                        }}
                      >
                        Apply
                      </button>`
                    : null}
                  ${passwordConfirmation
                    ? html`<${ConfirmationDialog}
                        toggleConfirmation=${togglePassword}
                        currentAction=${currentAction}
                      /> `
                    : null}
                </div>
              </div>
            </form>
          </div>
          <div class="settings-paragraph">
            <div class="settings-subheader">
              <h6>Actions</h6>
            </div>
            <div class="settings-subcontent">
              <div class="button-list-centered">
                ${!actionConfirmation
                  ? html`
                      <button
                        id="delete_transactions"
                        class="button-std medium"
                        onclick=${() => {
                          toggleOffDialogs();
                          toggleAction();
                          setCurrentAction(() => deleteTransactions);
                        }}
                      >
                        Delete all transactions
                      </button>
                      <button
                        id="delete_account"
                        class="button-std medium"
                        onclick=${() => {
                          toggleOffDialogs();
                          toggleAction();
                          setCurrentAction(() => deleteUser);
                        }}
                      >
                        Delete account
                      </button>
                    `
                  : null}
                ${actionConfirmation
                  ? html`<${ConfirmationDialog}
                      toggleConfirmation=${toggleAction}
                      currentAction=${currentAction}
                    /> `
                  : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function ConfirmationDialog(props) {
  return html` <p>Are you sure?</p>
    <button
      type="button"
      class="button-std medium"
      onclick=${() => {
        props.currentAction();
        props.toggleConfirmation();
      }}
    >
      Yes
    </button>
    <button
      type="button"
      class="button-std medium"
      onclick=${props.toggleConfirmation}
    >
      No
    </button>`;
}
export function renderCategoryForms() {
  renderObjectDropdowns(
    user.categories,
    "category",
    "category-dynamic-dropdown"
  );
  renderObjectDropdowns(
    user.categories,
    "category",
    "category-dynamic-dropdown-with-blank",
    undefined,
    true
  );
  renderObjectCheckboxes(user.categories, "category-dynamic-checkboxes");
}

export function renderBankForms() {
  renderObjectDropdowns(user.banks, "bank", "user-bank-dynamic-dropdown");
  renderObjectDropdowns(
    session.banks,
    "bank",
    "session-bank-dynamic-dropdown-with-blank",
    undefined,
    true
  );
  renderObjectCheckboxes(user.banks, "user-bank-dynamic-checkboxes");
}

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
  startingItem = false,
  blankItem = false
) {
  if (blankItem) items = { ...items, ...{ "": { id: "", name: "" } } };

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
      ${props.items.map(
        (item) => html` <option
          value=${item}
          selected=${item === props.startingItem ? true : false}
        >
          ${item}
        </option>`
      )}
    </select>
  `;
}

export function renderListDropdowns(
  items,
  dropdownName,
  parentClass,
  startingItem = false
) {
  // If starting item was given, rearrange the array so the array
  // (and so the generated dropdown) starts with it
  if (startingItem != false && items.includes(startingItem)) {
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

export function renderObjectCheckboxes(items, parentClass, blankItem = false) {
  if (blankItem) items = { ...items, ...{ "": { id: "", name: "" } } };
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

export async function modifyTransaction(id, modifiedColumns) {
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
}

export async function modifyCategory(id, modifiedColumns) {
  const modifiedCategory = await fetch(`/api/categories/${id}/modify`, {
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

  for (let [categoryName, categoryParams] of Object.entries(user.categories)) {
    if (categoryParams.id == id) delete user.categories[categoryName];
  }
  user.categories[modifiedCategory.name] = modifiedCategory;
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
}

async function modifyUser(id, modifiedColumns) {
  console.log("modify user");
}

async function deleteTransactions(userId) {
  console.log("delete transactions");
}

async function deleteUser(id) {
  console.log("delete user");
}
