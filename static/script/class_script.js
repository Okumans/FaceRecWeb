const RED = "rgba(232, 86, 118, .8)"
const REDER = "rgba(232, 86, 118, 1)"
const GREEN = "rgba(45,255,196)"
const GREENER = 'rgba(176, 216, 164, 1)'
const YELLOW = "#e8bc56"
const YELLOWER  = "rgba(254, 225, 145, 1)"

const attendanceSummary = document.getElementById("attendance-summary");
const sumValues = obj => Object.values(obj).reduce((a, b) => a + b, 0);
const uniqueArray = array => array.filter((value, index, self) => self.indexOf(value) === index);
const CLASS = window.location.href.split("/").slice(-1)[0]

Chart.defaults.color = "rgba(255, 255, 255, .7)";
Chart.defaults.font.family = "Kanit"
document.getElementById("container").style.marginTop = document.getElementById("navbar").offsetHeight + 20 + "px"
document.getElementById("grade").textContent = "มัธยมศึกษาปีที่ " + CLASS

function hashObject(obj) {
  const objString = JSON.stringify(obj);
  const hash = CryptoJS.SHA256(objString).toString();
  return hash;
}

const plugin = {
  id: 'customCanvasBackgroundColor',
  beforeDraw: (chart, args, options) => {
    const { ctx } = chart;
    const chartArea = chart.chartArea;
    const radius = 10; // Adjust the radius value to change the roundness of the corners

    ctx.save();
    ctx.globalCompositeOperation = 'destination-over';
    ctx.fillStyle = options.color || 'rgba(108, 184, 173, 0.2)';

    ctx.beginPath();
    ctx.moveTo(chartArea.left + radius, chartArea.top);
    ctx.lineTo(chartArea.right - radius, chartArea.top);
    ctx.quadraticCurveTo(chartArea.right, chartArea.top, chartArea.right, chartArea.top + radius);
    ctx.lineTo(chartArea.right, chartArea.bottom - radius);
    ctx.quadraticCurveTo(chartArea.right, chartArea.bottom, chartArea.right - radius, chartArea.bottom);
    ctx.lineTo(chartArea.left + radius, chartArea.bottom);
    ctx.quadraticCurveTo(chartArea.left, chartArea.bottom, chartArea.left, chartArea.bottom - radius);
    ctx.lineTo(chartArea.left, chartArea.top + radius);
    ctx.quadraticCurveTo(chartArea.left, chartArea.top, chartArea.left + radius, chartArea.top);
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  }
};

let myChart;
let objHash;

function updateAttendance(){
  axios.get("/class-attendance-data/" + CLASS)
    .then(response => {
      const classData = response.data;
      console.log("update information")
      
      if (hashObject(classData) != objHash){
        objHash = hashObject(classData)
        const CheckedCount = classData.checkedCount
        const CheckedLateCount = classData.checkedLateCount
        const NotCheckedCount = classData.notCheckedCount

        const classes = uniqueArray([...Object.keys(CheckedCount), ...Object.keys(CheckedLateCount), ...Object.keys(NotCheckedCount)])
        const totalPeopleCount = sumValues(CheckedCount) + sumValues(CheckedLateCount) + sumValues(NotCheckedCount)
        const totalCheckedCount = sumValues(CheckedCount) + sumValues(CheckedLateCount)

        var CheckedCountEach = {}
        var PeopleCountEach = {}
        for (var i in classes) {
          if (CheckedCountEach[classes[i]] == undefined) {
            CheckedCountEach[classes[i]] = 0
          }
          if (PeopleCountEach[classes[i]] == undefined) {
            PeopleCountEach[classes[i]] = 0
          }
          CheckedCountEach[classes[i]] += (CheckedCount[classes[i]] != undefined) ? CheckedCount[classes[i]] : 0
          PeopleCountEach[classes[i]] += (CheckedCount[classes[i]] != undefined) ? CheckedCount[classes[i]] : 0

          CheckedCountEach[classes[i]] += (CheckedLateCount[classes[i]] != undefined) ? CheckedLateCount[classes[i]] : 0
          PeopleCountEach[classes[i]] += (CheckedLateCount[classes[i]] != undefined) ? CheckedLateCount[classes[i]] : 0

          PeopleCountEach[classes[i]] += (NotCheckedCount[classes[i]] != undefined) ? NotCheckedCount[classes[i]] : 0
        }

        const MaxClass = Math.max(...Object.values(PeopleCountEach))
        console.log(CheckedCountEach, PeopleCountEach)

        // Display attendance summary
        attendanceSummary.innerHTML = `
          <p>Total Checked: ${totalCheckedCount}/${totalPeopleCount}</p>
        `;

        const chartDataConfig = {
          labels: classes.map(c => CLASS + "/" + c),
          datasets: [
            {
              label: "Checked",
              data: Object.values(CheckedCountEach),
              backgroundColor: GREENER,
              borderRadius: 10,
              stack: "background"
            },
            {
              label: "Not Checked",
              data: Object.values(NotCheckedCount),
              borderRadius: 10,
              backgroundColor: "rgba(232, 66, 88, 1)",
              stack: "background"
            },
          ],
        };

        const chartOptions = {
          plugins:{
            legend:{
              labels:{
                font: {
                  size: 15,
                  family: "Kanit"
              },
                usePointStyle: true,
                pointStyle: "circle"
              }
            }
          },
          scales: {
            x: {
              stacked: true,
              grid: {
                display: false, // Remove the horizontal grid lines
              },
            },
            y: {
              beginAtZero: true,
              max: MaxClass,
              stepSize: 1,
              grid: {
                color: "rgba(255, 255, 255, 0.1)"
              },
            },
          },
          onClick: (event, elements) => {
            if (elements.length > 0) {
              const index = elements[0].index;
              console.log(index)
              const url = "/classes/" + CLASS + "/" + classes[index];
              window.location.href = url;
            }
          }
        };

        const chartContext = document.getElementById("attendance-chart").getContext("2d");

        if (myChart) {
          myChart.destroy();
        }

        myChart = new Chart(chartContext, {
          type: "bar",
          data: chartDataConfig,
          options: chartOptions,
          plugins: [plugin],
        });

      }})
      .catch(error => {
        console.error("Error:", error);
      });
  }

updateAttendance();
setInterval(updateAttendance, 10000)