const ctx = document.getElementById('myChart');

let myChart;
let jsonData;

fetch('data.json')
.then(function(response){
    if(response.ok == true){
        return response.json();
    }
})
.then(function(data){
    jsonData = data;
    createChartOne(data, 'bar');
});

function setChartType(chartType) {

    myChart.destroy();
    createChartOne(jsonData, chartType);
}
function createChartOne(data, type) {
    myChart = new Chart(ctx, {
        type: type,
        data: {
            labels: data.map(row => row.month),
            datasets: [{
                label: '# of Votes',
                data: data.map(row => row.income),
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                x: {
                    ticks: {
                        color: 'white',
                    }
                },
                y: {
                    ticks: {
                        color: 'white',
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: 'white'
                    }
                }
            },

            maintainAspectRatio: false
        }
    });
}




const ctxt = document.getElementById('myChartTwo');

let myChartTwo;
let jsonDataTwo;

fetch('data_two.json')
.then(function(response){
    if(response.ok == true){
        return response.json();
    }
})
.then(function(data){
    jsonDataTwo = data;
    createChartTwo(data, 'bar');
});

function setChartTypeTwo(chartType) {

    myChartTwo.destroy();
    createChartTwo(jsonDataTwo, chartType);
}
function createChartTwo(data, type) {
    myChartTwo = new Chart(ctxt, {
        type: type,
        data: {
            labels: data.map(row => row.month),
            datasets: [{
                label: '# of Votes',
                data: data.map(row => row.money),
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                x: {
                    ticks: {
                        color: 'white',
                    }
                },
                y: {
                    ticks: {
                        color: 'white',
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: 'white'
                    }
                }
            },
            
            maintainAspectRatio: false
        }
    });
}


