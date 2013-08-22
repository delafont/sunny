
function draw_graph(data){
    $('#graph_container').highcharts({
        chart: {},
        title: {text: 'BMC LL4 model'},
        xAxis: {title: {text: 'Dose'},
                type: 'logarithmic',
               },
        yAxis: {title: {text: 'Response'},
                type: 'linear',
                min: -10,
                max: 110,
               },
        legend: {enabled: false},
        series: [
            {
                type: 'scatter',
                name: 'Dose-response data',
                data: data.measurements,
                color: '#2F7ED8',
            }, {
                type: 'spline',
                name: 'Fit',
                data: data.curve,
                enableMouseTracking: false,
                marker: {enabled: false},
                color: 'black',  //'#8BBC21',
            }, {
                type: 'scatter',
                name: 'Fitted data',
                data: data.fitted,
                marker: {symbol: 'circle'},
                color: 'black',
            }
        ]
    });
}


// Add a row to the input table with a Remove button
function add_newline(d,r) {
    if(typeof(d)==='undefined') d='';
    if(typeof(r)==='undefined') r='';
    var newline = '<td><input></input></td><td><input></input></td>';
    var delete_button = $('<td>').addClass('remove').html('x')
                                 .click(function() { $(this.parentNode).remove(); });
    $('#tbody').append('<tr></tr>');
    $('#tbody tr:last').append(newline).append(delete_button).addClass('datarow');
    $('#tbody tr:last input:first').val(d);
    $('#tbody tr:last input:last').val(r);
}


