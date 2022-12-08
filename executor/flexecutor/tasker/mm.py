import numpy as np
import sys

def run_mm_task(a, b):
    return np.matmul(a,b)


if __name__ == '__main__':
    mat_size = int(sys.argv[1])
    a = np.random.randint(256, size=(mat_size,mat_size))
    b = np.random.randint(256, size=(mat_size,mat_size))
    print(run_mm_task(a, b))
