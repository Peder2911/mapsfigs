
import json
import logging
import contextlib
import textwrap

import base64

import pandas as pd
import fire
from flask import Flask,render_template,request,redirect
import jinja2

from orm import get_session,Base,Variable,Mapping,connect
from parsing import getCodebookFromExcel,getDescriptionsFromExcel,ascii_to_int,fixedVname,KEEP,sqlcol
from datafixing import simplify
from plotting import plot_hist

logger = logging.getLogger(__name__)

app = Flask(__name__)

def load(datapath,codebookpath):
    Base.metadata.create_all()
    dat = pd.read_csv(datapath,encoding="latin1",low_memory=False)
    dat = simplify(dat)

    with contextlib.closing(get_session()) as sess:
        _import_metadata(codebookpath,sess) # pylint: disable=no-value-for-parameter

    with contextlib.closing(get_session()) as sess:
        vnames = set([e for e,*_ in sess.query(Variable.name).all()])

    dat = dat[list(vnames.union(KEEP))]

    with contextlib.closing(connect()) as con:
        dat.to_sql("data",con,if_exists="replace")

@app.route("/var")
def listvar():
    with contextlib.closing(get_session()) as sess:
        variables = sess.query(Variable).all()
    return render_template("lsvariable.html",variables=variables)

@app.route("/var/<vname>")
def showvar(vname):
    return render_template("variable.html",vname = vname)

@app.route("/gen/hist/<vname>.png")
def genhist(vname):
    with contextlib.closing(connect()) as con:
        df = _getvar(vname,con)
    with contextlib.closing(get_session()) as sess:
        df[vname] = _withmeta(df[vname],sess)
        descr = _getdescr(vname,sess)
        descr = "\n".join(textwrap.wrap(descr,50))

    picbytes = plot_hist(df,descr)
    #b64 = base64.b64encode(picbytes).decode()
    return picbytes, 200, {"Content-Type": "image/png"}

@app.route("/meta/<vname>",methods=["GET","POST"])
def editmeta(vname):
    if request.method == "GET":
        with contextlib.closing(get_session()) as sess:
            var = (sess
                    .query(Variable)
                    .filter(Variable.name == vname)
                    .first()
                )
            mappings = var.mappings
        return render_template("meta.html",variable=var,mappings=mappings)
    elif request.method == "POST":
        """
        VALIDATION
        """

        with contextlib.closing(get_session()) as sess:
            var = (sess
                    .query(Variable)
                    .filter(Variable.name == vname)
                    .first()
                )

            var.description = request.form["description"]

            mappings = {mpid for mpid,_ in [k.split("_") for k in request.form.keys() if "_" in k]}
            for mpid in mappings:
                mp = (sess
                    .query(Mapping)
                    .get({"id": mpid})
                    )
                mp.key = request.form[f"{mpid}_key"]
                mp.value = request.form[f"{mpid}_value"]

            sess.commit()

        return redirect(request.url) 

def _getvar(vname,connection):
    return pd.read_sql(f"SELECT {sqlcol(vname)} FROM data",connection)

def _getdescr(vname,session):
    return session.query(Variable).filter(Variable.name == vname).first().description

def _withmeta(series,session):
    vname = series.name
    var = session.query(Variable).filter(Variable.name == vname).first()
    mappings = {mp.key:mp.value for mp in var.mappings}
    return series.apply(lambda x: mappings.get(x))

def _import_metadata(path,session):
    cb = getCodebookFromExcel(path)
    descr = getDescriptionsFromExcel(path)
    for vname,mp in cb.items():
        if session.query(Variable).filter(Variable.name == vname).first():
            continue

        mappings = []
        for k,v in mp.items():
            try:
                k = ascii_to_int(k)
            except ValueError:
                pass

            mappings.append(Mapping(key = k,value = v))
        
        try:
            description = descr[vname.upper()]
        except KeyError:
            description = ""

        var = Variable(
            name = vname,
            description = description,
            mappings = mappings
            )
        session.add(var)

    session.commit()

if __name__ == "__main__":
    flask.Flask(app)

