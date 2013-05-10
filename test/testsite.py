from bottle import route, run, static_file

@route('/')
def index():
    return "This is the root"

@route('/<filename>')
def server_static(filename):
    return static_file(filename, 'static')

run(host='localhost', port=8080, debug=True)
