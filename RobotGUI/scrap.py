import threading

i = 0
i_lock = threading.Lock()

def test():
    global i
    i_lock.acquire()
    for x in range(100000):
        i += 1

threads = [threading.Thread(target=test) for t in range(10)]
for t in threads:
    t.start()

for t in threads:
    t.join()

assert i == 1000000
