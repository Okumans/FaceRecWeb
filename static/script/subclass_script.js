const RED = "rgba(232, 86, 118, .8)"
const REDER = "rgba(232, 86, 118, 1)"
const GREEN = "rgba(176, 216, 164, 1)"
const GREENER = 'rgba(176, 216, 164, 1)'
const YELLOW = "#e8bc56"
const YELLOWER = "rgba(254, 225, 145, 1)"

Chart.defaults.color = "rgba(255, 255, 255, .7)";
Chart.defaults.font.family = "Kanit"

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

console.log(document.getElementById("navbar").offsetHeight)
document.getElementById("container").style.marginTop = document.getElementById("navbar").offsetHeight + 10 + "px"

const position = window.location.href.split("/").slice(-2,)
const page = position[0]
const subpage = position[1]

let myChart;
let objHash;

document.getElementById("grade").textContent = "มัธยมศึกษาปีที่ " + page + "/" + subpage

function updateAttendance() {
  console.log(position)
  fetch('/subclass-attendance-data/' + page + '/' + subpage)
    .then(response => response.json())
    .then(data => {
      const attendanceData = data.attendanceData;
      const attendanceCount = attendanceData.length;
      const checkedCount = attendanceData.filter(item => item.checked).length;
      const checkedLateCount = attendanceData.filter(item => item.checked && item.late).length;
      const notCheckedCount = attendanceCount - checkedCount;

      if (objHash != hashObject(data)) {
        objHash = hashObject(data)

        document.getElementById("attendance-count").textContent = `Checked: ${checkedCount} / ${attendanceCount}`;

        const attendanceTable = document.getElementById("attendance-table");
        const tbody = attendanceTable.querySelector("tbody");
        tbody.innerHTML = "";

        attendanceData.forEach(item => {
          const row = document.createElement("tr");
          const noCell = document.createElement("td");
          const nameCell = document.createElement("td");
          const timeCell = document.createElement("td");
          const statusCell = document.createElement("td");

          var name = item.student.realname + " " + item.student.surname
          name = (name == " ") ? "-" : name
          date = !item.time ? 0 : new Date(item.time)

          noCell.textContent = (item.student.class_number) ? item.student.class_number : "-"
          nameCell.textContent = item.student.realname + " " + item.student.surname;
          timeCell.textContent = date ? date.getHours() + ":" + date.getMinutes() : "-"
          statusCell.textContent = item.checked ? (item.late ? "Checked Late" : "Checked") : "Not Checked";

          noCell.style.backgroundColor = "#60b6aa3a"
          if (!item.checked) {
            statusCell.style.backgroundColor = RED
            statusCell.style.transition = ".3s";
            row.addEventListener('mouseover', function () {
              statusCell.style.backgroundColor = REDER
              statusCell.style.fontWeight = 700

            })
            row.addEventListener('mouseleave', function () {
              statusCell.style.backgroundColor = RED
              statusCell.style.fontWeight = 100
              statusCell.style.textShadow = ""
            })
          }
          else if (item.late) {
            statusCell.style.backgroundColor = YELLOW
            statusCell.style.transition = ".3s";
            row.addEventListener('mouseover', function () {
              statusCell.style.backgroundColor = YELLOWER
              statusCell.style.fontWeight = 700

            })
            row.addEventListener('mouseleave', function () {
              statusCell.style.backgroundColor = YELLOW
              statusCell.style.fontWeight = 100
              statusCell.style.textShadow = ""
            })
          }
          else if (item.checked) {
            statusCell.style.backgroundColor = GREEN
            row.style.transition = ".3s";
            row.addEventListener('mouseover', function () {
              statusCell.style.backgroundColor = GREENER
              statusCell.style.fontWeight = 700

            })
            row.addEventListener('mouseleave', function () {
              statusCell.style.backgroundColor = GREEN
              statusCell.style.fontWeight = 100
              statusCell.style.textShadow = ""
            })
          }

          row.onclick = () => window.location.href = "/students/" + item.student.IDD


          row.appendChild(noCell)
          row.appendChild(nameCell);
          row.appendChild(timeCell);
          row.appendChild(statusCell);
          tbody.appendChild(row);
        });

        // Generate attendance chart
        const chartDataConfig = {
          labels: ['Attendance'],
          datasets: [
            {
              label: 'Checked',
              data: [checkedCount - checkedLateCount],
              backgroundColor: 'rgba(176, 216, 164, 1)',
              borderRadius: 10,
              stack: "background"
            },
            {
              label: 'Checked Late',
              data: [checkedLateCount],
              borderRadius: 10,
              backgroundColor: 'rgba(254, 225, 145, 1)',
              stack: "background"
            },
            {
              label: 'Not Checked',
              data: [notCheckedCount],
              borderRadius: 10,
              backgroundColor: 'rgba(232, 66, 88, 1)',
              stack: "background"
            }
          ]
        };

        const chartOptions = {
          plugins: {
            legend: {
              labels: {
                font: {
                  size: 13,
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
                display: false
              },
            },
            y: {
              beginAtZero: true,
              max: attendanceCount,
              stepSize: 1,
              grid: {
                color: "rgba(255, 255, 255, 0.1)"
              },
            }
          },
          chartArea: {
            customCanvasBackgroundColor: {
              backgroundColor: 'rgba(251, 85, 85, 0.2)',
            }
          }
        };

        const chartContext = document.getElementById("attendance-chart").getContext("2d");

        if (myChart) {
          myChart.destroy();
        }

        myChart = new Chart(chartContext, {
          type: 'bar',
          data: chartDataConfig,
          options: chartOptions,
          plugins: [plugin],
        });
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
}

function download(){
  fetch(`/downloaddoc/${page}/${subpage}`)
    .then(response => {
      if (response.ok) {
        return response.blob();
      } else {
        throw new Error('Network response was not OK.');
      }
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${page}-${subpage}_attendance-summary.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    })
    .catch(error => {
      console.error('Error:', error);
    });
}
updateAttendance()
setInterval(updateAttendance, 10000)
