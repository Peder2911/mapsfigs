import logging

import contextlib
from contextlib import closing
import os
import io
import textwrap

from matplotlib import pyplot as plt
import azure.functions as func 
import matplotlib.ticker as mtick
import seaborn as sns

from __app__.plotting import plotbytes,calcwidth,wrapped,wrap # pylint: disable=import-error
from __app__.orm import get_session,connect # pylint: disable=import-error
from __app__.orm.services import withmeta,getvar,getdescr,getdict # pylint: disable=import-error


@plotbytes
def plot_hist(data,variable=None,keepna=False):
    if not variable:
        variable = data.columns[0]

    with closing(get_session()) as sess:
        vdict = getdict(variable,sess)
    data = data[variable].value_counts().reset_index()
    data[variable] = (data[variable] / data[variable].sum())

    #wrap = lambda v: "\n".join(textwrap.wrap(v,18))
    data["index"] = data["index"].apply(wrap)
    vdict = {k:wrap(v) for k,v in vdict.items()}
    if not keepna:
        vdict = {k:v for k,v in vdict.items() if k>=0}

    fig,ax = plt.subplots()
    sns.barplot(
            x = data["index"],
            y = data[variable],
            ax = ax,
            order = vdict.values()
        )
    
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    #plt.title("\n".join(textwrap.wrap(description,60)))
    plt.xlabel("")
    plt.ylabel("")
    plt.subplots_adjust(top=0.85,bottom=0.15)
    fig.set_size_inches(calcwidth(data[variable]),6)

def main(req: func.HttpRequest):
    vname = req.route_params["vname"]
    with contextlib.closing(connect()) as con:
        df = getvar(vname,con)
    with contextlib.closing(get_session()) as sess:
        df[vname] = withmeta(df[vname],sess)
        #descr = getdescr(vname,sess)
        #descr = "\n".join(textwrap.wrap(descr,50))

    picbytes = plot_hist(df)
    return func.HttpResponse(picbytes,mimetype="image/png")
