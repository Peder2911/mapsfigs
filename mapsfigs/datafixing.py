
import pandas as pd

def simplify(df):
    def fn(series):
        try:
            series = series.astype(pd.Int64Dtype())
        except:
            pass
        return series
    return df.apply(fn,0)
