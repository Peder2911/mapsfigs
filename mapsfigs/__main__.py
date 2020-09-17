
import logging
import contextlib
import sqlite3

import pandas as pd
import fire

from orm import get_session,Base,Variable,Mapping
from parsing import getCodebookFromExcel,getDescriptionsFromExcel,ascii_to_int,fixedVname

logger = logging.getLogger(__name__)

def _withsess(fn):
    def inner(self,*args,**kwargs):
        with contextlib.closing(get_session()) as sess:
            fn(self,_session=sess,*args,**kwargs)
    return inner

class mf():
    def __init__(self):
        Base.metadata.create_all()

    def load(self,datapath,codebookpath):
        with contextlib.closing(sqlite3.connect("data/maps.sqlite")) as con:
            pd.read_csv(datapath,encoding="latin1").to_sql("data",con,if_exists="replace")
        self._import_metadata(codebookpath)

    @_withsess
    def _import_metadata(self,path,_session):
        cb = getCodebookFromExcel(path)
        descr = getDescriptionsFromExcel(path)
        for vname,mp in cb.items():
            if _session.query(Variable).filter(Variable.name == vname).first():
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
            _session.add(var)

        _session.commit()

    @_withsess
    def sessfn(self,_session):
        print(_session)

if __name__ == "__main__":
    fire.Fire(mf)

