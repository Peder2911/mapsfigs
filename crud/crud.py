
import json
import logging
import contextlib
import textwrap

import base64

import pandas as pd
import fire
import jinja2
import azure.functions as func 

from __app__.orm import get_session,Base,Variable,Mapping,connect # pylint: disable=import-error

logger = logging.getLogger(__name__)

## Re-add templating

@app.route("/var")
def listvar(req):
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

ACTIONS = {
        "list": listvar,
        "edit": editmeta,
        "show": showvar
}

def main(req: func.HttpRequest):
    action = req.route_params["action"]
    return ACTIONS[action](req)

