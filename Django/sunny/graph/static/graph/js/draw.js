
function draw_graph(data){
    $('#graph_container').highcharts({
        chart: {},
        title: {text: 'BMC LL4 model'},
        xAxis: {title: {text: 'Dose'},
                type: 'logarithmic',
               },
        yAxis: {title: {text: 'Response'},
                type: 'linear',
                min: data.bounds[2],
                max: data.bounds[3],
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
    print_log(data)
}

// Create a table from given *data*
function update_table(data){
    M = data.measurements;
    N = data.measurements.length;
    if (N==0) // no measurements yet, add a blank input line
        add_newline();
    else
        for (var i=0; i<N; i++){
            add_newline(M[i][0],M[i][1]);
        }
}

// Add a row to the input table with a Remove button, with class 'datarow'
function add_newline(d,r,position='last') {
    if(typeof(d)==='undefined') d='';
    if(typeof(r)==='undefined') r='';
    var newline = '<td><input></input></td><td><input></input></td>';
    var delete_button = $('<td>').addClass('remove').html('x')
                                 .click(function() { $(this.parentNode).remove(); });
    if (position=='last'){
        $('#tbody').append('<tr></tr>');
        $('#tbody tr:last').append(newline).append(delete_button).addClass('datarow');
    } else {
        $('#tbody').prepend('<tr></tr>');
        $('#tbody tr:first').append(newline).append(delete_button).addClass('datarow');
    }
    $('#tbody tr:last input:first').val(d);
    $('#tbody tr:last input:last').val(r);
}

// Print the R output - or more - inside the #log div
function print_log(data){
    var logbox = $('#log .log_content')
    $.each(data.loglist, function(index,logstring){
        logbox.append("<p>"+logstring+"</p>")
    })
}
