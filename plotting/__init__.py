
import io
from matplotlib import pyplot as plt

def plotbytes(fn):
    def inner(*args,**kwargs):
        bio = io.BytesIO()
        plt.clf()
        fn(*args,**kwargs)
        plt.savefig(bio)
        return bio.getvalue()
    return inner
