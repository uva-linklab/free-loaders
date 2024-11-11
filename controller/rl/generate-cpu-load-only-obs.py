import random

# 32 1/0 inputs for task ID, CPU loads

for _i in range(10000):
    ivs = [
            random.choice([x for x in range(60)]),
            random.uniform(0, 10000),

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
