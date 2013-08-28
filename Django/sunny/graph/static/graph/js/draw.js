
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
    print_log(data.loglist);
}

function clear_all_db(clear_all_db_url){
    $.post(clear_all_db_url,true,function(e){
        location.reload();
    });
}

// Switch the displayed table according to the selected radio button
function change_sample(radio_button,data){
    data.sample.id = $(radio_button).val();
    $.get(json_url,
          data.sample,
          function(data_response){
               create_table(data_response);
               draw_graph(data_response);
          }
    )
}

// Update data (POST) and redraw - upon clicking the Update button
function post_data_and_redraw(data,json_url){
    var data = get_data_from_table(data);
    $.post(json_url,
           JSON.stringify({'measurements':data.measurements,'sample':data.sample}),
           function(data_response) {
                draw_graph(data_response);
           }, "json"
    )
}

// Read data from table
function get_data_from_table(data){
    data.measurements = []; // clean first
    $('#input_table tr.datarow').each(function(index,v){
        var fields = $('input',v);
        var dose = $(fields[0]).val();
        var response = $(fields[1]).val();
        var experiment = $(fields[2]).val();
        if (dose.length>0 && response.length>0)
            data.measurements.push([dose,response,experiment]);
    })
    return data
}

// Create a table from given *data*
function create_table(data){
    M = data.measurements;
    N = data.measurements.length;
    if (N==0) // no measurements yet, add a blank input line
        add_newline();
    else
        for (var i=0; i<N; i++){
            add_newline(M[i][0],M[i][1],M[i][2]);
        }
}

// Add a row to the input table with a Remove button, with class 'datarow'
function add_newline(d,r,e,position='last') {
    if(typeof(d)==='undefined') d=''; // dose
    if(typeof(r)==='undefined') r=''; // response
    if(typeof(e)==='undefined') e=''; // experiment
    var newline = '<td><input></td><td><input></td><td><input></td>';
    var delete_button = $('<td>').addClass('remove').html('x')
                                 .click(function() { $(this.parentNode).remove(); });
    if (position=='last'){
        $('#tbody').append('<tr></tr>');
        var line = $('#tbody tr:last');
        line.append(newline).append(delete_button).addClass('datarow');
    } else {
        $('#tbody').prepend('<tr></tr>');
        var line = $('#tbody tr:first');
        line.append(newline).append(delete_button).addClass('datarow');
    }
    $('input',line).each(function(i,input){
        switch(i){
        case 0: $(input).val(d); break;
        case 1: $(input).val(r); break;
        case 2: $(input).val(e); break;
        }
    })
}

// Print the R output - or more - inside the #log div
function print_log(loglist){
    var logbox = $('#log .log_content');
    logbox.text('');
    $.each(loglist, function(index,logstring){
        logbox.append("<p>"+logstring+"</p>");
    })
}

// Dynamic file import - upon clicking the "Upload input file" button
function import_file(file,data){
    var reader = new FileReader();
    reader.onload = function(e){
        var grid = $('#input_table tr.datarow');
        var lines = e.target.result.split('\n');
        lines = lines.slice(-lines.length+1); // remove header line
        $.each(lines, function(i,L){
            L = $.trim(L);
            L = L.split('\t');
            dose = L[0];
            response = parseFloat(L[1]).toFixed(2);
            experiment = L[2];
            // Update the input table
            if (L.length > 1){
                if (i < grid.length){ // replace existing lines
                    var cells = $('input',grid[i]);
                    $(cells[0]).val(dose);
                    $(cells[1]).val(response);
                    $(cells[2]).val(experiment);
                } else { // add necessary lines
                    add_newline(dose,response,experiment);
                }
            } else { // remove superfluous lines
                var glen = grid.length;
                for (var k=i; k<=glen; k++){
                    $(grid[k]).remove();
                }
                return false;
            }
        })
        // Create new sample if necessary, read the new table and redraw
        var sha1 = SHA1(e.target.result);
        data.sample.sha1 = sha1;
        data.sample.name = file.name;
        $.post(new_sample_url,
               JSON.stringify(data.sample),
               function(data_response){
                   data.sample.id = data_response['id'];
                   if (data_response['new'] == true) {}
                   post_data_and_redraw(data,json_url);
                   update_samples_list(data.sample);
               }, "json"
        )
        // Update the samples list
        function update_samples_list(sample){
            var thisinput = $('#samples_container input[value='+sample.id+']');
            if (thisinput.length > 0){
                thisinput.text(sample.name)
            } else {
                var newinput = $('<input>', {
                    type: 'radio',
                    name: 'samples',
                    value: sample.id,
                }).change(function() {
                    change_sample(this,data);
                }).attr('checked', true);
                $('#samples_container form').append(newinput).append(sample.name).append("<br>")
            }
        }
    }
    reader.error = function(e){
        console.log('Error while reading file\n', e)
    }
    reader.readAsText(file);
}


