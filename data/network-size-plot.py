import matplotlib.pyplot as plt
import numpy as np

# Sample data (replace with your actual latency measurements)
scheduler = [
    'fReeLoaders',
    'HEROS', '''performance-
priority''',
    '''energy-
priority''',
    'WRR',
    'load balancer',
    'random',
]

offload_req = [88 for x in range(7)]
offload_res = [23 for x in range(7)]
stat_req = [50, 50, 50, 50, 0, 50, 0]
stat_res = [142, 172, 158, 158, 0, 158, 0]

# Create stacked bar chart
import matplotlib.figure as pltf
w, h = pltf.figaspect(.5)
fig, ax = plt.subplots(figsize=(w,h,))
# fig.subplots_adjust(bottom=0.15)

# Plot the bars
ax.bar(scheduler, offload_req, label='offload req.', color=[110 / 255, 96 / 255, 128 / 255])
ax.bar(scheduler, offload_res, label='offload resp.',
       bottom=offload_req,
       color=[186 / 255, 155 / 255, 224 / 255])
ax.bar(scheduler, stat_req, label='state req.',
       bottom=np.array(offload_req) + np.array(offload_res),
       color=[135 / 255, 107 / 255, 103 / 255])
ax.bar(scheduler, stat_res, label='state resp.',
       bottom=np.array(offload_req) + np.array(offload_res) + np.array(stat_req),
       color=[209 / 255, 139 / 255, 128 / 255])

# Add labels, title, and legend
ax.grid(axis='y')
ax.set_axisbelow(True)
ax.set_ylim(0, 350)

ax.set_ylabel('bytes TX', fontsize=16)
# ax.set_xlabel('scheduler', fontsize=16)
ax.legend(reverse=True)

def af(val, _pos):
    return '{} B'.format(int(val))
from matplotlib import ticker
ax.yaxis.set_major_formatter(ticker.FuncFormatter(af))

plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)

plt.savefig('/tmp/network-size.pdf', format='pdf', dpi='figure', pad_inches=0.1)
