import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import pandas as pd
import numpy as np
from matplotlib import cm

cmpa=cm.get_cmap(name='Set3')

plt.rcParams.update({'font.size': 12})
plot_linewidth = 0.25

rewards = pd.read_csv("mem_rewards.csv")

fig, ax = plt.subplots() #figsize=(5, 3)

ax.plot(rewards["reward_mem050"], label="Memory = 50")
ax.plot(rewards["reward_mem100"], label="Memory = 100")
ax.plot(rewards["reward_mem200"], label="Memory = 200")
ax.plot(rewards["reward_mem500"], label="Memory = 500")
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.legend()
ax.grid(linewidth=plot_linewidth, zorder=0)
ax.set_ylabel('Accumulative Rewards')
ax.set_xlim([0, None])
ax.set_ylim([0, 3000])

plt.xlabel('Number of Task Offloads')
plt.xticks(np.arange(0, 4000+1, 1000))
plt.yticks(np.arange(0, 3000+1, 1000))
plt.tight_layout()
plt.savefig(f'ablation-mem-rewards.pdf')
plt.show()

