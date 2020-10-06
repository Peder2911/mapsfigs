import logging

import contextlib
from contextlib import closing
import os
import io
import textwrap

import azure.functions as func 

import pandas as pd
from scipy.stats import chisquare
import jinja2

from __app__.plotting import plotbytes,calcwidth,wrapped,wrap # pylint: disable=import-error
from __app__.orm import get_session,connect # pylint: disable=import-error
from __app__.orm.services import withmeta,getvar,getdescr,getdict # pylint: disable=import-error

STYLE = """
<style>
table {
  table-layout: fixed ;
}
th,td {
    width: 100px;
    height: 50px;
    text-align: center;
    background: #f0f0f0;
}
th {
    background: #a0a0a0;
}
td.summary {
    text-align: right;
    padding-right: 10px;
}
</style>
"""

def htmlCrossTable(ctab,aggfn):
    template = jinja2.Template("""
    <table>
        <tr>
            <th scope=col></th>
            {% for v in columns %}
                <th scope=col>{{ v }}</th>
            {% endfor %}
        </tr>
        {% for r in rows %}
            <tr>
                <th scope=row>{{ r[0] }}</th>
                    {% for v in r[1] %}
                        <td>{{ v }}</td>
                    {% endfor %}
            </tr>
        {% endfor %}
        <tr>
            <td class="summary" colspan = 100>
                N: {{ n }}
                Chi: {{ cstat }}
                ({{ cp }})
            </td>
        </tr>
    </table>
    """)
    n = ctab.values.sum().sum()
    chi = chisquare(ctab.values,axis=None)
    cstat,cp = chi.statistic,chi.pvalue
    cstat = round(cstat,4)

    ctab = aggfn(ctab)
    logging.info(ctab)

    return template.render(
            columns = ctab.columns,
            rows = [[i,v] for i,v in zip(ctab.index,ctab.values)],
            n = n, 
            cstat = cstat, 
            cp = cp
        )

def getAggFn(kind):
    def pst(array):
        overall = array.sum().sum()
        return (array/overall)*100

    functions = {
            "count": lambda df: df.astype(int),
            "pst": lambda df: (pst(df)).apply(lambda v: round(v,2))
    }

    try:
        fn = functions[kind]
    except KeyError:
        fn = functions["count"]
    return fn

def fixIndices(df):
    df.columns = df.columns.astype(int)
    df.index = df.index.astype(int)
    return df

def main(req: func.HttpRequest):
    with closing(connect()) as con:
        v1,v2 = req.route_params["variables"].split("-")
        df = pd.read_sql(f"SELECT {v1},{v2} FROM data",con)

    try:
        kind = req.params["type"]
    except KeyError:
        kind = "count"
    aggfn = getAggFn(kind) 
    ctab = fixIndices(pd.crosstab(df[v1],df[v2]))
    ctab = htmlCrossTable(ctab,aggfn)
    return func.HttpResponse(STYLE+ctab,mimetype="text/html")
