#!/usr/bin/env python

import argparse
import csv
import os
import os.path

LabelMapping = [
    ('others', {
        1: 'screeching',
        2: 'plastic crinkling',
        3: 'cleaning',
        4: 'gear',
    },),

    ('engine', {
        1: 'small engine',
        2: 'medium engine',
        3: 'large engine' }),

    ('machinery impact', {
        1: 'rock drill',
        2: 'jackhammer',
        3: 'hoe ram',
        4: 'pile driver',
    },),

    ('non-machinery impact', {
        1: 'glass breaking',
        2: 'car crash',
        3: 'explosion',
    },),

    ('powered saw', {
        1: 'chainsaw',
        2: 'small rotating saw',
        3: 'large rotating saw',
    },),

    ('alert signal', {
        1: 'car horn',
        2: 'car alarm',
        3: 'siren',
        4: 'reverse beeper',
    },),

    ('music', {
        1: 'stationary music',
        2: 'mobile music',
    },),

    ('human voice', {
        1: 'talking',
        2: 'shouting',
        3: 'large crowd',
        4: 'amplified speech',
        5: 'singing',
    },),

    ('human movement', {
        1: 'footsteps',
        2: 'clapping',
    },),

    ('animal', {
        1: 'dog barking',
        2: 'bird chirping',
        3: 'insect chirping',
    },),

    ('water', {
        1: 'hose pump',
    },),

    ('weather', {
        1: 'rain',
        2: 'thunder',
        3: 'wind',
    },),

    ('brake', {
        1: 'friction brake',
        2: 'exhaust brake',
    },),

    ('train', {
        1: 'electric train',
    },),
]

def main(args):

    # Output rows: file name, label
    output_rows = []

    for audio_file_name in _list_flac_files(args.samples):
        # Open its metadata CSV
        (audio_file_name_base, audio_file_ext) = os.path.splitext(audio_file_name)
        csv_file_name = '{}.csv'.format(audio_file_name_base)
        csv_path = os.path.join(args.labels, csv_file_name)
        try:
            with open(csv_path, 'r') as csv_fh:
                csvr = csv.reader(csv_fh)
                _headers = next(csvr)

                import subprocess
                for (row_no, row) in enumerate(csvr):
                    onset = float(row[5])
                    # print('{}'.format(row[2]))
                    raw_label = row[2]
                    if raw_label == '0-0':
                        continue

                    label = _map_label(raw_label)
                    print('{} -> {}'.format(audio_file_name_base, label))
                    # Create a name for the new file.
                    split_audio_file_name = '{}-{}.flac'.format(row[1], row_no)
                    output_audio_file_path = os.path.join(args.output, split_audio_file_name)

                    # Record this for output to CSV later.
                    output_rows.append((split_audio_file_name, label,))

                    # Do not re-do.
                    if os.path.exists(output_audio_file_path):
                        continue

                    # Perform the audio split.
                    ffmpeg_cli_args = ['ffmpeg',
                                       '-y',
                                       '-loglevel', '8',
                                       '-i', os.path.join(args.samples, audio_file_name),
                                       '-ac', '1',
                                       '-ar', str(args.sample_rate),
                                       '-ss', '00:00:{:.3f}'.format(onset).zfill(6),
                                       '-t', '00:00:{:.3f}'.format(args.sample_length).zfill(6),
                                       output_audio_file_path]
                    r = subprocess.run(ffmpeg_cli_args, capture_output=True)
                    if r.returncode != 0:
                        print('...transcode failed.')
                        # print('STDOUT:')
                        # for l in r.stdout:
                        #     print(l)

                        # print('STDERR:')
                        # for l in r.stderr:
                        #     print(l)

                        # import sys
                        # sys.exit(1)

        except FileNotFoundError:
            print('No corresponding file for {}'.format(csv_file_name))

    metadata_path = os.path.join(args.output, 'labels.csv')
    with open(metadata_path, 'w', newline='') as fh:
        csvw = csv.writer(fh)
        header = ['file_name'] + ['blank{}'.format(x) for x in range(0, 6)] + ['class']
        empty_cols = ['' for x in range(0, 6)]
        for (file_name, label) in output_rows:
            csvw.writerow([file_name] + empty_cols + [label])

def _list_flac_files(dir_path):
    for file_name in os.listdir(dir_path):
        if file_name.endswith('.flac'):
            yield file_name

def _map_label(raw_label):
    '''Map the raw label to a text name.
    '''

    [category, specific] = raw_label.split('-')
    category_no = int(category)
    specific_no = int(specific)
    if specific_no == 0:
        return LabelMapping[category_no][0]
    else:
        try:
            label = LabelMapping[category_no][1][specific_no]
            return label
        except KeyError:
            return LabelMapping[category_no]

if __name__ == '__main__':

    ap = argparse.ArgumentParser(description='Preprocess data from the SINGAPURA dataset.')
    ap.add_argument('-l', '--sample-length', help='Length of audio sample to use in seconds.',
                    dest='sample_length', default=1.0, type=float)
    ap.add_argument('-r', '--sample-rate', help='Sample rate of the output samples in Hz.',
                    dest='sample_rate', default=11025, type=int)
    ap.add_argument('samples', help='Path to directory containing audio files.',
                    type=str)
    ap.add_argument('labels', help='Path to directory containing label CSVs.',
                    type=str)
    ap.add_argument('output', help='Output directory for samples and metadata.',
                    type=str)

    args = ap.parse_args()

    main(args)
