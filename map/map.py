
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

from __app__.plotting import plotbytes # pylint: disable=import-error
from __app__.orm import get_session,connect # pylint: disable=import-error
from __app__.orm.services import withmeta,getvar,getdescr,getdict # pylint: disable=import-error
from __app__.util import sanitizeVarname


@plotbytes
def plot_map(geodata):
    fig,ax = plt.subplots()
    geodata.plot(column = "var",ax=ax)

def main(req: func.HttpRequest):
    vname = req.route_params["vname"]
    with contextlib.closing(connect()) as con:
        data = pd.read_sql(
                f"SELECT \"{sanitizeVarname(vname)}\""
                "AS var, \"PDET\" FROM data",
                con)
        geodata = pd.read_sql("SELECT * FROM geodata",con)
        geodata["geometry"] = geodata["geostring"].apply(wkt.loads)
        geodata = gpd.GeoDataFrame(geodata,geometry="geometry")

    data = data.groupby("PDET").mean()
    logging.info(data)
    geodata = geodata.merge(data,on="PDET")

    picbytes = plot_map(geodata)
    return func.HttpResponse(picbytes,mimetype="image/png")
