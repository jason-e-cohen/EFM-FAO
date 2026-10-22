import pandas as pd
def rankdata(x): return pd.Series(x).rank().to_numpy()
