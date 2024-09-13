#!/bin/sh

set -u

perf=/usr/lib/linux-tools/4.15.0-213-generic/perf

printf "Object classification:\n"
for i in 0 1 2 3 4 5 6 7 8 9
do
	printf "    image = dog%d\n" "$i"
	for _i in 0 1 2 3 4 5 6 7 8 9
	do
		$perf stat -e instructions:u python obj_detection.py \
			"../../../mock-offloader/moffloader/obj_det_input_files/dog$i".jpg 2>&1 \
			| grep -Eo '^.+instructions' \
			| grep -Eo '[0-9,]+'
	done
done

printf "Room classification:\n"
for i in 0 1 2 3 4 5 6 7 8 9
do
	printf "    image = room%d\n" "$i"
	for _i in 0 1 2 3 4 5 6 7 8 9
	do
		$perf stat -e instructions:u python room_classification/room_classification.py \
			"~/free-loaders/mock-offloader/moffloader/room_classification_input_files/room$i".jpg \
			| grep -Eo '^.+instructions' \
			| grep -Eo '[0-9,]+'
	done
done

exit 0
