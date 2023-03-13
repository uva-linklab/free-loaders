import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
from matplotlib import cm

cmpa=cm.get_cmap(name='Set3')

plt.rcParams.update({'font.size': 12})


x_labels = ["Loops\n(Light)","Loops\n(Heavy)","FFT\n(Light)","FFT\n(Heavy)","Matrix\nMult.\n(Light)","Matrix\nMult.\n(Heavy)"] 

barWidth = 0.40


exec_time_alpha1 = np.array([363.117772599925,
	    				   	 822.710326223662,
	    				   	 514.102648604999,
	    				   	 2598.86405058205,
	    				   	 3183.98770093917,
	    				   	 5025.99335943951
])

exec_time_alpha0 = np.array([450.304364504879,
				             1696.26217105171,
				             497.73739851438,
				             2539.19204218047,
				             3229.12590687091,
				             6027.9245564318
])

energ_cons_alpha1 = np.array([3.11738039833911,
							  24.4958680581865,
							  0.863682600675207,
							  5.25188531067222,
							  163.9494452,
							  150.7019928
])

energ_cons_alpha0 = np.array([0.467017023628705,
							  4.61692646724527,
							  0.123803481436692,
							  1.05334712515984,
							  8.62191297300045,
							  10.6246580516071
])

exec_time_reduction = [100*(1-y/x) for (x,y) in zip(exec_time_alpha0,exec_time_alpha1)]
energ_cons_reduction = [100*(1-y/x) for (x,y) in zip(energ_cons_alpha1,energ_cons_alpha0)] 

for i,task in enumerate(x_labels):
	print("==============================================================")
	print("Task type: "+"".join(task.split("\n")))
	print("Execution time reduction: "+str(exec_time_reduction[i])[0:5]+"%")
	print("Energy consumption reduction: "+str(energ_cons_reduction[i])[0:5]+"%")
print("==============================================================")



r1 = np.arange(len(x_labels))
r2 = [x + barWidth for x in r1]

rcenter = [x + 0.5*barWidth for x in r1]

plt.bar(r1, exec_time_reduction, color=cmpa(4), width=barWidth, edgecolor='white', label="Execution time reduction",zorder=2)
plt.bar(r2, energ_cons_reduction, color=cmpa(6), width=barWidth, edgecolor='white', label="Energy consumption reduction",zorder=2) 

plt.xticks(rcenter, x_labels)
plt.ylabel('Reduction (%)')
plt.xlabel('Type of tasks')
plt.ylim(ymin=0,ymax=100)
plt.grid(linewidth=0.25, zorder=0)
# Create legend & Show graphic
plt.legend(prop={"size":11},bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left",mode="expand", borderaxespad=0, ncol=2)
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.gca().set_aspect(0.020)
plt.tight_layout()
plt.savefig(f'Operation_mode_comparison.pdf')

plt.show()

