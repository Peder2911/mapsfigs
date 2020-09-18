
import os
import io

import textwrap
from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

removeMissing = lambda x: x[x[x.columns[0]]!="No answer"]

def plotbytes(fn):
    def inner(*args,**kwargs):
        bio = io.BytesIO()
        plt.clf()
        fn(*args,**kwargs)
        plt.savefig(bio)
        return bio.getvalue()
    return inner

@plotbytes
def plot_hist(data,description,variable=None):
    data = removeMissing(data)
    if not variable:
        variable = data.columns[0]
    data = data[variable].value_counts().reset_index()
    data[variable] = (data[variable] / data[variable].sum())

    data["index"] = data["index"].apply(lambda v: "\n".join(textwrap.wrap(v,20)))
    calcwidth = 2 * data.shape[0]

    fig,ax = plt.subplots()
    sns.barplot(
            x = data["index"],
            y = data[variable],
            ax = ax
        )
    
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))


    plt.title("\n".join(textwrap.wrap(description,60)))
    plt.xlabel("")
    plt.ylabel("")
    plt.subplots_adjust(top=0.85,bottom=0.15)

    fig.set_size_inches(max(7,calcwidth),6)
