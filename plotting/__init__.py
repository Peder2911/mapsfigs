
import logging
import textwrap
import io
from matplotlib import pyplot as plt
from pandas import Series

MIMETYPES = {
        "png": "image/png",
        "jpg": "image/jpg",
        "pdf": "application/pdf",
        "ps": "application/postscript",
        "svg": "image/svg+xml"
    }

def plotbytes(format="png"):
    def wrapper(fn):
        def inner(*args,**kwargs):
            try:
                mimetype = MIMETYPES[format]
            except KeyError:
                raise NotImplementedError

            bio = io.BytesIO()
            plt.clf()
            fn(*args,**kwargs)
            plt.savefig(bio,format = format)
            return bio.getvalue(),mimetype
        return inner
    return wrapper

calcwidth = lambda series: max(6,2.2 * len(series.unique()))
wrap = lambda label: "\n".join(textwrap.wrap(label,16))
wrapped = lambda labels: [wrap(lbl) for lbl in labels]
