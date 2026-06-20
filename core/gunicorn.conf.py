import multiprocessing

# gthread = sync workers with threading.
worker_class = 'gthread'

# Number of workers
# Standard formula: (2 x CPU cores) + 1
if ((multiprocessing.cpu_count() * 2) + 1) > 9:
    workers = 9
else:
    workers = 4


# Each worker handles up to 4 concurrent requests
threads = 4

# Port 8000 internally -- nginx sits in front on port 1212 and forwards to this
bind = '0.0.0.0:8000'

# 0 = no timeout -- critical for large file
timeout = 0

keepalive = 5

# Logging
# '-' sends logs to stdout/stderr so Docker
# can capture them with 'docker logs'
accesslog = '-'
errorlog  = '-'
loglevel  = 'info'

proc_name = 'kornercloud'
