import pandas as pd 
import os
import numpy as np
import matplotlib.pyplot as plt

rewards_filename = "reward_loss.csv"
dsr_filename = "dsr.csv"
ablation_folder = "ablation"

mem_exp_folders = ["dec22-memory-50","dec21-memory-100","dec20-memory-200","dec21-memory-500"]
mem_values = ["050", "100", "200", "500"]

mineps_exp_folders =["jan15-mem-100-epsmin-0","dec29-memory-100-epsmin-0.01","dec26-memory-100-epsmin-0.05","dec21-memory-100"]
mineps_values = ["0p00", "0p01", "0p05", "0p10"]


df_list_rewards = []
df_list_dsr = []
for i,folder_name in enumerate(mem_exp_folders):
	df_list_rewards.append(pd.read_csv(ablation_folder+"/"+folder_name+"/"+rewards_filename,names=["reward_mem"+mem_values[i]]))
	df_list_dsr.append(pd.read_csv(ablation_folder+"/"+folder_name+"/"+dsr_filename,names=["dsr_mem"+mem_values[i]]))

mem_exp_rewards_df = pd.concat(df_list_rewards, axis=1)
mem_exp_rewards_df[:3999].to_csv("mem_rewards.csv")

mem_exp_dsr_df = pd.concat(df_list_dsr, axis=1)
mem_exp_dsr_df[:3999].to_csv("mem_dsr.csv")



df_list_rewards = []
df_list_dsr = []
for i,folder_name in enumerate(mineps_exp_folders):
	df_list_rewards.append(pd.read_csv(ablation_folder+"/"+folder_name+"/"+rewards_filename,names=["reward_mineps"+mineps_values[i]]))
	df_list_dsr.append(pd.read_csv(ablation_folder+"/"+folder_name+"/"+dsr_filename,names=["dsr_mineps"+mineps_values[i]]))

mineps_exp_rewards_df = pd.concat(df_list_rewards, axis=1)
mineps_exp_rewards_df[:3999].to_csv("mineps_rewards.csv")

mineps_exp_dsr_df = pd.concat(df_list_dsr, axis=1)
mineps_exp_dsr_df[:3999].to_csv("mineps_dsr.csv")






# mem_exp_df[:3999].plot()
# plt.show()

# mem_exp_df["reward_500"][:3999].diff().plot()
# plt.show()