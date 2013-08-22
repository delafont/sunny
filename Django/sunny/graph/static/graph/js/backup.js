
function draw_graph(data){
    $('#graph_container').highcharts({
        chart: {},
        title: {text: 'BMC LL4 model'},
        xAxis: {title: {text: 'Dose'},
                type: 'logarithmic',
               },
        yAxis: {title: {text: 'Response'},
                type: 'linear',
                min: 0,
                max: 100,
               },
        legend: {enabled: false},
        series: [
            {
                type: 'scatter',
                name: 'Dose-response data',
                data: data.measurements,
            }, {
                type: 'line',
                name: 'Log-logistic(4) fit',
                data: data.curve,
                enableMouseTracking: false,
                marker: {enabled: false},
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
    $('#tbody tr:last').append(newline).append(delete_button);
    $('#tbody tr:last input:first').val(d);
    $('#tbody tr:last input:last').val(r);
}


// Old function with my own canvas drawing
function own_draw_graph(data){
    //maybe this is not working
    $("#global_container")
    .append(
        $('div', {
            id: "mycanvas_container",
        })
        .append($('canvas', {
            id: "mycanvas",
            width: '500px',
            height: '300px'
        }))
    )
    //var canvas = $("#mycanvas");
    //canvas.attr('width','500px');
    //canvas.attr('height','300px');
    canvas.clearCanvas();
    var vmargin = 5;
    var max_x = Math.log(data.bounds[0]) + 1;
    var max_y = 100 + 2*vmargin;
    var w = canvas.width();
    var h = canvas.height();
    x_scale = w/max_x;
    y_scale = h/max_y;

    // Axis
    canvas.drawLine({
        strokeStyle: "black",
        x1: 0, y1: vmargin,
        x2: 0, y2: h,
    })
    canvas.drawLine({
        strokeStyle: "black",
        x1: 0, y1: h,
        x2: w-15, y2: h,
    })

    // Points
    $.each(data.measurements, function(index,x){
        canvas.drawRect({
            fillStyle: "black",
            x: x_scale * Math.log(x[0]),
            y: h - y_scale * x[1] - vmargin,
            width: 3,
            height: 3,
        })
    })

    // Fit
    var curve = {
        strokeStyle: "blue",
        strokeWidth: 2,
    };
    $.each(data.curve, function(index,x){
        curve['x'+(index+1)] = x_scale * Math.log(x[0]);
        curve['y'+(index+1)] = h - y_scale * x[1] - vmargin;
    })
    canvas.drawLine(curve);

    // BMC ...
    var BCM = 0;
}

