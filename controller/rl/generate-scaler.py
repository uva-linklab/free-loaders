# Generates a standard scaler for the input state of few runs of the task scheduler
from sklearn.preprocessing import StandardScaler
import pandas as pd

# fetch data from a file
data = pd.read_csv('pobs.csv', header=None).values
scaler = StandardScaler()
scaler.fit(data)
scalerd_data = scaler.transform(data)