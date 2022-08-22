from threading import Thread, Lock

n = 5000
lock = Lock()


def func1():
    global n
    for i in range(1000000):
        lock.acquire()
        n = n - 1
        lock.release()


def func2():
    global n
    for i in range(1000000):
        lock.acquire()
        n = n + 1
        lock.release()


t1 = Thread(target=func1)
t2 = Thread(target=func2)

t1.start()
t2.start()

t1.join()
t2.join()

print(n)


"""
-1  +1
x = n - 1  # x=4999
n = x      # n=4999
x = n + 1  # x=5000
n = x      # n=5000
"""

"""
-1  +1
x = n - 1  # x=4999
x = n + 1  # x=5001
n = x      # n=5001
n = x      # n=5001
"""

