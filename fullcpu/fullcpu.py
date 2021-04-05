from concurrent.futures import ProcessPoolExecutor


def compute():
    i = 0
    while True:
        i = (i + 1) % 100000


if __name__ == '__main__':
    n = 20
    with ProcessPoolExecutor(n) as pool:
        for i in range(n):
            pool.submit(compute)
