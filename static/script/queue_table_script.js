const table = document.getElementById("attendance-table")

function setJeightLight(){
    const rows = table.rows
    for (let i=1; i<rows.length; i++){
        const row = rows[i]
        const queueId = row.getElementsByTagName('td')[1]
        
        if (queueId.textContent == window.location.href.split("/").slice(-1)[0]){
            const columns = row.getElementsByTagName('td')
            for (const column in columns){
                columns[column].style.backgroundColor = "#FFFF00"
            }
            break
        }
    }
}

setInterval(function(){
    const rows = table.rows
    for (let i=1; i<rows.length; i++){
        const row = rows[i]
        const queueTimeTaken = row.getElementsByTagName('td')[3]
        
        if (queueTimeTaken.textContent == "-") return

        let minutes = parseInt(queueTimeTaken.textContent.split(":")[0])
        let seconds = parseInt(queueTimeTaken.textContent.split(":")[1])
        

        let totalSeconds = minutes * 60 + seconds
        totalSeconds += 1*i

        minutes = Math.floor(totalSeconds / 60)
        seconds = totalSeconds % 60
        queueTimeTaken.textContent = ("0" + minutes).slice(-2) + ":" + ("0" + seconds).slice(-2)
    }
}, 1000)

function update_table(table_data){
    while (table_data.length > table.rows.length-1){
        var new_row = table.insertRow(1)
        new_row.insertCell(0).innerHTML = "-"
        new_row.insertCell(1).innerHTML = "-"
        new_row.insertCell(2).innerHTML = "-"
        new_row.insertCell(3).innerHTML = "-"
    }
    while (table_data.length < table.rows.length-1){
        table.deleteRow(1);
    }

    const rows = table.rows
    for (let i=1; i<rows.length; i++){
        const row = rows[i]
        const cells = row.getElementsByTagName('td')
        cells[0].textContent = table_data[i-1][0]
        cells[1].textContent = table_data[i-1][1]
        cells[2].textContent = table_data[i-1][2]
        cells[3].textContent = table_data[i-1][3]
    }

    
}

setInterval(function(){
    fetch('/queues_get', {method: 'GET'})
        .then(response => response.json())
        .then(data => update_table(data["data"]))
        .catch(error => console.error(error))
}, 5000)

setJeightLight()