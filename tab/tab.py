import logging

import contextlib
from contextlib import closing
import os
import io
import textwrap

import azure.functions as func 

import pandas as pd
from scipy.stats import chi2_contingency 
import jinja2

from __app__.plotting import plotbytes,calcwidth,wrapped,wrap # pylint: disable=import-error
from __app__.orm import get_session,connect,Variable # pylint: disable=import-error
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
            <td class="summary">
                N: {{ n }}
            </td>
            <td class="summary">
                Chi: {{ cstat }}
            </td>
            <td class="summary">
                P: {{ cp }}
            </td>
        </tr>
    </table>
    """)
    n = ctab.values.sum().sum()
    chi = chi2_contingency(ctab.values)
    cstat,cp,*_ = chi 
    cstat = round(cstat,4)
    cp = round(cp,5)

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

def fixIndices(df,v1,v2):
    with contextlib.closing(get_session()) as sess:
        lookups = []
        for v in v1,v2:
            mappings = sess.query(Variable).filter(Variable.name == v).first().mappings
            keyval = {mp.key:mp.value for mp in mappings}
            lookups.append(keyval)
        v1,v2 = lookups 
    df.columns = [v2[v] for v in df.columns.astype(int)]
    df.index = [v1[v] for v in df.index.astype(int)]
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
    ctab = fixIndices(pd.crosstab(df[v1],df[v2]),v1,v2)
    ctab = htmlCrossTable(ctab,aggfn)
    return func.HttpResponse(STYLE+ctab,mimetype="text/html")
