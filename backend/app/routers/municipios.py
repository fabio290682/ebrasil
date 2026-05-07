from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import DATABASE_BACKEND
from ..database import get_db
from ..models import Municipio
from ..schemas import MunicipioOut
from ..services.query import list_municipios

router = APIRouter(prefix="/municipios", tags=["municipios"])


@router.get("", response_model=list[MunicipioOut])
def get_municipios(uf: str | None = Query(default=None, min_length=2, max_length=2), db: Session = Depends(get_db)):
    if DATABASE_BACKEND == "mongo":
        from ..services.mongo_query import list_municipios as list_municipios_mongo
        return list_municipios_mongo(uf=uf)
    return list_municipios(db, uf=uf)


@router.get("/{codigo_ibge}", response_model=MunicipioOut)
def get_municipio(codigo_ibge: str, db: Session = Depends(get_db)):
    if DATABASE_BACKEND == "mongo":
        from ..services.mongo_query import get_municipio as get_municipio_mongo
        municipio = get_municipio_mongo(codigo_ibge)
        if not municipio:
            raise HTTPException(status_code=404, detail="Municipio nao encontrado")
        return municipio

    municipio = db.get(Municipio, codigo_ibge)
    if not municipio:
        raise HTTPException(status_code=404, detail="Municipio nao encontrado")
    return municipio
