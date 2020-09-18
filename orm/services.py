
import re
import pandas as pd
from . import Variable

sqlcol = lambda x: re.sub("[^a-zA-Z_0-9]+","",x)

def getvar(vname,connection):
    return pd.read_sql(f"SELECT {sqlcol(vname)} FROM data",connection)

def withmeta(series,session):
    vname = series.name
    var = session.query(Variable).filter(Variable.name == vname).first()
    mappings = {mp.key:mp.value for mp in var.mappings}
    return series.apply(lambda x: mappings.get(x))

def getdescr(vname,session):
    return session.query(Variable).filter(Variable.name == vname).first().description
