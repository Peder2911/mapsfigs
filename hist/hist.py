
import contextlib
import os
import io
import textwrap

from matplotlib import pyplot as plt
import azure.functions as func 
import matplotlib.ticker as mtick
import seaborn as sns

from __app__.plotting import plotbytes # pylint: disable=import-error
from __app__.orm import get_session,connect # pylint: disable=import-error
from __app__.orm.services import withmeta,getvar,getdescr # pylint: disable=import-error

removeMissing = lambda x: x[x[x.columns[0]]!="No answer"]

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

def main(req: func.HttpRequest):
    vname = req.route_params["vname"]
    with contextlib.closing(connect()) as con:
        df = getvar(vname,con)
    with contextlib.closing(get_session()) as sess:
        df[vname] = withmeta(df[vname],sess)
        descr = getdescr(vname,sess)
        descr = "\n".join(textwrap.wrap(descr,50))

    picbytes = plot_hist(df,descr)
    return func.HttpResponse(picbytes,mimetype="image/png")
