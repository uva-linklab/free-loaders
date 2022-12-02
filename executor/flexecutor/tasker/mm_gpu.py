import sys
import cupy as cp

def run_mm_task_gpu(a, b):
    res = cp.matmul(a,b)
    cp.cuda.Stream.null.synchronize()
    return res


if __name__ == '__main__':
    # https://stackoverflow.com/questions/64409663/why-is-my-gpu-slower-than-cpu-in-matrix-operations
    mat_size = int(sys.argv[1])

    a = cp.random.randint(256, size=(mat_size,mat_size))
    b = cp.random.randint(256, size=(mat_size,mat_size))
    print(run_mm_task_gpu(a, b))
