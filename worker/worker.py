import time


class Worker(object):
    def __init__(self):
        print("Initializing worker")
        time.sleep(10)
        print("Initialized worker")

    def __call__(self, x, y):
        print("Worker doing important work")
        time.sleep(2)
        z = x + y
        print("Worker done.")
        return z


if __name__ == "__main__":
    worker = Worker()
    worker(1, 2)
