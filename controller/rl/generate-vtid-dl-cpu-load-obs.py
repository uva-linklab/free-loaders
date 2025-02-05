import random

# 32 1/0 inputs for task ID, deadline, CPU loads

for _i in range(10000):
    ivs = [
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),
            random.choice([0, 1]),

            random.uniform(0, 20000),

            random.uniform(0, 4),
            random.uniform(0, 4),
            random.uniform(0, 4),
            random.uniform(0, 4),
            random.uniform(0, 4),
            random.uniform(0, 4),
            random.uniform(0, 4),
            random.uniform(0, 4),
            random.uniform(0, 6),
            random.uniform(0, 8)]

    print(','.join([str(x) for x in ivs]))
