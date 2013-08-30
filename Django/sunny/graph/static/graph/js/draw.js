

/**************************** GLOBAL VARIABLES ****************************/

var _JSON_URL_;
var _NEW_SAMPLE_URL_;
var _CLEAR_ALL_DB_URL_;
var _DATA_;
var _CHART_;
var _ACTIVE_GRAPH_IDS_;
var _ACTIVE_TABLE_ID_;

/********************************* GRAPH **********************************/

function draw_graph(){
    console.log(">>> Draw Graph");
    var series = [];
    for (i in _DATA_.samples){
        var sample = _DATA_.samples[i];
        var points = _DATA_.points[sample.id];
        var curves = _DATA_.curves[sample.id];
        for (exp in points){
            series.push.apply(series, [{
                type: 'scatter',
                name: 'DR - '+sample.name+' - '+ exp,
                data: points[exp],
                tooltip: {valuePrefix: exp},
                marker: {radius:2.5},
                //color: '#2F7ED8',
            }, {
                type: 'spline',
                name: 'Fit - '+sample.name+' - '+ exp,
                data: curves[exp],
                enableMouseTracking: false,
                marker: {enabled: false},
                //color: 'black',  //'#8BBC21',
            }]);
        }
    }
    _CHART_ = new Highcharts.Chart({
        chart: {renderTo: 'graph_container'},
        title: {text: 'BMC LL4 model'},
        xAxis: {title: {text: 'Dose'},
                type: 'logarithmic',
               },
        yAxis: {title: {text: 'Response (% of control)'},
                type: 'linear',
                min: _DATA_.bounds[2],
                max: _DATA_.bounds[3],
               },
        legend: {enabled: true},
        series: series
    });
    print_log(_DATA_.loglist);
    return _CHART_;
}
// Remove all series in the graph
function clear_graph(){
    for (i in _CHART_.series){
        _CHART_.series[i].setData([]);
    }
}

/******************************* SAMPLE SWITCH *********************************/

// Switch the displayed table according to the selected checkboxes, and redraw.
function change_sample_graph(button){
    console.log(">>> Change Samples Graph -->");
    selected_sample_ids = [];
    $('input:checkbox[name=samples_graph]:checked').each(function(){
        selected_sample_ids.push(parseInt($(this).val()));
    });
    update_local('active_samples',selected_sample_ids)
    //$.get(_JSON_URL_,
    //      JSON.stringify(selected_sample_ids),
    //      function(data_response){
    //           create_table(data_response);
    //           draw_graph(data_response);
    //      }
    //)
    console.log('>>> Selected graph samples:',selected_sample_ids);
    return selected_sample_ids;
}
function change_sample_table(button){
    console.log(">>> Change Sample Table -->");
    selected_sample_id = parseInt($(button).val());
    update_local('active_table',selected_sample_id)
    console.log(_DATA_.points,selected_sample_id)
    console.log(_DATA_.points[selected_sample_id])
    create_table(_DATA_.points[selected_sample_id]);
    console.log('>>> Selected table sample:',selected_sample_id);
    return selected_sample_id;
}

/******************************* LOCAL STORAGE *********************************/

// Fetch in `localStorage` which samples were plotted and re-check the respective checkboxes
function boxcheck_active_samples(){
    console.log(">>> BoxCheck Active Samples");
    var active_ids = get_local('active_samples');
    for (as in active_ids){
        $('input:checkbox[name=samples_graph][value='+as+']').prop('checked',true);
    }
    _ACTIVE_GRAPH_IDS_ = active_ids;
    return active_ids;
}
// Fetch in `localStorage` which table was active and re-check the respective radio button
function radiocheck_active_table(){
    console.log(">>> RadioCheck Active Table");
    var active_ids = get_local('active_samples');
    var active_id = get_local('active_table')[0];
    $('input:radio[name=samples_table][value='+active_id+']').prop('checked',true);
    _ACTIVE_TABLE_ID_ = active_id;
    return active_id;
}
// Keep existing, add a new sample to the localStorage
function add_to_local(key,newids){
    console.log(">>> Add to Active Samples", newid);
    ids = get_local('active_samples');
    for (i in newids){
        var newid = newids[i];
        if ($.inArray(newid,ids) == -1){
            ids.push(newid);
        }
    }
    update_local(key,ids)
    return ids;
}
// If there are ids corresponding to *key*, return a list of them.
function get_local(key){
    var val = localStorage.getItem(key);
    if (val){ ids = JSON.parse(val); }
    else { ids = []; }
    return ids;
}
// Replace the current active samples in the localStorage
function update_local(key,ids){
    localStorage.setItem(key,JSON.stringify(ids));
}

/********************************** SERVER EXCHANGE **********************************/

// Clear Measurement and Sample tables from the database, and clear localStorage
function clear_all_db(){
    console.log(">>> Clear All DB");
    $.post(_CLEAR_ALL_DB_URL_,true,function(e){
        location.reload();
    });
    localStorage.clear();
}
// Send the (possibly edited) table data, and the active samples for redrawing
function update_event(){
    console.log(">>> Update Event");
    var measurements = read_data_from_table();
    if (_ACTIVE_TABLE_ID_){
        measurements = {_ACTIVE_TABLE_ID_:measurements};
        samples = _ACTIVE_GRAPH_IDS_;
    //} else if (measurements) { // custom entries
    //    measurements = {-1: measurements};
    //    samples = {-1: {'id':-1,'name':'custom','sha1':''}}
    } else {
        measurements = {};
        samples = _ACTIVE_GRAPH_IDS_;
    }
    var tosend = {'measurements':measurements, 'samples':samples};
    post_data_and_redraw(tosend);
}
/* Update data (POST) and redraw - upon clicking the Update button
   *tosend* must be of the form

       {'measurements': {sample_id:[(dose,response,exp),]},
        'samples': [sample_ids] or {sample_id:...} }

   Measurements are modified in the DB according to the first.
   Samples determine the POST response and ultimately the graph.
*/
function post_data_and_redraw(tosend){
    console.log(">>> Post Data And Redraw");
    $.post(_JSON_URL_,
           JSON.stringify(tosend),
           function(data_response) {
                _DATA_ = data_response;
                draw_graph();
           }, "json"
    );
}

/********************************** TABLE ***********************************/

// Read data from table
function read_data_from_table(){
    console.log(">>> Get Data From Table");
    var measurements = [];
    $('#input_table tr.datarow').each(function(index,v){
        var fields = $('input',v);
        var dose = parseFloat($(fields[0]).val());
        var response = parseFloat($(fields[1]).val());
        var experiment = parseInt($(fields[2]).val());
        if (dose || response){
            measurements.push([dose,response,experiment]);
        }
    });
    return measurements;
}
// Create a table from given *points*, a dict {exp:[(1,2,exp),]}
function create_table(points){
    console.log(">>> Create Table");
    console.log('points',points)
    $('#input_table .datarow').remove();
    if (!points){
        add_newline('','','');
    }
    for (exp in points){
        M = points[exp];
        N = M.length;
        if (N==0) { // no measurements yet, add a blank input line
            add_newline('','','',position='first');
        } else {
            for (var i=0; i<N; i++){
                add_newline(M[i][0],M[i][1],exp);
            }
        }
    }
}
// Add a row to the input table with a Remove button, with class 'datarow'
function add_newline(d,r,e,position='last') {
    if(typeof(d)==='undefined') d=''; // dose
    if(typeof(r)==='undefined') r=''; // response
    if(typeof(e)==='undefined') e=''; // experiment
    var newline = '<td><input class="dose_in"></td><td><input class="response_in"></td>'
                + '<td><input class="experiment_in"></td>';
    var delete_button = $('<td>').addClass('remove').html('x')
                                 .click(function() { $(this.parentNode).remove(); });
    if (position=='last'){
        $('#input_table tbody').append('<tr></tr>');
        var line = $('#tbody tr:last');
        line.append(newline).append(delete_button).addClass('datarow');
    } else {
        $('#input_table tbody').prepend('<tr></tr>');
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

/********************************** LOG ***********************************/

// Print the R output - or more - inside the #log div
function print_log(loglist){
    var logbox = $('#log .log_content');
    logbox.text('');
    $.each(loglist, function(index,logstring){
        logbox.append("<p>"+logstring+"</p>");
    })
}

/********************************** FILE IMPORT ***********************************/

// Dynamic file import - upon clicking the "Upload input file" button
function import_file(file){
    console.log('>>> Import File');
    var reader = new FileReader();
    reader.onload = function(e){
        // Parse and fill the table
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
                    // sample is not known yet
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
        // is it already on the current samples list?:
        //all_sha1 = [];
        //for (i in _DATA_.samples) { all_sha1.push(_DATA_.samples[i].sha1); }
        //if (sha1 in all_sha1){
        //    "Do nothing?"
        //} else {
            var newsample = {'sha1':sha1, 'name':file.name}
            $.post(_NEW_SAMPLE_URL_,
                   JSON.stringify(newsample),
                   function(data_response){
                       //if (data_response['new'] == true) {}
                       newsample.id = data_response['id'];
                       add_to_local('active_samples',[newsample.id]);
                       update_local('active_table',[newsample.id]);
                       boxcheck_active_samples();
                       radiocheck_active_table();
                       _DATA_.samples[newsample.id] = newsample;
                       tosend = {'measurements': {},
                                 'samples': _ACTIVE_GRAPH_IDS_ };
                       tosend.measurements[newsample.id] = read_data_from_table();
                       post_data_and_redraw(tosend);
                       console.log(1,_DATA_.points)
                       update_samples_list(newsample);
                   }, "json"
            );
    }
    reader.error = function(e){
        console.log('Error while reading file\n', e);
    }
    reader.readAsText(file);
}

function update_samples_list(sample){
    console.log('>>> Update samples list');
    // checkboxes
    var thisinput = $('#graph_samples_container input[value='+sample.id+']');
    if (thisinput.length > 0){
        thisinput.append(sample.name);
    } else {
        //$('#graph_samples_container input[name=samples_graph]').removeAttr('checked');
        var newinput = $('<input>', {
            type: 'checkbox',
            name: 'samples_graph',
            value: sample.id,
        }).change(function() {
            change_sample_graph(this);
        }).attr('checked', true);
        $('#graph_samples_container form').append(newinput).append(sample.name).append("<br>");
    }
    // radio buttons
    var thisinput = $('#table_samples_container input[value='+sample.id+']');
    if (thisinput.length > 0){
        thisinput.append(sample.name);
    } else {
        var newinput = $('<input>', {
            type: 'radio',
            name: 'samples_table',
            value: sample.id,
        }).change(function() {
            change_sample_table(this);
        }).attr('checked', true);
        $('#table_samples_container form').append(newinput).append(sample.name).append("<br>");
    }
}

