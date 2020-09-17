
import string
import os
import json
import pandas as pd

from typing import List,Dict,Union

from collections import defaultdict 

import yaml

import numpy as np

import re


fixedVname = lambda x: re.sub("(_AT|_FW)$","",x)
stripPrefix = lambda x: re.sub("(_FW|_AT)$","",x)

def daneCode(v):
    try:
        return "{0:05d}".format(int(v))
    except ValueError:
        return pd.NA

def genDeptName(name):
    return re.sub("[^A-Za-z]","",name)[:3].lower()

def getOldCodebook(dat: pd.DataFrame):
    """
    Makes a dictionary of dictionaries mapping values to strings, used to annotate plots.
    """
    d = dict()
    for v in set(dat["Variable"]):
        vd = dict()
        for idx,r in dat[dat["Variable"] == v].iterrows():
            vd.update({str(r["Valor"]):str(r["Valor_Etiqueta"])})
        d.update({v:vd})
    return d

def getMergedCodebook(raw: pd.DataFrame)-> Dict[str,Dict[str,str]]:
    dat: Dict[str,Union[Dict,None]] = dict()
    nones = defaultdict(list) 

    replacements = {
        "Apply": "Yes",
        "Does not apply": "No"
    }
    def fixValue(value):
        try:
            return replacements[value]
        except KeyError:
            return value

    for idx,r in raw.iterrows():
        vname = r["Variablename"]
        vname = fixedVname(vname)

        try:
            v = yaml.safe_load(r["Alternatives"])
            #print(v)
            v = {k:fixValue(v) for k,v in v.items()}
        except: 
            dat[vname] = None
            continue

        try:
            if any([x is None for x in v.values()]):
                nones[json.dumps(v,indent=4)].append(vname)
                dat[vname] = None
                continue

        except AttributeError:
            dat[vname] = None
            continue
            
        dat[vname] = v

    def fixValue(value):
        if value is True:
            return "Yes"
        elif value is False:
            return "No"
        else:
            return str(value)

    try:
        comp = {k:v for k,v in dat.items() if v is not None}
        comp = {ko:{str(k):fixValue(v) for k,v in vo.items()} for ko,vo, in comp.items()}
    except:
        pass
    return comp

def getDescriptions(dat: pd.DataFrame):
    """
    Makes a dictionary of variable descriptions used to annotate plots
    """
    d = dict()
    for idx,r in dat.iterrows():
        label = r["Etiqueta"].split(".")[-1]
        d.update({fixedVname(r["Variable"]):label})
    return d

def getMergedDescriptions(dat: pd.DataFrame):
    """
    Makes a dictionary of variable descriptions used to annotate plots
    """
    dat.columns = [c.strip() for c in dat.columns]

    d = dict()
    for idx,r in dat.iterrows():
        d.update({fixedVname(r["Variablename"]).upper():r["Question"]})
    return d

def getDescriptionsFromExcel(*args,**kwargs):
    return getMergedDescriptions(pd.read_excel(*args,**kwargs))

def getCodebookFromExcel(*args,**kwargs):
    return getMergedCodebook(pd.read_excel(*args,**kwargs))

def fixMissing(v):
    if v > -1:
        return v
    else:
        return pd.NA

def orderedCats(cbdict):
    items = [(k,v) for k,v in cbdict.items()]
    items.sort(key = lambda x: int(x[0]))
    return [v for k,v in items]

def fixCatVar(v,vname,cb):
    return pd.Categorical(
        v.apply(lambda x: cb[vname.upper()][str(int(x))]),
        categories=orderedCats(cb[vname.upper()])[2:],
        ordered=True)

def ascii_to_int(char):
    return string.ascii_letters.index(char)
