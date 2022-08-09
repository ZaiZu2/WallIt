// Format transactions into used by Category Chart
function calculateCategoryWeights() {
  let categoryWeights = {};

  for (let transaction of transactions) {
    if (transaction.amount < 0 && transaction.category != null) {
      if (Object.keys(categoryWeights).includes(transaction.category)) {
        categoryWeights[transaction.category] += -1 * transaction.amount;
      } else {
        categoryWeights[transaction.category] = -1 * transaction.amount;
      }
    }
  }
  // Round up any floating point errors
  for (let [categoryName, categoryWeight] of Object.entries(categoryWeights)) {
    categoryWeights[categoryName] = Math.round(categoryWeight * 100) / 100;
  }
  return categoryWeights;
}

export function reloadCategoryChart(chart) {
  const weights = calculateCategoryWeights();
  chart.data.labels = Object.keys(weights);
  chart.data.datasets[0].data = Object.values(weights);
  chart.update();
}

const ctx = document.getElementById("categoryChart").getContext("2d");
export const categoryChart = new Chart(ctx, {
  type: "bar",
  data: {
    labels: [],
    datasets: [
      {
        label: "Spendings",
        backgroundColor: ["rgba(255, 99, 132, 0.4)"],
        borderColor: ["rgba(255, 99, 132, 1)"],
        borderWidth: 2,
      },
      // {
      //   label: "Spendings",
      //   data: calculateCategoryWeights(transactions),
      //   backgroundColor: [
      //     "rgba(255, 99, 132, 0.4)",
      //     "rgba(54, 162, 235, 0.4)",
      //     "rgba(255, 206, 86, 0.4)",
      //     "rgba(75, 192, 192, 0.4)",
      //     "rgba(153, 102, 255, 0.4)",
      //     "rgba(255, 159, 64, 0.4)",
      //   ],
      //   borderColor: [
      //     "rgba(255, 99, 132, 1)",
      //     "rgba(54, 162, 235, 1)",
      //     "rgba(255, 206, 86, 1)",
      //     "rgba(75, 192, 192, 1)",
      //     "rgba(153, 102, 255, 1)",
      //     "rgba(255, 159, 64, 1)",
      //   ],
      //   borderWidth: 2,
      // },
    ],
  },
  options: {
    responsive: false,
    scales: {
      x: {
        stacked: true,
      },
      y: {
        beginAtZero: true,
      },
    },
  },
});
