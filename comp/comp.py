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
from __app__.plotting.text import nlwrap # pylint: disable=import-error
from __app__.orm import get_session,connect # pylint: disable=import-error
from __app__.orm.services import withmeta,getvar,getdescr,getdict # pylint: disable=import-error

def plotfn(name):
    FUNCTIONS ={
            "count": countplot,
            "mean": meanplot,
            "pst": lambda *args,**kwargs: countplot(*args,**kwargs,pst=True),
            "grppst": lambda *args,**kwargs: countplot(*args,**kwargs,pst=True,incat=True)
        }
    return FUNCTIONS[name]

def countplot(data,v1,v2,keepna,pst=False,incat=False):
    data = data.groupby(v1)[v2].value_counts()

    if pst:
        if incat:
            data = data.groupby(level=0).apply(lambda x: (x / x.sum()))
        else:
            tot_n = data.sum()
            data = data.groupby(level=0).apply(lambda x: (x / tot_n))

    data.name = "count" 
    data = data.reset_index()

    with closing(get_session()) as sess:
        dicts = {}
        for v in v1,v2:
            data[v] = withmeta(data[v],sess)
            dicts[v] = getdict(v,sess)

        v1d,v2d = (getdescr(v,sess) for v in (v1,v2))

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

    plt.title(nlwrap(v1d,50))

    legend = plt.legend(title=nlwrap(v2d,20),frameon = False,loc=2,bbox_to_anchor=(1.,1))
    ttl = legend.get_title()
    ttl.set_multialignment("center")

    for txt in legend.get_texts():
        txt.set_text(nlwrap(txt.get_text(),15))

    width = calcwidth(data[v1])
    fig.set_size_inches(width,6)
    plt.subplots_adjust(right=0.7,bottom=0.15)

def meanplot(data,v1,v2,keepna):
    if not keepna:
        for v in v1,v2:
            data = data[data[v] > 0]

    with closing(get_session()) as sess:
        data[v1] = withmeta(data[v1],sess)
        vdict = getdict(v1,sess)
        v1d,v2d = (getdescr(v,sess) for v in (v1,v2))

    minval,maxval = data[v2].min(),data[v2].max()

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
    fig.subplots_adjust(left=0.20)
    fig.text(0.06,0.5,nlwrap(v2d+" (mean)",25),rotation="vertical",va="center",ha="center")
    plt.title(v1d)
    plt.ylim(minval,maxval)

def main(req: func.HttpRequest):
    try:
        format = req.params["fmt"]
    except KeyError:
        format = "png"

    @plotbytes(format=format)
    def comp(data,v1,v2,agg = "count",keepna=False):
        try:
            fn = plotfn(agg)
        except KeyError:
            return func.HttpResponse(status_code=400)
        else:
            fn(data,v1,v2,keepna)
        plt.xlabel("")
        plt.ylabel("")
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
    
    bytes,mimetype = comp(df,v1,v2,agg=agg,keepna=keepna)

    return func.HttpResponse(bytes,mimetype=mimetype)
