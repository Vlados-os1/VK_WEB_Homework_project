bind = "0.0.0.0:8000"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

accesslog = "-"
errorlog = "-"
loglevel = "info"

limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

preload_app = True