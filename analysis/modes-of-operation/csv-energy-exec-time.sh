#!/bin/bash
tid=$1
log_file_dir=$2
alpha_vals=("1.0" "0.0")

for alpha_val in "${alpha_vals[@]}"
do
   python energy-exec-time.py -tid "$tid" "$log_file_dir/alpha-$alpha_val.log"
done
