import {
  html,
  render,
  useState,
} from "https://unpkg.com/htm/preact/standalone.module.js";
import { DynamicListDropdown } from "./components.js";
import {
  deleteTransactions,
  modifyUser,
  changePassword,
  deleteUser,
} from "./utils.js";

const accountSettingsButton = document.getElementById("settings_button");
accountSettingsButton.addEventListener("click", (event) => {
  render(
    html`<${SettingsModal} user=${user} />`,
    document.getElementById("settings")
  );
});

export function SettingsModal(props) {
  return html`
    <div class="dim-background">
      <div class="modal">
        <div class="modal-header">
          <h5>Settings</h5>
          <span
            class="material-symbols-rounded custom-small-icon close-icon"
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
            <${ModifyAccountForm} userDetails=${user.user_details} />
          </div>
          <div class="settings-paragraph">
            <div class="settings-subheader">
              <h6>Password reset</h6>
            </div>
            <${ModifyPasswordForm} />
          </div>
          <div class="settings-paragraph">
            <div class="settings-subheader">
              <h6>Actions</h6>
            </div>
            <${ActionButtons} />
          </div>
        </div>
      </div>
    </div>
  `;
}

function ModifyAccountForm(props) {
  const [accountForm, updateAccountForm] = useState({
    username: "",
    first_name: "",
    last_name: "",
    main_currency: "",
  });
  const [userFeedback, updateUserFeedback] = useState([]);
  const [dialogState, setDialogState] = useState(false);
  const [feedback, setFeedback] = useState("");

  const toggleDialog = () => setDialogState((prev) => !prev);

  const isFormEmpty = () => {
    for (let value of Object.values(accountForm)) if (value) return false;
    return true;
  };

  const handleAccountChange = (event) => {
    const { name, value } = event.target;
    updateAccountForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAccountSubmit = (event) => {
    event.preventDefault();
    toggleDialog();
    updateUserFeedback([]);

    let modifiedColumns = {};
    for (let [name, value] of Object.entries(accountForm)) {
      if (value != false) modifiedColumns[name] = value;
    }

    if (Object.keys(modifiedColumns).length !== 0)
      modifyUser(props.userDetails.id, modifiedColumns);
  };

  const printFeedback = () => {
    return html`${userFeedback.map((message) => html`<p>${message}</p>`)}`;
  };

  return html` <form onsubmit="${handleAccountSubmit}">
    <div class="settings-subcontent">
      <div class="settings-grid">
        <label for="email" class="label-horizontal">E-mail</label>
        <input
          id="email"
          name="email"
          placeholder=${props.userDetails.email}
          type="email"
          readonly
        />
        <label for="username" class="label-horizontal">Username</label>
        <input
          name="username"
          placeholder=${props.userDetails.username}
          type="text"
          value=${accountForm.username}
          oninput="${handleAccountChange}"
        />
        <label for="first_name" class="label-horizontal">First name</label>
        <input
          name="first_name"
          placeholder=${props.userDetails.first_name}
          type="text"
          value=${accountForm.first_name}
          oninput="${handleAccountChange}"
        />
        <label for="last_name" class="label-horizontal">Last name</label>
        <input
          name="last_name"
          placeholder=${props.userDetails.last_name}
          type="text"
          value=${accountForm.last_name}
          oninput="${handleAccountChange}"
        />
        <label for="main_currency" class="label-horizontal">Currency</label>
        <${DynamicListDropdown}
          name=${"main_currency"}
          items=${session.currencies}
          startingItem=${user.main_currency}
          handleChange=${handleAccountChange}
        />
      </div>
      <div class="button-list-centered">
        ${!dialogState
          ? html`<button
              type="button"
              class="button-std medium"
              onclick=${(event) => {
                event.preventDefault(); // Why is this button submiting form???
                toggleDialog();
              }}
              disabled=${isFormEmpty() ? true : false}
            >
              Apply
            </button>`
          : html` <p>Are you sure?</p>
              <button type="submit" class="button-std medium">Yes</button>
              <button
                type="button"
                class="button-std medium"
                onclick=${toggleDialog}
              >
                No
              </button>`}
      </div>
    </div>
    ${feedback ? html`<p class="feedback">${feedback}</p>` : null}
  </form>`;
}

function ModifyPasswordForm() {
  const [passwordForm, updatePasswordForm] = useState({
    old_password: "",
    new_password: "",
    repeat_password: "",
  });
  const [dialogState, setDialogState] = useState(false);
  const [feedback, setFeedback] = useState("");

  const toggleDialog = () => setDialogState((prev) => !prev);

  const isFormFilled = () => {
    for (let value of Object.values(passwordForm)) if (!value) return false;
    return true;
  };

  const handlePasswordChange = (event) => {
    const { name, value } = event.target;
    updatePasswordForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handlePasswordSubmit = (event) => {
    event.preventDefault();
    toggleDialog();

    if (Object.keys(passwordForm).length !== 0)
      changePassword(user.user_details.id, passwordForm);
  };

  return html`<form onsubmit="${handlePasswordSubmit}">
    <div class="settings-subcontent">
      <div class="settings-grid">
        <label for="old_password" class="label-horizontal">Old password</label>
        <input
          name="old_password"
          placeholder="*"
          type="password"
          value=${passwordForm.old_password}
          oninput=${handlePasswordChange}
          required
        />
        <label for="new_password" class="label-horizontal">New password</label>
        <input
          name="new_password"
          placeholder="*"
          type="password"
          value=${passwordForm.new_password}
          oninput=${handlePasswordChange}
          required
        />
        <label for="repeat_password" class="label-horizontal"
          >Repeat password</label
        >
        <input
          name="repeat_password"
          placeholder="*"
          type="password"
          value=${passwordForm.repeat_password}
          oninput=${handlePasswordChange}
          required
        />
      </div>
      <div class="button-list-centered">
        ${!dialogState
          ? html`<button
              type="button"
              class="button-std medium"
              onclick=${(event) => {
                event.preventDefault(); // Why is this button submiting form???
                toggleDialog();
              }}
              disabled=${isFormFilled() ? false : true}
            >
              Apply
            </button>`
          : html` <p>Are you sure?</p>
              <button type="submit" class="button-std medium">Yes</button>
              <button
                type="button"
                class="button-std medium"
                onclick=${toggleDialog}
              >
                No
              </button>`}
      </div>
    </div>
    ${feedback ? html`<p class="feedback">${feedback}</p>` : null}
  </form>`;
}

function ActionButtons() {
  const [dialogState, setDialogState] = useState(false);
  const [currentAction, setCurrentAction] = useState(null);
  const [feedback, setFeedback] = useState("");

  const toggleDialog = () => setDialogState((prev) => !prev);

  const handleDeleteTransactions = () => {
    toggleDialog();
    setCurrentAction(() => deleteTransactions.bind(this, user.user_details.id));
  };

  const handleDeleteUser = () => {
    toggleDialog();
    setCurrentAction(() => deleteUser.bind(this, user.user_details.id));
  };

  const handleConfirmation = async () => {
    setFeedback(await currentAction());
    toggleDialog();
  };

  return html` <div class="settings-subcontent">
      <div class="button-list-centered">
        ${!dialogState
          ? html`
              <button
                id="delete_transactions"
                class="button-std medium"
                onclick=${handleDeleteTransactions}
              >
                Delete all transactions
              </button>
              <button
                id="delete_account"
                class="button-std medium"
                onclick=${handleDeleteUser}
              >
                Delete account
              </button>
            `
          : html` <p>Are you sure?</p>
              <button
                type="button"
                class="button-std medium"
                onclick=${handleConfirmation}
              >
                Yes
              </button>
              <button
                type="button"
                class="button-std medium"
                onclick=${toggleDialog}
              >
                No
              </button>`}
      </div>
    </div>
    ${feedback ? html`<p class="feedback">${feedback}</p>` : null}`;
}
