import logging

import contextlib
from contextlib import closing
import os
import io
import textwrap

import azure.functions as func 

from matplotlib import pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

from sqlalchemy.exc import ProgrammingError

from __app__.plotting import plotbytes,calcwidth,wrapped,wrap # pylint: disable=import-error
from __app__.orm import get_session,connect # pylint: disable=import-error
from __app__.orm.services import withmeta,getvar,getdescr,getdict # pylint: disable=import-error


def main(req: func.HttpRequest):
    try:
        format = req.params["fmt"]
    except KeyError:
        format = "png"

    vname = req.route_params["vname"]

    with contextlib.closing(connect()) as con:
        try:
            df = getvar(vname,con)
        except ProgrammingError: 
            return func.HttpResponse(status_code=404)

    with contextlib.closing(get_session()) as sess:
        df[vname] = withmeta(df[vname],sess)

    @plotbytes(format=format)
    def plot_hist(data,variable=None,keepna=False):
        """
        Plotting function.
        """
        if not variable:
            variable = data.columns[0]

        with closing(get_session()) as sess:
            vdict = getdict(variable,sess)
            description = getdescr(variable,sess)

        data = data[variable].value_counts().reset_index()
        data[variable] = (data[variable] / data[variable].sum())

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

        plt.title("\n".join(textwrap.wrap(description,60)))
        plt.xlabel("")
        plt.ylabel("")
        plt.subplots_adjust(top=0.85,bottom=0.15)
        fig.set_size_inches(calcwidth(data[variable]),6)

    try:
        picbytes,mimetype = plot_hist(df)
    except NotImplementedError:
        return func.HttpResponse(status_code=400)

    return func.HttpResponse(picbytes,mimetype=mimetype)
