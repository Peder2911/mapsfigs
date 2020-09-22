
import textwrap
import io
from matplotlib import pyplot as plt
from pandas import Series

def plotbytes(fn):
    def inner(*args,**kwargs):
        bio = io.BytesIO()
        plt.clf()
        fn(*args,**kwargs)
        plt.savefig(bio)
        return bio.getvalue()
    return inner


calcwidth = lambda series: max(6,2.2 * len(series.unique()))
wrap = lambda label: "\n".join(textwrap.wrap(label,16))
wrapped = lambda labels: [wrap(lbl) for lbl in labels]
