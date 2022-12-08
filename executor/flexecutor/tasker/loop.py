import sys

def run_loop_task(loop_count):
    sum = 0
    for i in range(loop_count):
        sum += 1
    return sum

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("needs loop count as arg")
        sys.exit(1)

    run_loop_task(int(sys.argv[1]))
