from bottle import route, run, template
from bottle import static_file
import os, sys

@route('/')
def index():
    html = ''
    html += '<h3>My graph</h3>'
    html += '...HTML here...<br />'
    html += '<input></input>'
    os.system('./script.r')
    html += '<div><img src="static/mygraph.png"/></div>!'
    return html

@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root='./static/')

run(host='localhost', port=8080, debug=True, reloader=True)
