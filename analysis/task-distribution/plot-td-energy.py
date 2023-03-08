import csv
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm

loops = [8,0,0,0,0,2,0,294,971,0]
mat_mult = [201,0,0,0,0,2,0,98,1096,0]
fft = [4,0,0,0,0,0,0,276,1048,0]

cmpa=cm.get_cmap(name='Set3')
plt.rcParams.update({'font.size': 14})

x_labels = ["Nano","RPi3₁","RPi3₂","RPi4₁","RPi4₂","RPi4₃","RPi4₄","RPi4₅","TX2","Desktop"]
# with open('data-alpha-1.0.csv', newline='') as csvfile:
#     reader = csv.reader(csvfile, delimiter=',', quotechar='|')
#     for row in reader:
#         print(row)

bar_width = 0.30

r1 = np.arange(len(x_labels))
r2 = [x + bar_width for x in r1]
r3 = [x + bar_width for x in r2]
rcenter = [x + 1*bar_width for x in r1]

plt.bar(r1, loops, width=bar_width, color=cmpa(4), label='Loops',zorder=2)
plt.bar(r2, mat_mult, width=bar_width, color=cmpa(6), label='Matrix Mult.',zorder=2)
plt.bar(r3, fft, width=bar_width, color=cmpa(5), label='FFT',zorder=2)
# plt.title("Horiontally Stacked Bar Graphs")

plt.ylabel("No. of Offloads")
plt.xticks(rcenter, x_labels, rotation=45)

plt.grid(linewidth=0.25, zorder=0, axis='y')
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.tight_layout()
plt.legend()
plt.savefig('td-energy.pdf')
