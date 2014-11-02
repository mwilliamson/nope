import time


def retry(func, exceptions):
    interval = 0.01
    max_wait_time = 5
    
    start = time.time()
    
    while True:
        try:
            return func()
        except exceptions:
            if time.time() > start + max_wait_time:
                raise
            else:
                time.sleep(interval)
