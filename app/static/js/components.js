import {
  html,
  render,
} from "https://unpkg.com/htm/preact/standalone.module.js";
import { Fragment } from "https://unpkg.com/preact?module";

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

export function DynamicListDropdown(props) {
  return html`
    <select
      id=${props.name}
      name=${props.name}
      onchange=${props.handleChange ? props.handleChange : false}
    >
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
