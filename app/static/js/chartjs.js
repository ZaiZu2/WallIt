// Format transactions into used by Category Chart
function calculateCategoryWeights() {
  // map array of categories into object
  let categoryWeights = {};
  for (let category of Object.values(user.categories)) {
    categoryWeights[category.id] = { name: category.name, sum: 0 };
  }

  for (let transaction of user.transactions) {
    if (transaction.amount < 0 && transaction.category != null) {
      categoryWeights[transaction.category]["sum"] += -1 * transaction.amount;
    }
  }
  // Round up any floating point errors and delete blank categories
  for (let id of Object.keys(categoryWeights)) {
    categoryWeights[id]["sum"] =
      Math.round(categoryWeights[id]["sum"] * 100) / 100;
    if (categoryWeights[id]["sum"] == false) delete categoryWeights[id];
  }

  const simplified = {};
  for (let categoryParams of Object.values(categoryWeights))
    simplified[categoryParams.name] = categoryParams.sum;

  return simplified;
}

export function reloadCategoryChart(chart) {
  if (user.transactions && user.transactions.length != 0) {
    const weights = calculateCategoryWeights();

    chart.data.labels = Object.keys(weights);
    chart.data.datasets[0].data = Object.values(weights);
    chart.update();
  }
}

// Category spendings chart
const categoryChartCell = document
  .getElementById("categoryChart")
  .getContext("2d");
export const categoryChart = new Chart(categoryChartCell, {
  type: "bar",
  data: {
    labels: [],
    datasets: [
      {
        label: "Spendings",
        maxBarThickness: 100,
        minBarLength: 5,
        backgroundColor: [
          "rgba(255, 99, 132, 0.6)",
          "rgba(54, 162, 235, 0.6)",
          "rgba(255, 206, 86, 0.6)",
          "rgba(75, 192, 192, 0.6)",
          "rgba(153, 102, 255, 0.6)",
          "rgba(255, 159, 64, 0.6)",
        ],
        borderColor: [
          "rgba(255, 99, 132, 1)",
          "rgba(54, 162, 235, 1)",
          "rgba(255, 206, 86, 1)",
          "rgba(75, 192, 192, 1)",
          "rgba(153, 102, 255, 1)",
          "rgba(255, 159, 64, 1)",
        ],
        borderWidth: 2,
      },
    ],
  },
  options: {
    responsive: false,
    scales: {
      x: {
        ticks: {
          color: "white",
        },
      },
      y: {
        grid: {
          color: "rgba(110, 110, 110, 0.5)",
          tickColor: "rgba(0, 0, 0, 0)",
        },
        ticks: {
          color: "white",
        },
      },
    },
    plugins: {
      legend: {
        display: false,
        title: {},
        labels: {
          color: "white",
        },
      },
    },
  },
});

export async function reloadMonthlyChart(chart) {
  const data = await fetch("/api/transactions/monthly", {
    method: "GET",
    mode: "cors",
    credentials: "same-origin",
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

  let chartLabels = [];
  let chartDatasets = {
    outgoing: [],
    incoming: [],
    balance: [],
  };

  for (let monthly of data) {
    chartLabels.push(monthly.month);
    chartDatasets.outgoing.push(monthly.outgoing);
    chartDatasets.incoming.push(monthly.incoming);
    chartDatasets.balance.push(monthly.balance);
  }

  chart.data.labels = chartLabels;
  chart.data.datasets.forEach((dataset) => {
    dataset.data = chartDatasets[dataset.label.toLowerCase()];
  });
  chart.update();
}

const monthlyChartCell = document
  .getElementById("monthlyChart")
  .getContext("2d");
export const monthlyChart = new Chart(monthlyChartCell, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "Incoming",
        data: [],
        fill: true,
        borderColor: "rgba(62, 183, 47, 1)",
        tension: 0,
      },
      {
        label: "Outgoing",
        data: [],
        fill: false,
        borderColor: "rgba(255, 99, 132, 1)",
        tension: 0,
      },
      {
        label: "Balance",
        data: [],
        fill: false,
        borderColor: "rgba(54, 162, 255, 1)",
        tension: 0,
      },
    ],
  },
  options: {
    responsive: false,
    scales: {
      x: {
        grid: {
          color: "rgba(110, 110, 110, 0.5)",
        },
        ticks: {
          color: "white",
        },
      },
      y: {
        grid: {
          color: "rgba(110, 110, 110, 0.5)",
          tickColor: "rgba(0, 0, 0, 0)",
        },
        ticks: {
          color: "white",
        },
      },
    },
    elements: {
      point: {
        borderWidth: 3,
        hitRadius: 6,
        hoverRadius: 4.5,
        hoverBorderWidth: 9,
      },
    },
    plugins: {
      legend: {
        title: {},
        labels: {
          color: "white",
        },
      },
    },
  },
});
