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

export async function deleteCategory(id) {
  const deletedCategory = await fetch(`/api/categories/${id}/delete`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => data);

  delete user.categories[deletedCategory.name];
  return deletedCategory;
}

export async function modifyUser(id, modifiedColumns) {
  const modifiedUser = await fetch(`/api/users/${id}/modify`, {
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

  delete modifiedUser[main_currency];
  user.user_details = modifiedUser;
}

export async function changePassword(id, passwordColumns) {
  await fetch(`/api/users/${id}/change_password`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
    body: JSON.stringify(passwordColumns),
  }).then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return response.json();
  });
}

export async function deleteTransactions(id) {
  return await fetch(`/api/users/${id}/delete_transactions`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
  })
    .then((response) => {
      if (!response.ok) {
        return "Error occured";
      }
      return response.json();
    })
    .then((data) => `Deleted ${data.number_of_deleted} transactions`);
}

export async function deleteUser(id) {
  const responseOk = await fetch(`/api/users/${id}/delete`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": document.getElementsByName("csrf-token")[0].content,
    },
  }).then((response) => {
    return response.ok;
  });

  if (responseOk) {
    setTimeout(() => {
      window.location.href = "/welcome";
    }, 5000);
    return "Account deleted successfully. You will be logged out in 5 seconds";
  } else return "Account deletion unsuccessful";
}
