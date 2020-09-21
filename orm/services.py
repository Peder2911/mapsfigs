
import re
import pandas as pd
from . import Variable

sqlcol = lambda x: re.sub("[^a-zA-Z_0-9]+","",x)

def getvar(vname,connection):
    return pd.read_sql(f"SELECT {sqlcol(vname)} FROM data",connection)

def withmeta(series,session):
    mappings = getdict(series.name,session)
    series = (series
            .apply(lambda x: mappings.get(x))
            .astype("category")
        )
    
    revmap = {v:k for k,v in mappings.items()}

    levels = list(mappings.values())
    levels.sort(key = lambda lvl: revmap[lvl]) 
    series.levels = levels 

    return series 

def getdict(variable,session):
    var = session.query(Variable).filter(Variable.name == variable).first()
    return {mp.key:mp.value for mp in var.mappings}

def getdescr(vname,session):
    return session.query(Variable).filter(Variable.name == vname).first().description
