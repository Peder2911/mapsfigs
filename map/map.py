
import re
import logging
import contextlib
from contextlib import closing
import os
import io
import textwrap

import pandas as pd
import geopandas as gpd
from shapely import wkt

from matplotlib import pyplot as plt
import azure.functions as func 
import matplotlib.ticker as mtick

import seaborn as sns
import contextily

from __app__.plotting import plotbytes # pylint: disable=import-error
from __app__.orm import get_session,connect # pylint: disable=import-error
from __app__.orm.services import withmeta,getvar,getdescr,getdict # pylint: disable=import-error
from __app__.util import sanitizeVarname # pylint: disable=import-error


@plotbytes
def plot_map(geodata,scalemin,scalemax):
    geodata = geodata.to_crs(epsg=3857)
    fig,ax = plt.subplots()
    geodata.plot(column = "var",ax=ax,alpha=0.8,
            legend=True,vmin=scalemin,vmax=scalemax)
    contextily.add_basemap(ax,
            source=contextily.providers.Stamen.TonerLite)
    fig.set_size_inches((6.5,8))

def main(req: func.HttpRequest):
    vname = req.route_params["vname"]
    with contextlib.closing(connect()) as con:
        san = sanitizeVarname(vname)
        data = pd.read_sql(
                f"SELECT {san} "
                f"AS var, pdet FROM data WHERE {san} > -1",
                con)
        scalemin,scalemax = data["var"].min(),data["var"].max()

        geodata = pd.read_sql("SELECT * FROM geodata",con)
        geodata["geometry"] = geodata["geostring"].apply(wkt.loads)
        geodata = gpd.GeoDataFrame(geodata,geometry="geometry")
        geodata = geodata.set_crs("epsg:4326")
    base = data.copy()
    try:
        try:
            data["isval"] = data["var"] == int(req.params["valeq"])
        except KeyError:
            data["isval"] = data["var"] > int(req.params["valgt"])

        data = (data[["pdet","isval"]]
                .groupby("pdet")
                .agg(["sum","count"])
            )
        data.columns = data.columns.droplevel(0)
        data = data.reset_index()
        data["var"] = (data["sum"] / data["count"])*100
        scalemin,scalemax = 0,100
    except KeyError:
        data = base.groupby("pdet").mean() 

    geodata = geodata.merge(data,on="pdet")

    picbytes = plot_map(geodata,scalemin,scalemax)

    return func.HttpResponse(picbytes,mimetype="image/png")
