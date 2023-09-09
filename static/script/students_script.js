// Define the data for the chart
const CHECKED = "CHECKED";
const CHECKED_LATE = "CHECKED_LATE";
const NOT_CHECKED = "NOT_CHECKED";

const RED = "#e85676"
const GREEN = "rgba(45,255,196)"


const idd = window.location.href.split("/").slice(-1)[0];
var labels = [];
var values = [];
var hashed_graph_info;

function hashArray(arr) {
  const jsonString = JSON.stringify(arr);
  const hash = CryptoJS.SHA256(jsonString);
  return hash.toString(CryptoJS.enc.Hex);
}

fetch('/students-get-data/' + idd)
  .then(response => response.json())
  .then(data => {
    console.log(data);
    hashed_graph_info = hashArray(data.student.graph_info);
    do_da_thing(data.student);
    setting_up(data.status);
  })
  .catch(error => {
    console.error(error);
  });

function setting_up(status) {
  let root = document.querySelector(":root");
  if (status == CHECKED_LATE) {
    root.style.setProperty('--state-color', '#e8bc56');
    root.style.setProperty('--state-color-glow', '#e8bc56');
  } else if (status == NOT_CHECKED) {
    root.style.setProperty('--state-color', '#e85676');
    root.style.setProperty('--state-color-glow', '#e85676');
  } else if (status == CHECKED) {
    root.style.setProperty('--state-color', 'rgba(45,255,196)');
    root.style.setProperty('--state-color-glow', 'rgba(45,255,196, 0.64)');
  }
}

function setting_up_fetch() {
  fetch('/students-get-data/' + idd)
    .then(response => response.json())
    .then(data => {
      var status = data.status;
      setting_up(status);

      if (hashArray(data.student.graph_info) != hashed_graph_info) {
        do_da_thing(data.student);
      }
    })
    .catch(error => {
      console.error(error);
    });
}

setInterval(setting_up_fetch, 1000);

function do_da_thing(student) {
  // Convert date2num values to JavaScript timestamp
  if (student.graph_info.length) {
    for (var i = 0; i < student.graph_info[0].length; i++) {
      var timestamp = student.graph_info[1][i];
      var timestamp_label = student.graph_info[0][i];
      var date = new Date(timestamp);
      var time = date.getHours() * 3600 + date.getMinutes() * 60 + date.getSeconds();
      var day = new Date(timestamp_label).toLocaleString('default', { weekday: 'long' });

      labels.push(day);
      values.push(time);
    }

    // Calculate average time
    var sum = values.reduce((acc, val) => acc + val, 0);
    var average = sum / values.length;
    var averageValues = Array(values.length).fill(average);

    // Create a new Chart.js chart
    var data = {
      labels: labels,
      datasets: [
        {
          label: "Check In",
          data: values,
          backgroundColor: "rgba(255, 0, 0, 0.5)",
          borderColor: GREEN, // Set the desired line color
          fill: true, // Enable fill color
          backgroundColor: "rgba(45,255,196, 0.3)", // Set the desired fill color
          tension: 0.4
          
        },
        {
          label: "Average",
          data: averageValues,
          borderColor: "#e8bc56", // Set the desired line color
          backgroundColor: "#e8bc56" // Set the desired fill color
        }
      ],
    };
    var options = {

      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          display: true,
          title: {
            font: {
              size: 16,
              family: "Kanit",
              weight: "bold"
          },
            display: true,
            text: 'Days',
          },
        },
        y: {
          display: true,
          title: {
            font: {
              size: 16,
              family: "Kanit",
              weight: "bold"
          },
            display: true,
            text: 'Time',
          },
          ticks: {
            callback: function (value) {
              var hours = Math.floor(value / 3600);
              var minutes = Math.floor((value % 3600) / 60);
              return ("0" + hours).slice(-2) + ":" + ("0" + minutes).slice(-2);
            },
          },
        },
      },
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend:{
          labels:{
            font: {
              size: 15,
              family: "Kanit"
          },
            usePointStyle: true,
            pointStyle: "circle"
          }
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              var value = context.raw;
              var hours = Math.floor(value / 3600);
              var minutes = Math.floor((value % 3600) / 60);
              return ("0" + hours).slice(-2) + ":" + ("0" + minutes).slice(-2);
            },
          },
        },
      },
    };

    var ctx = document.getElementById("arrival-times-chart").getContext("2d");
    window.myLine = new Chart(ctx, {
      type: 'line',
      data: data,
      options: options,
    });
    var bodyHeight = document.body.offsetHeight;
    var containerHeight = document.getElementById("container").clientHeight;
    var leftHeight = bodyHeight - containerHeight
    document.getElementById("arrival-times-chart").style.height = leftHeight
  }
}
