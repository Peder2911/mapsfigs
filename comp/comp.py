"""
Double bar plot, showing distribution over two variables
"""
import textwrap
import contextlib
from contextlib import closing
import string
import logging

import azure.functions as func 

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.ticker import PercentFormatter 

from __app__.plotting import plotbytes,calcwidth,wrapped # pylint: disable=import-error
from __app__.orm import get_session,connect # pylint: disable=import-error
from __app__.orm.services import withmeta,getvar,getdescr,getdict # pylint: disable=import-error

def plotfn(name):
    FUNCTIONS ={
            "count": countplot,
            "mean": meanplot,
            "pst": pstplot 
        }

    return FUNCTIONS[name]

def pstplot(*args,**kwargs):
    countplot(*args,**kwargs,pst=True)

def countplot(data,v1,v2,keepna,pst=False):
    data = data.groupby(v1)[v2].value_counts()
    if pst:
        data = data.groupby(level=0).apply(lambda x: (x / x.sum()))

    data.name = "count" 
    data = data.reset_index()

    with closing(get_session()) as sess:
        dicts = {}
        for v in v1,v2:
            data[v] = withmeta(data[v],sess)
            dicts[v] = getdict(v,sess)

    if not keepna:
        rmna = lambda d: {k:v for k,v in d.items() if k >= 0}
        dicts = {k:rmna(v) for k,v in dicts.items()}

    fig,ax = plt.subplots()
    sns.barplot(
            data = data, 
            x = v1, y = "count", hue = v2, ci = "sd",
            order = dicts[v1].values(),
            hue_order = dicts[v2].values(),
            ax = ax
        )
    ax.set_xticklabels(wrapped(dicts[v1].values()))

    if pst:
        ax.yaxis.set_major_formatter(PercentFormatter(1.0))

    plt.legend(title="",frameon = False,loc=2,bbox_to_anchor=(1.,1))

    width = calcwidth(data[v1])
    fig.set_size_inches(width,6)
    plt.subplots_adjust(right=1-(2/width),bottom=0.15)

def meanplot(data,v1,v2,keepna):
    if not keepna:
        for v in v1,v2:
            data = data[data[v] > 0]

    with closing(get_session()) as sess:
        data[v1] = withmeta(data[v1],sess)
        vdict = getdict(v1,sess)

    if not keepna:
        vdict = {k:v for k,v in vdict.items() if k > 0}

    fig,ax = plt.subplots(figsize=(3,3))

    sns.barplot(
            data = data,
            x=v1,y=v2,
            ax = ax,
            order = vdict.values(),
        )

    ax.set_xticklabels(wrapped(vdict.values()))
    fig.set_size_inches(calcwidth(data[v1]),6)

@plotbytes
def comp(data,v1,v2,agg = "count",keepna=False):
    try:
        fn = plotfn(agg)
    except KeyError:
        return func.HttpResponse(status_code=400)
    else:
        fn(data,v1,v2,keepna)
    plt.xlabel("")
    plt.ylabel("")

def main(req: func.HttpRequest):
    try:
        v1,v2 = req.route_params["variables"].split("-")
    except ValueError:
        return func.HttpResponse(status_code=404)

    with contextlib.closing(connect()) as con:
        df = getvar(v1,con).join(getvar(v2,con))

    try:
        keepna = req.params["na"] == "True"
    except KeyError:
        keepna = False

    try:
        agg = req.params["agg"]
    except KeyError:
        agg = "count"

    return func.HttpResponse(comp(df,v1,v2,agg=agg,keepna=keepna),mimetype="image/png")
