import csv
import random

MaxLoads = [4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 6.0, 4.0]

with open('pobs.csv', 'w') as fh:
    for _i in range(0, 1000):
        row = [round(random.uniform(0, 15000), 2), random.randint(0, 59)] \
               + [round(l * random.uniform(0, 1), 2) for l in MaxLoads]
        srow = list(map(str, row))
        line = ','.join(srow)
        print(line, file=fh)
