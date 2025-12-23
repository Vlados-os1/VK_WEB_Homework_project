import json
from urllib.parse import parse_qs

def simple_app(environ, start_response):
    method = environ.get('REQUEST_METHOD', 'GET')

    query_string = environ.get('QUERY_STRING', '')
    get_params = parse_qs(query_string)

    post_params = {}
    if method == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            request_body_size = 0

        if request_body_size > 0:
            request_body = environ['wsgi.input'].read(request_body_size)
            post_params = parse_qs(request_body.decode('utf-8'))

    status = '200 OK'
    headers = [('Content-Type', 'application/json; charset=utf-8')]

    response_data = {
        'method': method,
        'path': environ.get('PATH_INFO', '/'),
        'get_parameters': {k: v[0] if len(v) == 1 else v for k, v in get_params.items()},
        'post_parameters': {k: v[0] if len(v) == 1 else v for k, v in post_params.items()},
        'headers': {k: v for k, v in environ.items() if k.startswith('HTTP_')}
    }

    response_body = json.dumps(response_data, indent=2, ensure_ascii=False).encode('utf-8')

    start_response(status, headers)
    return [response_body]


application = simple_app

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    server = make_server('localhost', 8081, simple_app)
    server.serve_forever()