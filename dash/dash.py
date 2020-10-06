
import json
from contextlib import closing
import jinja2
import azure.functions as func 
from __app__.orm import Variable, get_session # pylint: disable=import-error


env = jinja2.Environment(
    loader = jinja2.PackageLoader("__app__.dash","."),
    autoescape = jinja2.select_autoescape(["html"])
)

def main(req:func.HttpRequest)->func.HttpResponse:
    with closing(get_session()) as sess:
        variables = sess.query(Variable).all()

    plottypes = [
            {"name":"Histogram",
                "description":"A simple histogram of unique values of variable 1.",
                "path":"hist/%s","needs":["v1"]},

            {"name":"Comparison means",
                "description": "Show means of variable 2 for unique values of variable 1.",
                "path":"comp/%s-%s?agg=mean","needs":["v1","v2"]},

            {"name":"Comparison percentages",
                "description": "Show percentage distribution for values of "
                               "variable 2 distributed over values of variable 1.",
                "path":"comp/%s-%s?agg=pst","needs":["v1","v2"]},

            {"name":"Group comp. percentages",
                "description": "Show percentage distribution of unique values of "
                               "variable 2 for each unique value of variable 1.",
                "path":"comp/%s-%s?agg=grppst","needs":["v1","v2"]},

            {"name":"Comparison counts",
                "description": "Show count distribution of unique values of "
                               "variable 2 for each unique value of variable 1.",
                "path":"comp/%s-%s?agg=count","needs":["v1","v2"]},

            {"name":"Map mean",
                "description": "Show map of means of variable 1",
                "path":"map/%s","needs":["v1"]},

            {"name":"Map percent equals",
                "description": "Show map of percentages of the number of"
                               "responses to variable 1 that equal a given value",
                "path":"map/%s?valeq=%s","needs":["v1","param"]}
        ]

    formats = [
            {"name":"png","ext":"png"},
            {"name":"postscript","ext":"ps"},
            {"name":"pdf","ext":"pdf"},
            {"name":"svg","ext":"svg"},
        ]

    html = env.get_template("dash.html").render(
                variables = variables,
                plottypes = plottypes,
                formats = formats,
                json = json
            )

    return func.HttpResponse(html, mimetype="text/html")

    
