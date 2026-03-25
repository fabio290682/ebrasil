# -*- coding: utf-8 -*-
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from .mongo import get_mongo_db
from .models import GastoPublico, Municipio


MUNICIPIOS_INICIAIS = [
    {"codigo_ibge": "4205407", "nome_municipio": "Florianópolis", "uf": "SC", "nome_estado": "Santa Catarina", "nome_regiao": "Sul", "populacao_estimada": 537213, "porte_municipio": "Metrópole (>500mil)", "latitude": -27.5949, "longitude": -48.5482},
    {"codigo_ibge": "4209102", "nome_municipio": "Joinville", "uf": "SC", "nome_estado": "Santa Catarina", "nome_regiao": "Sul", "populacao_estimada": 616323, "porte_municipio": "Metrópole (>500mil)", "latitude": -26.3044, "longitude": -48.8487},
    {"codigo_ibge": "4202404", "nome_municipio": "Blumenau", "uf": "SC", "nome_estado": "Santa Catarina", "nome_regiao": "Sul", "populacao_estimada": 380630, "porte_municipio": "Grande (100-500mil)", "latitude": -26.9194, "longitude": -49.0661},
    {"codigo_ibge": "3550308", "nome_municipio": "São Paulo", "uf": "SP", "nome_estado": "São Paulo", "nome_regiao": "Sudeste", "populacao_estimada": 12396372, "porte_municipio": "Metrópole (>500mil)", "latitude": -23.5505, "longitude": -46.6333},
    {"codigo_ibge": "3304557", "nome_municipio": "Rio de Janeiro", "uf": "RJ", "nome_estado": "Rio de Janeiro", "nome_regiao": "Sudeste", "populacao_estimada": 6775561, "porte_municipio": "Metrópole (>500mil)", "latitude": -22.9068, "longitude": -43.1729},
    {"codigo_ibge": "5300108", "nome_municipio": "Brasília", "uf": "DF", "nome_estado": "Distrito Federal", "nome_regiao": "Centro-Oeste", "populacao_estimada": 3094325, "porte_municipio": "Metrópole (>500mil)", "latitude": -15.7801, "longitude": -47.9292},
    {"codigo_ibge": "3106200", "nome_municipio": "Belo Horizonte", "uf": "MG", "nome_estado": "Minas Gerais", "nome_regiao": "Sudeste", "populacao_estimada": 2530701, "porte_municipio": "Metrópole (>500mil)", "latitude": -19.9167, "longitude": -43.9345},
    {"codigo_ibge": "2927408", "nome_municipio": "Salvador", "uf": "BA", "nome_estado": "Bahia", "nome_regiao": "Nordeste", "populacao_estimada": 2900319, "porte_municipio": "Metrópole (>500mil)", "latitude": -12.9714, "longitude": -38.5014},
    {"codigo_ibge": "2304400", "nome_municipio": "Fortaleza", "uf": "CE", "nome_estado": "Ceará", "nome_regiao": "Nordeste", "populacao_estimada": 2703391, "porte_municipio": "Metrópole (>500mil)", "latitude": -3.7319, "longitude": -38.5267},
    {"codigo_ibge": "1302603", "nome_municipio": "Manaus", "uf": "AM", "nome_estado": "Amazonas", "nome_regiao": "Norte", "populacao_estimada": 2255903, "porte_municipio": "Metrópole (>500mil)", "latitude": -3.1190, "longitude": -60.0217},
]

_GASTOS = [
    # SC - Florianópolis
    ("Fornecedor Alfa LTDA", "12.345.678/0001-99", "Educação", "339039", "1500", None, None, None, date(2024, 1, 15), 12500.0, "4205407", "SC", "Betha", "https://transparencia.pmf.sc.gov.br"),
    ("Editora Sapiência SA", "22.333.444/0001-55", "Educação", "339039", "1500", None, None, None, date(2024, 2, 10), 45200.0, "4205407", "SC", "Betha", "https://transparencia.pmf.sc.gov.br"),
    ("Hospital São Lucas LTDA", "33.444.555/0001-66", "Saúde", "339036", "1706", None, None, None, date(2024, 3, 5), 185000.0, "4205407", "SC", "Betha", "https://transparencia.pmf.sc.gov.br"),
    ("Farmácia Popular ME", "44.555.666/0001-77", "Saúde", "339030", "1500", None, None, None, date(2024, 4, 18), 8750.5, "4205407", "SC", "Betha", "https://transparencia.pmf.sc.gov.br"),
    ("Construtora Alpha SA", "55.666.777/0001-88", "Infraestrutura", "449051", "1706", None, None, None, date(2024, 5, 22), 320000.0, "4205407", "SC", "Betha", "https://transparencia.pmf.sc.gov.br"),
    # SC - Joinville
    ("Construtora Delta SA", "99.887.766/0001-10", "Infraestrutura", "449051", "1706", None, None, None, date(2024, 6, 10), 92000.5, "4209102", "SC", "Betha", "https://transparencia.joinville.sc.gov.br"),
    ("Serviços de TI LTDA", "66.777.888/0001-99", "Administração", "339040", "1500", None, None, None, date(2024, 7, 3), 27400.0, "4209102", "SC", "Betha", "https://transparencia.joinville.sc.gov.br"),
    ("Gráfica Municipal ME", "77.888.999/0001-11", "Administração", "339039", "1500", None, None, None, date(2024, 8, 14), 5600.0, "4209102", "SC", "Betha", "https://transparencia.joinville.sc.gov.br"),
    ("Academia de Esportes SA", "88.999.000/0001-22", "Esporte e Lazer", "339039", "1500", None, None, None, date(2024, 9, 27), 18200.0, "4209102", "SC", "Betha", "https://transparencia.joinville.sc.gov.br"),
    # SC - Blumenau
    ("Papelaria Central ME", "10.293.847/0001-77", "Administração", "339030", "1500", None, None, None, date(2024, 6, 20), 3870.9, "4202404", "SC", "Betha", "https://transparencia.blumenau.sc.gov.br"),
    ("Transporte Escolar LTDA", "20.384.756/0001-88", "Educação", "339036", "1500", None, None, None, date(2024, 10, 8), 67000.0, "4202404", "SC", "Betha", "https://transparencia.blumenau.sc.gov.br"),
    # SP - São Paulo
    ("Metrô SP SA", "11.222.333/0001-44", "Transporte", "449051", "1706", None, None, None, date(2024, 1, 20), 4500000.0, "3550308", "SP", "SP Transparência", "https://transparencia.prefeitura.sp.gov.br"),
    ("Hospital das Clínicas FMUSP", "12.312.312/0001-23", "Saúde", "339036", "1706", None, None, None, date(2024, 2, 14), 1200000.0, "3550308", "SP", "SP Transparência", "https://transparencia.prefeitura.sp.gov.br"),
    ("Empresa de Limpeza SP LTDA", "23.423.423/0001-34", "Administração", "339039", "1500", None, None, None, date(2024, 3, 9), 780000.0, "3550308", "SP", "SP Transparência", "https://transparencia.prefeitura.sp.gov.br"),
    ("Uniforme Escolar SA", "34.534.534/0001-45", "Educação", "339030", "1500", None, None, None, date(2024, 4, 25), 340000.0, "3550308", "SP", "SP Transparência", "https://transparencia.prefeitura.sp.gov.br"),
    # RJ - Rio de Janeiro
    ("Light Energia SA", "05.999.733/0001-50", "Infraestrutura", "339039", "1706", None, None, None, date(2024, 3, 15), 2100000.0, "3304557", "RJ", "RJ Transparência", "https://transparencia.rio.rj.gov.br"),
    ("Comlurb RJ LTDA", "06.811.348/0001-78", "Administração", "339039", "1500", None, None, None, date(2024, 5, 20), 650000.0, "3304557", "RJ", "RJ Transparência", "https://transparencia.rio.rj.gov.br"),
    # DF - Legislativo Federal (CEAP)
    ("POSTO DE COMBUSTIVEL X", "11.222.333/0001-44", "Legislativo", "CEAP", "Cota Parlamentar", "Legislativo Federal", "Dep. Federal Silva", "PT", date(2024, 6, 20), 450.0, "5300108", "DF", "Camara API", "https://dadosabertos.camara.leg.br/api/v2"),
    ("LIVRARIA SENADO LTDA", "22.333.444/0001-55", "Legislativo", "CEAP", "Cota Parlamentar", "Legislativo Federal", "Sen. Costa", "MDB", date(2024, 7, 5), 1200.0, "5300108", "DF", "Senado API", "https://dadosabertos.senado.leg.br"),
    ("AGÊNCIA DE VIAGENS BRASIL", "33.444.555/0001-66", "Legislativo", "CEAP", "Cota Parlamentar", "Legislativo Federal", "Dep. Federal Souza", "PL", date(2024, 8, 12), 3800.0, "5300108", "DF", "Camara API", "https://dadosabertos.camara.leg.br/api/v2"),
    ("ASSESSORIA PARLAMENTAR ME", "44.555.666/0001-77", "Legislativo", "CEAP", "Cota Parlamentar", "Legislativo Federal", "Dep. Federal Lima", "PSDB", date(2024, 9, 3), 2500.0, "5300108", "DF", "Camara API", "https://dadosabertos.camara.leg.br/api/v2"),
    # MG - Belo Horizonte
    ("BHTrans LTDA", "01.234.567/0001-89", "Transporte", "449051", "1706", None, None, None, date(2024, 2, 28), 900000.0, "3106200", "MG", "BH Transparência", "https://transparencia.pbh.gov.br"),
    ("Fundação Municipal de Cultura", "98.765.432/0001-10", "Cultura", "339039", "1500", None, None, None, date(2024, 4, 11), 120000.0, "3106200", "MG", "BH Transparência", "https://transparencia.pbh.gov.br"),
    # BA - Salvador
    ("EMBASA SA", "15.202.937/0001-86", "Saneamento", "449051", "1706", None, None, None, date(2024, 6, 30), 1500000.0, "2927408", "BA", "Salvador Transparência", "https://transparencia.salvador.ba.gov.br"),
    # CE - Fortaleza
    ("ETUFOR CE LTDA", "07.811.404/0001-60", "Transporte", "449051", "1706", None, None, None, date(2024, 7, 22), 850000.0, "2304400", "CE", "Fortaleza Transparência", "https://transparencia.fortaleza.ce.gov.br"),
    # AM - Manaus
    ("MANAUSTUR AM SA", "04.812.785/0001-40", "Turismo", "339039", "1500", None, None, None, date(2024, 8, 17), 230000.0, "1302603", "AM", "Manaus Transparência", "https://transparencia.manaus.am.gov.br"),
]


def seed_if_empty(db: Session):
    has_data = db.scalar(select(GastoPublico.id).limit(1))
    if has_data:
        return

    now = datetime.utcnow()

    for municipio in MUNICIPIOS_INICIAIS:
        db.merge(Municipio(**municipio))

    gastos_demo = []
    for row in _GASTOS:
        (fav_nome, fav_doc, funcao, elem, fonte, cat_orig, agente, partido,
         dt, valor, ibge, uf, sistema, url) = row
        gastos_demo.append(GastoPublico(
            id=str(uuid4()),
            categoria_origem=cat_orig,
            agente_publico=agente,
            partido=partido,
            tipo_despesa=None,
            data_empenho=dt,
            valor_empenhado=valor,
            favorecido_nome=fav_nome,
            favorecido_cnpj_cpf=fav_doc,
            elemento_despesa=elem,
            fonte_recurso=fonte,
            funcao_governo=funcao,
            numero_empenho=f"{dt.year}NE{str(len(gastos_demo)+1).zfill(4)}",
            municipio_ibge=ibge,
            uf=uf,
            fornecedor_sistema=sistema,
            url_origem=url,
            atualizado_em=now,
        ))

    db.add_all(gastos_demo)
    db.commit()


def seed_mongo_if_empty():
    db = get_mongo_db()
    if db.gastos_publicos.count_documents({}, limit=1):
        return

    db.municipios.update_many({}, {"$setOnInsert": {}}, upsert=True)
    for municipio in MUNICIPIOS_INICIAIS:
        db.municipios.update_one({"codigo_ibge": municipio["codigo_ibge"]}, {"$set": municipio}, upsert=True)

    now = datetime.utcnow().isoformat()
    for idx, row in enumerate(_GASTOS, start=1):
        (
            fav_nome,
            fav_doc,
            funcao,
            elem,
            fonte,
            cat_orig,
            agente,
            partido,
            dt,
            valor,
            ibge,
            uf,
            sistema,
            url,
        ) = row
        doc = {
            "id": str(uuid4()),
            "categoria_origem": cat_orig,
            "agente_publico": agente,
            "partido": partido,
            "tipo_despesa": None,
            "data_empenho": dt.isoformat(),
            "valor_empenhado": float(valor),
            "favorecido_nome": fav_nome,
            "favorecido_cnpj_cpf": fav_doc,
            "elemento_despesa": elem,
            "fonte_recurso": fonte,
            "funcao_governo": funcao,
            "numero_empenho": f"{dt.year}NE{str(idx).zfill(4)}",
            "municipio_ibge": ibge,
            "uf": uf,
            "fornecedor_sistema": sistema,
            "url_origem": url,
            "atualizado_em": now,
        }
        db.gastos_publicos.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
