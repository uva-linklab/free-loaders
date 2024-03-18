#!/bin/bash

set -e
set -u


FL_PATH=${FL_PATH:-~/free-loaders}
TASKER_PATH="$FL_PATH"/executor/flexecutor/tasker

PERF_PATH=${PERF_PATH:-/bin/perf}
# perf=/usr/lib/linux-tools/4.15.0-213-generic/perf

if [ ! -d "$FL_PATH" ]
then
    printf "fReeLoaders repository not found.\n"
    exit 1
fi

if [ ! -e "$PERF_PATH" ]
then
    printf "perf not found.\n"
    exit 1
fi

cd "$TASKER_PATH"

for i in 0 1 2 3 4 5 6 7 8 9
do
    total_ins=0
    for _i in 0 1 2 3 4 5 6 7 8 9
    do
        trial_ins=$( $PERF_PATH stat -e instructions:u python3 loop.py "$i"000000 2>&1 \
            | grep -Eo '^.+instructions' \
            | grep -Eo '[0-9,]+' \
            | tr -d ',' )
        total_ins=$(($total_ins + $trial_ins))
    done
    max_resident=$( /usr/bin/time -f '%M' python3 loop.py "$i"000000 2>&1 >/dev/null )
    average_ins=$(( $total_ins / 10 ))
    printf "Loop, %d = %d, %d\n" "$i" "$average_ins" "$max_resident"
done

for i in 500 556 611 667 722 778 833 889 944 1000
do
    total_ins=0
    for _i in 0 1 2 3 4 5 6 7 8 9
    do
        trial_ins=$( $PERF_PATH stat -e instructions:u python3 mm.py $i 2>&1 \
            | grep -Eo '^.+instructions' \
            | grep -Eo '[0-9,]+' \
            | tr -d ',' )
        total_ins=$(( $total_ins + $trial_ins ))
    done

    max_resident=$( /usr/bin/time -f '%M' python3 mm.py $i 2>&1 >/dev/null )
    average_ins=$(( $total_ins / 10 ))
    printf "Matrix, %dx%d = %d, %d\n" "$i" "$i" "$average_ins" "$max_resident"
done

for i in 44100 88200 132300 176400 220500 264600 308700 352800 396900 441000
do
    total_ins=0
    for _i in 0 1 2 3 4 5 6 7 8 9
    do
        trial_ins=$( $PERF_PATH stat -e instructions:u python3 fft.py $i 2>&1 \
            | grep -Eo '^.+instructions' \
            | grep -Eo '[0-9,]+' \
            | tr -d ',' )
        total_ins=$(( $total_ins + $trial_ins ))
    done

    max_resident=$( /usr/bin/time -f '%M' python3 fft.py $i 2>&1 >/dev/null )
    average_ins=$(( $total_ins / 10 ))
    printf "FFT, %d = %d, %d\n" "$i" "$average_ins" "$max_resident"
done

printf "HAR:\n"
for i in 1 2 3 4 5 6 7 8 9 10
do
    total_ins=0
	for _i in 0 1 2 3 4 5 6 7 8 9
	do
		trial_ins=$( $PERF_PATH stat -e instructions:u python3 har/human_act_rec.py $i 2>&1 \
			| grep -Eo '^.+instructions' \
			| grep -Eo '[0-9,]+' \
            | tr -d ',' )
        total_ins=$(( $trial_ins + $total_ins ))
	done

    max_resident=$(/usr/bin/time -f '%M' python3 har/human_act_rec.py $i 2>&1 >/dev/null)
    average_ins=$(( $total_ins / 10 ))
    printf "HAR, %d = %d, %d\n" "$i" "$average_ins" "$max_resident"
done

printf "Object classification:\n"
for i in 0 1 2 3 4 5 6 7 8 9
do
    total_ins=0
	for _i in 0 1 2 3 4 5 6 7 8 9
	do
		trial_ins=$( $PERF_PATH stat -e instructions:u python3 obj_detection.py \
			"$FL_PATH/mock-offloader/moffloader/obj_det_input_files/dog$i".jpg \
			| grep -Eo '^.+instructions' \
			| grep -Eo '[0-9,]+' \
            | tr -d ',' )
        total_ins=$(( $trial_ins + $total_ins ))
	done

    max_resident=$(/usr/bin/time -f '%M' python3 obj_detection.py \
                                 "$FL_PATH/mock-offloader/moffloader/obj_det_input_files/dog$i.jpg" \
                                 $i 2>&1 >/dev/null)
    average_ins=$(( $total_ins / 10 ))
    printf "Object classification, %d = %d, %d\n" "$i" "$average_ins" "$max_resident"
done

printf "Room classification:\n"
for i in 0 1 2 3 4 5 6 7 8 9
do
    total_ins=0
	for _i in 0 1 2 3 4 5 6 7 8 9
	do
		trial_ins=$( $PERF_PATH stat -e instructions:u python3 room_classification/room_classification.py \
			"$FL_PATH/mock-offloader/moffloader/room_classification_input_files/room$i".jpg \
			| grep -Eo '^.+instructions' \
			| grep -Eo '[0-9,]+' \
            | tr -d ',' )
	done

    max_resident=$(/usr/bin/time -f '%M' python3 har/human_act_rec.py $i 2>&1 >/dev/null)
    average_ins=$(( $total_ins / 10 ))
    printf "Room classification, %d = %d, %d\n" "$i" "$average_ins" "$max_resident"
done

exit 0
