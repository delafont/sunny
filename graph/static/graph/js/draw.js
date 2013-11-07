

/**************************** GLOBAL VARIABLES ****************************/

var _USER_;
var _JSON_URL_;
var _NEW_SAMPLE_URL_;
var _REMOVE_SAMPLE_URL_;
var _CLEAR_ALL_DB_URL_;
var _DATA_;
var _CHART_;
var _ACTIVE_GRAPH_IDS_ = [];
var _ACTIVE_TABLE_ID_;
var _IMG_URL_;
var _GETFILE_URL_;
var _UPDATE_ACTIVE_URL_;

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
        var bmc = _DATA_.BMC[sample_id];
        var bounds = _DATA_.bounds[sample_id];
        var anchors = _DATA_.anchors[sample_id];
        var symbol = symbols[index % symbols.length];
        if (points){
            xmin = Math.min(xmin,bounds[0]);
            xmax = Math.max(xmax,bounds[1]);
            ymin = Math.min(-1,ymin,bounds[2]);
            ymax = Math.max(ymax,bounds[3]);
            var nexp = Object.keys(points).length ;
            $.each(points, function(exp){
                var color = colors[idx % colors.length];
                series.push.apply(series, [{
                    type: 'scatter',
                    name: sample.name+'['+exp+']',
                    data: points[exp],
                    stickyTracking: false,
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
            series.push({
                type: 'spline',
                name: 'Pooled '+sample.name,
                data: curves['pooled'],
                enableMouseTracking: false,
                stickyTracking: false,
                marker: {enabled: false},
                color: 'black',
                dashStyle: 'ShortDash',
            });
        }
        if (anchors){
            var color = colors[(idx-1) % colors.length];
            series.push({
                type: 'scatter',
                marker: {symbol:'diamond', radius:7, fillColor:'black'},
                data: [anchors],
                name: 'Anchor '+sample.name,
            });
        }
        if (bmc && bmc['10']){
            var color = colors[(idx-1) % colors.length];
            bmc_lines.push.apply(bmc_lines, [{
                value: bmc['10'][0],
                width: 1,
                color: color,
                label: {text: 'BMC 10', style: {color: '#606060'},
                }
            }, {
                value: bmc['10'][1],
                width: 1,
                color: color,
                dashStyle: 'Dash',
                label: {text: 'BMCL 10', style: {color: '#606060'},
                }
            }]);
        }
    });

    _CHART_ = new Highcharts.Chart({
        chart: {renderTo: 'chart'},
        title: {text: ''},
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
    update_BMC_display_block();
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
    update_local('active_table',[_ACTIVE_TABLE_ID_]);
    // Got _ACTIVE_TABLE_ID_ from DB the first time, so that it works across browsers
    // and sessions, then put it in LocalStorage so that it works faster.
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
    $('#loading img:first').remove();
}
function bind_remove_sample_buttons(){
    $('.remove_sam').click(function() {
        //$(this.parentNode).remove();
        //remove_sample();
    });
}

/******************************* SAMPLE SWITCH *********************************/

// Switch the displayed graphs according to the selected checkboxes.
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
// Switch the displayed table according to the selected radio button.
function change_sample_table(button){
    console.log(">>> Change Sample Table -->");
    _ACTIVE_TABLE_ID_ = parseInt($(button).val());
    update_local('active_table',[_ACTIVE_TABLE_ID_])
    $.post(_UPDATE_ACTIVE_URL_, _ACTIVE_TABLE_ID_.toString());
    update_BMC_display_block();
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

// Set active samples global variables from localStorage
function load_active_samples(){
    console.log(">>> Load Active Samples (localStorage)");
    _ACTIVE_GRAPH_IDS_ = get_local('active_samples');
    _ACTIVE_TABLE_ID_ = get_local('active_table')[0];
}

// Create new sample sample on click on the button
function create_new_sample_onclick(){
    var newsample_name = prompt("Sample name:");
    var newsample = {'sha1':random_string(20), 'name':newsample_name};
    create_table({});
    create_new_sample(newsample);
}
// Check if the sha1 exists in database, if not creates a new Sample instance and updates all
// *newsample* is an object of the type {'name':.., 'sha1':..}
function create_new_sample(newsample){
    console.log(">>> New Sample", newsample);
    $.post(_NEW_SAMPLE_URL_,
           JSON.stringify(newsample),
           function(data_response){
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

// Remove sample on click on the red cross in front of the sample name
function remove_sample_onclick(button){
    var this_li = $(button).parent();
    var sample_id = $('input', this_li).val();
    remove_sample(sample_id);
    $('#samples_container input[value='+sample_id+']').parent('li').remove();
}
function remove_sample(sample_id){
    console.log(">>> Remove Sample", sample_id);
    $.each(_DATA_, function(key,val){
        if (val[sample_id]){
            delete _DATA_[key][sample_id];
        }
    });
    _ACTIVE_GRAPH_IDS_.splice($.inArray(sample_id,_ACTIVE_GRAPH_IDS_), 1); // remove
    for (var sid in _DATA_.samples) {break;} // first sample id found
    if (sample_id == _ACTIVE_TABLE_ID_){ // if we remove the currently selected table id
        _ACTIVE_TABLE_ID_ = sid;
        _ACTIVE_GRAPH_IDS_.push(_ACTIVE_TABLE_ID_);
    }
    update_local('active_samples',_ACTIVE_GRAPH_IDS_);
    update_local('active_table',[_ACTIVE_TABLE_ID_]);
    $.post(_REMOVE_SAMPLE_URL_, sample_id);
    $.post(_UPDATE_ACTIVE_URL_, _ACTIVE_TABLE_ID_.toString());
    check_active_samples();
    create_table();
    draw_graph();
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
    var wanna_destroy = confirm("Are you sure?");
    if (wanna_destroy == true){
        if (_CHART_) {_CHART_.destroy();}
        localStorage.clear();
        $('#samples_container ul').empty();
        $('#results').empty();
        _ACTIVE_TABLE_ID_ = undefined;
        _ACTIVE_GRAPH_IDS_ = [];
        $.post(_CLEAR_ALL_DB_URL_,true,function(e){
            get_data_and_redraw();
            //location.reload();
        });
    }
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
    $('#input_table .datarow').remove();
    if (typeof(_ACTIVE_TABLE_ID_)==='undefined') {
        return;
    }
    if (typeof(points)==='undefined') {
        points = _DATA_.points[_ACTIVE_TABLE_ID_];
    }
    if ($.isEmptyObject(points)) {
        add_newline('','','','last');
    }
    for (exp in points){
        M = points[exp];
        N = M.length;
        if (N==0) { // no measurements yet, add a blank input line
            add_newline('','','','first');
        } else {
            for (var i=0; i<N; i++){
                add_newline(M[i][0],M[i][1],exp,'last');
            }
        }
    }
}
// Add a row to the input table with a Remove button, with class 'datarow'
// Position is 'first' or 'last' (element of the table).
function add_newline(d,r,e,position) {
    if (typeof(d)==='undefined') d=''; // dose
    if (typeof(r)==='undefined') r=''; // response
    if (typeof(e)==='undefined') e=''; // experiment
    var newline = '<td><input class="dose_in"></td><td><input class="response_in"></td>'
                + '<td><input class="experiment_in"></td>';
    var delete_button = $('<td>').addClass('remove_mes').html('x')
                                 .click(function() { $(this.parentNode).remove(); });
    if (position=='last'){
        $('#input_table tbody').append('<tr></tr>');
        var line = $('#tbody tr:'+position);
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
                    add_newline(dose,response,experiment,'last');
                }
            } else { // remove superfluous lines
                var glen = grid.length;
                for (var k=i; k<=glen; k++){
                    $(grid[k]).remove();
                }
                return false;
            }
        });
        // Create new sample if necessary, read the new table and redraw
        var sha1 = SHA1(e.target.result);
        // is it already on the current samples list?:
        //all_sha1 = [];
        //for (i in _DATA_.samples) { all_sha1.push(_DATA_.samples[i].sha1); }
        //if (sha1 in all_sha1){
        //    "Do nothing?"
        //} else {
            var sname = file.name.replace(/\.[^/.]+$/, "");
            var newsample = {'sha1':sha1, 'name':sname}
            create_new_sample(newsample);
    }
    reader.error = function(e){
        console.log('Error while reading file\n', e);
    }
    reader.readAsText(file);
}

function update_samples_list(sample){
    console.log('>>> Update samples boxes/radio');
    // Checkboxes
    var thisinput = $('#graph_samples_container input[value='+sample.id+']');
    var delete_button = $('<span>').addClass('remove_sam').append('x')
        .click(function(){remove_sample_onclick(this);});
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
        $('#graph_samples_container ul').append($('<li>').append(newinput)
            .append(sample.name).append(delete_button));
    }
    // Radio buttons
    var thisinput = $('#table_samples_container input[value='+sample.id+']');
    var delete_button = $('<span>').addClass('remove_sam').append('x')
        .click(function(){remove_sample_onclick(this);});
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
        $('#table_samples_container ul').append($('<li>').append(newinput)
            .append(sample.name).append(delete_button));
    }
}

function load_sample_data(){
    console.log('Not yet implemented');
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

/************************** BMC DISPLAY BLOCK *****************************/

function update_BMC_display_block(){
    var bmc = _DATA_.BMC[_ACTIVE_TABLE_ID_];
    if (bmc && bmc['10']){
        var bmc10_val = $('<p>', {text: 'BMC 10 : '+bmc['10'][0]});
        var bmcl10_val = $('<p>', {text: 'BMCL 10 : '+bmc['10'][1]});
        $('#results').empty().append(bmc10_val).append(bmcl10_val);
        var otherbmcs = $('<div>').addClass('otherbmcs');
        $('#results').append(otherbmcs);
        if (bmc['15']){
            var bmc15_val = $('<span>', {text: 'BMC 15: '+bmc['15'][0]});
            var bmcl15_val = $('<span>', {text: 'BMCL 15 : '+bmc['15'][1]});
            otherbmcs.append(bmc15_val).append(bmcl15_val);
            if (bmc['50']){
                otherbmcs.append('<br>')
                var bmc50_val = $('<span>', {text: 'BMC 50: '+bmc['50'][0]});
                var bmcl50_val = $('<span>', {text: 'BMCL 50 : '+bmc['50'][1]});
                otherbmcs.append(bmc50_val).append(bmcl50_val);
            }
        }
    }
}


/*#------------------------------------------------------#
  # This code was written by Julien Delafontaine         #
  # Bioinformatics and Biostatistics Core Facility, EPFL #
  # http://bbcf.epfl.ch/                                 #
  # webmaster.bbcf@epfl.ch                               #
  #------------------------------------------------------#*/
