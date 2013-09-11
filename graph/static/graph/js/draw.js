

/**************************** GLOBAL VARIABLES ****************************/

var _JSON_URL_;
var _NEW_SAMPLE_URL_;
var _CLEAR_ALL_DB_URL_;
var _DATA_;
var _CHART_;
var _ACTIVE_GRAPH_IDS_ = [];
var _ACTIVE_TABLE_ID_;
var _IMG_URL_;
var _SAMPLE_DATA_URL_;
var _GETFILE_URL_;

/********************************* GRAPH **********************************/

function draw_graph(){
    console.log(">>> Draw Graph");
    var series = [];
    var bmc_lines = []; var bmc_bands = [];
    var nsamples = _ACTIVE_GRAPH_IDS_.length;
    var colors = ['#0d233a','#2f7ed8','#8bbc21','#910000','#1aadce',
                  '#492970','#f28f43','#77a1e5','#c42525','#a6c96a'];
    var symbols = ["circle","square","diamond","triangle","triangle-down"];
    var xmin = 1; var xmax = 1; var ymin = 1; var ymax = 1;
    var idx = 0;
    $.each(_ACTIVE_GRAPH_IDS_, function(index,sample_id){
        var sample = _DATA_.samples[sample_id];
        var points = _DATA_.points[sample_id];
        var curves = _DATA_.curves[sample_id];
        var bmc = _DATA_.BMC[sample_id]
        var bounds = _DATA_.bounds[sample_id];
        var anchors = _DATA_.anchors[sample_id];
        var symbol = symbols[index % symbols.length]
        if (points){
            xmin = Math.min(xmin,bounds[0])
            xmax = Math.max(xmax,bounds[1])
            ymin = Math.min(-1,ymin,bounds[2])
            ymax = Math.max(ymax,bounds[3])
            var nexp = Object.keys(points).length ;
            $.each(points, function(exp){
                var color = colors[idx % colors.length];
                series.push.apply(series, [{
                    type: 'scatter',
                    name: sample.name+'['+exp+']',
                    data: points[exp],
                    marker: {radius:2.5, symbol:symbol},
                    legendIndex: index,
                    color: color,
                }, {
                    type: 'spline',
                    name: sample.name+'['+exp+']',
                    data: curves[exp],
                    enableMouseTracking: false,
                    stickyTracking: false,
                    marker: {enabled: false},
                    //linkedTo: index,
                    //legendIndex: nsamples+index,
                    color: color,
                }]);
                idx++;
            });
        }
        if (anchors){
            var color = colors[(idx-1) % colors.length];
            console.log(anchors)
            series.push({
                type: 'scatter',
                marker: {symbol:'diamond', radius:7, fillColor:color},
                data: [anchors],
                name: 'anchor',
            })
        }
        if (bmc){
            var color = colors[(idx-1) % colors.length];
            bmc_lines.push.apply(bmc_lines, [{
                value: bmc[0],
                width: 1,
                color: color,
                label: {text: 'BMC', style: {color: '#606060'},
                }
            }, {
                value: bmc[1],
                width: 1,
                color: color,
                dashStyle: 'Dash',
                label: {text: 'BMCL', style: {color: '#606060'},
                }
            }]);
        }
    });

    _CHART_ = new Highcharts.Chart({
        chart: {renderTo: 'graph_container'},
        title: {text: 'BMC model'},
        xAxis: {title: {text: 'Concentration'},
                type: 'logarithmic',
                min: xmin,
                max: xmax,
                //gridLineWidth: 1,
                plotLines: bmc_lines,
               },
        yAxis: {title: {text: 'Viability (% of control)'},
                type: 'linear',
                min: ymin,
                max: ymax,
                //gridLineWidth: 1,
               },
        legend: {enabled: true},
        series: series
    });
    print_log();
    update_results();
    return _CHART_;
}
// Remove all series in the graph
function clear_graph(){
    for (i in _CHART_.series){
        _CHART_.series[i].setData([]);
    }
}

/******************************* ON PAGE LOAD *********************************/

// On page reload: read localStorage, check boxes, get data and redraw table+graph
function on_page_load(){
    load_active_samples();
    check_active_samples();
    get_data_and_redraw();
}
function show_loading_gif(){
    $('#loading').append($('<img>', {
        src: _IMG_URL_+'/loading.gif',
        alt: "[loading.gif]",
        height: "50", width: "50",
    }));
}
function hide_loading_gif(){
    $('#loading img').remove();
}
function bind_remove_sample_buttons(){
    $('.remove_sam').click(function() {
        //$(this.parentNode).remove();
        //remove_sample();
    });
}

/******************************* SAMPLE SWITCH *********************************/

// Switch the displayed table according to the selected checkboxes, and redraw.
function change_sample_graph(button){
    console.log(">>> Change Samples Graph -->");
    _ACTIVE_GRAPH_IDS_ = [];
    $('input:checkbox[name=samples_graph]:checked').each(function(){
        _ACTIVE_GRAPH_IDS_.push(parseInt($(this).val()));
    });
    update_local('active_samples',_ACTIVE_GRAPH_IDS_);
    // check if all samples marked as 'graph active' are in _DATA_
    var already_loaded = _ACTIVE_GRAPH_IDS_.every(function(x){return $.inArray(x,_DATA_.curves)});
    if (already_loaded){
        draw_graph();
    } else {
        get_data_and_redraw();
    }
    return _ACTIVE_GRAPH_IDS_;
}
function change_sample_table(button){
    console.log(">>> Change Sample Table -->");
    _ACTIVE_TABLE_ID_ = parseInt($(button).val());
    update_local('active_table',[_ACTIVE_TABLE_ID_])
    update_results();
    create_table(_DATA_.points[_ACTIVE_TABLE_ID_]);
    return _ACTIVE_TABLE_ID_;
}
// Fetch in `localStorage` which samples were plotted and re-check the respective checkboxes
function boxcheck_active_samples(){
    var active_ids = get_local('active_samples');
    $.each(active_ids,function(i,sample_id){
        $('input:checkbox[name=samples_graph][value='+sample_id+']').prop('checked',true);
    });
    return active_ids;
}
// Fetch in `localStorage` which table was active and re-check the respective radio button
function radiocheck_active_table(){
    var active_id = get_local('active_table')[0];
    if (active_id == undefined){
        active_id = $('input:radio[name=samples_table]:first').val()
    }
    $('input:radio[name=samples_table][value='+active_id+']').prop('checked',true);
    return active_id;
}
// Both of the above
function check_active_samples(){
    console.log(">>> Check Radio/Boxes Of Active Samples:",_ACTIVE_GRAPH_IDS_,_ACTIVE_TABLE_ID_);
    boxcheck_active_samples();
    radiocheck_active_table();
}
// Set global variables from localStorage
function load_active_samples(){
    console.log(">>> Load Active Samples (localStorage)");
    _ACTIVE_GRAPH_IDS_ = get_local('active_samples');
    _ACTIVE_TABLE_ID_ = get_local('active_table')[0];
}
function remove_sample(sample_id){
    _ACTIVE_GRAPH_IDS_.splice($.inArray(sample_id,_ACTIVE_GRAPH_IDS_), 1);
    if (sample_id == _ACTIVE_TABLE_ID_){
        if (_ACTIVE_GRAPH_IDS_.length > 0) {
            _ACTIVE_TABLE_ID_ = _ACTIVE_GRAPH_IDS_[0];
        } else {
            _ACTIVE_TABLE_ID_ = undefined;
        }
    }
    update_local('active_samples',_ACTIVE_GRAPH_IDS_);
    update_local('active_table',[_ACTIVE_TABLE_ID_]);
    delete _DATA_.points[sample_id];
    delete _DATA_.curves[sample_id];
    delete _DATA_.samples[sample_id];
    create_table();
}

/******************************* LOCAL STORAGE *********************************/

// keys: 'active_samples', 'active_table'

// Keep existing, add a list of new ids to the localStorage under *key*
function add_to_local(key,newids){
    console.log(">>> Add to Active Samples", newid);
    ids = get_local(key);
    for (i in newids){
        var newid = newids[i];
        if ($.inArray(newid,ids) == -1){
            ids.push(newid);
        }
    }
    update_local(key,ids)
    return ids;
}
// If there are ids corresponding to *key*, return a list of them
function get_local(key){
    var val = localStorage.getItem(key);
    if (val){ ids = JSON.parse(val); }
    else { ids = []; }
    return ids;
}
// Replace the current list of ids for *key* in the localStorage
function update_local(key,ids){
    localStorage.setItem(key,JSON.stringify(ids));
    return ids;
}

/********************************** SERVER EXCHANGE **********************************/

/* Update data (POST), compute the fitting curves and redraw. *measurements* must be
   of the form `{sample_id:[(dose,response,exp),]}`.
   Measurements are modified in the DB according to *measurements*.
   Samples determine the POST response and ultimately the graph and table.
*/
function post_data_and_redraw(measurements){
    console.log(">>> Post Data And Redraw");
    show_loading_gif();
    var sample_ids = all_active_samples();
    var tosend = {'measurements':measurements, 'samples':sample_ids};
    $.post(_JSON_URL_,
        JSON.stringify(tosend),
        function(data_response) {
            update_all(data_response);
        }, "json"
    );
}
// Update data (GET) for all active ids, update plot and table
function get_data_and_redraw(){
    console.log(">>> Get Data And Redraw");
    show_loading_gif();
    var sample_ids = all_active_samples();
    $.getJSON(_JSON_URL_,
        JSON.stringify(sample_ids),
        function(data_response){
            update_all(data_response);
        }
    );
}
// Update _DATA_, recreate the table, redraw
function update_all(newdata){
    _DATA_ = newdata;
    create_table();
    draw_graph();
    hide_loading_gif();
}
// Send the (possibly edited) table data, and the active samples for redrawing
function update_event(){
    console.log(">>> Update Event");
    var measurements = {};
    if (_ACTIVE_TABLE_ID_){
        measurements[_ACTIVE_TABLE_ID_] = read_data_from_table();
    }
    //} else if (measurements) { // custom entries
    //    measurements = {-1: measurements};
    //    samples = {-1: {'id':-1,'name':'custom','sha1':''}}
    post_data_and_redraw(measurements);
    check_active_samples();
}
// Clear Measurement and Sample tables from the database, and clear localStorage
function clear_all_db(){
    console.log(">>> Clear All DB");
    if (_CHART_) {_CHART_.destroy();}
    localStorage.clear();
    $('#samples_container form').empty();
    $('#results').empty();
    $.post(_CLEAR_ALL_DB_URL_,true,function(e){
        get_data_and_redraw();
        //location.reload();
    });
}
// Return the union of graph- and table active samples
function all_active_samples(){
    //var sample_ids = _ACTIVE_GRAPH_IDS_.slice(0);
    //if ($.inArray(_ACTIVE_TABLE_ID_,sample_ids) == -1) {
    //    sample_ids.push(_ACTIVE_TABLE_ID_);
    //}
    var sample_ids = [];
    $('#samples_container input:radio').each(function(i,elt){
        sample_ids.push($(elt).val());
    })
    return sample_ids;
}

/********************************** TABLE ***********************************/

// Read data from table
function read_data_from_table(){
    console.log(">>> Read Data From Table");
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
    console.log(">>> Create Table", points);
    if (typeof(points)==='undefined') {
        points = _DATA_.points[_ACTIVE_TABLE_ID_];
    }
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
    if (typeof(d)==='undefined') d=''; // dose
    if (typeof(r)==='undefined') r=''; // response
    if (typeof(e)==='undefined') e=''; // experiment
    var newline = '<td><input class="dose_in"></td><td><input class="response_in"></td>'
                + '<td><input class="experiment_in"></td>';
    var delete_button = $('<td>').addClass('remove_mes').html('x')
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
            if (L[2] == undefined) {experiment = '1';}
            else {experiment = L[2];}
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
            var sname = file.name.replace(/\.[^/.]+$/, "")
            var newsample = {'sha1':sha1, 'name':sname}
            $.post(_NEW_SAMPLE_URL_,
                   JSON.stringify(newsample),
                   function(data_response){
                       //if (data_response['new'] == true) {}
                       newsample.id = data_response['id'];
                       _ACTIVE_GRAPH_IDS_ = add_to_local('active_samples',[newsample.id]);
                       _ACTIVE_TABLE_ID_ = update_local('active_table',[newsample.id])[0];
                       check_active_samples();
                       _DATA_.samples[newsample.id] = newsample;
                       update_samples_list(newsample);
                       var measurements = {};
                       measurements[newsample.id] = read_data_from_table();
                       post_data_and_redraw(measurements);
                   }, "json"
            );
    }
    reader.error = function(e){
        console.log('Error while reading file\n', e);
    }
    reader.readAsText(file);
}

function update_samples_list(sample){
    console.log('>>> Update samples boxes/radio');
    // checkboxes
    var thisinput = $('#graph_samples_container input[value='+sample.id+']');
    var delete_button = $('<span>').addClass('remove_sam').append('x');
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
        $('#graph_samples_container form').append(newinput).append(sample.name).append(delete_button).append("<br>");
    }
    // radio buttons
    var thisinput = $('#table_samples_container input[value='+sample.id+']');
    var delete_button = $('<span>').addClass('remove_sam').append('x');
    //var dl_button = $('<a>', {href:_GETFILE_URL_, 'class':'dl_norm_data'}).append('Download');
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
        $('#table_samples_container form').append(newinput).append(sample.name).append(delete_button).append("<br>");
    }
}

function load_sample_data(){
    console.log('Not yet implemented')
}

/********************************** LOG ***********************************/

// Print the R output - or more - inside the #log div
function print_log(){
    var logbox = $('#log .log_content');
    logbox.text('');
    $.each(_DATA_.loglist, function(index,logstring){
        logbox.append("<p>"+logstring+"</p>");
    })
}

/********************************** LOG ***********************************/

function update_results(){
    var bmc = _DATA_.BMC[_ACTIVE_TABLE_ID_];
    if (bmc){
        var bmc_val = $('<p>', {text: 'BMC : '+bmc[0]});
        var bmcl_val = $('<p>', {text: 'BMCL : '+bmc[1]});
        //var nextval = $('<p>', {text: 'Next : '+next_val});
        $('#results').empty().append(bmc_val).append(bmcl_val);
    }
}
