import sys
import numpy as np

def run_fft_task(signal):
    return np.fft.fft(signal)

if __name__ == '__main__':
    # audio is sampled usually at 22050 or 44100 samples per sec
    signal_size = int(sys.argv[1])
    a = np.random.normal(0, 0.5, size=signal_size)
    print(run_fft_task(a))
