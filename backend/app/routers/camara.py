# -*- coding: utf-8 -*-
"""
Integração com a API de Dados Abertos da Câmara dos Deputados.
Base URL: https://dadosabertos.camara.leg.br/api/v2
Documentação: https://dadosabertos.camara.leg.br/swagger/api.html
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

CAMARA_BASE = "https://dadosabertos.camara.leg.br/api/v2"
DEFAULT_TIMEOUT = 30
DEFAULT_ITENS = 20
MAX_ITENS = 100

router = APIRouter(prefix="/camara", tags=["camara"])


# ---------------------------------------------------------------------------
# Utilitário de requisição
# ---------------------------------------------------------------------------

def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    clean: dict[str, str] = {}
    for k, v in (params or {}).items():
        if v is not None and v != "":
            clean[k] = str(v)

    url = f"{CAMARA_BASE}{path}"
    if clean:
        url = f"{url}?{urlencode(clean)}"

    req = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(status_code=exc.code, detail=f"Câmara API: {exc.reason}") from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"Câmara API indisponível: {exc.reason}") from exc


def _data(payload: Any) -> Any:
    if isinstance(payload, dict):
        return payload.get("dados", payload)
    return payload


# ---------------------------------------------------------------------------
# Deputados
# ---------------------------------------------------------------------------

@router.get("/deputados", summary="Lista deputados federais")
def listar_deputados(
    nome: str | None = Query(default=None, description="Parte do nome parlamentar"),
    siglaUf: str | None = Query(default=None, min_length=2, max_length=2, description="UF ex: SP, RJ"),
    siglaPartido: str | None = Query(default=None, description="Sigla do partido ex: PT, PL"),
    siglaSexo: str | None = Query(default=None, pattern="^[MF]$", description="M ou F"),
    idLegislatura: int | None = Query(default=None, description="ID da legislatura"),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get("/deputados", {
        "nome": nome, "siglaUf": siglaUf, "siglaPartido": siglaPartido,
        "siglaSexo": siglaSexo, "idLegislatura": idLegislatura,
        "pagina": pagina, "itens": itens, "ordem": "ASC", "ordenarPor": "nome",
    })
    return {"dados": _data(payload), "fonte": "Câmara API", "pagina": pagina}


@router.get("/deputados/{id}", summary="Detalhes de um deputado")
def detalhe_deputado(id: int):
    payload = _get(f"/deputados/{id}")
    return _data(payload)


@router.get("/deputados/{id}/despesas", summary="Despesas CEAP de um deputado")
def despesas_deputado(
    id: int,
    ano: int | None = Query(default=None, description="Ano das despesas"),
    mes: int | None = Query(default=None, ge=1, le=12, description="Mês (1-12)"),
    cnpjCpfFornecedor: str | None = Query(default=None, description="CNPJ ou CPF do fornecedor"),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/deputados/{id}/despesas", {
        "ano": ano, "mes": mes, "cnpjCpfFornecedor": cnpjCpfFornecedor,
        "pagina": pagina, "itens": itens, "ordem": "DESC", "ordenarPor": "ano",
    })
    return {"deputado_id": id, "dados": _data(payload), "fonte": "Câmara API"}


@router.get("/deputados/{id}/discursos", summary="Discursos de um deputado")
def discursos_deputado(
    id: int,
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/deputados/{id}/discursos", {
        "dataInicio": dataInicio, "dataFim": dataFim,
        "pagina": pagina, "itens": itens,
    })
    return {"deputado_id": id, "dados": _data(payload)}


@router.get("/deputados/{id}/frentes", summary="Frentes parlamentares de um deputado")
def frentes_deputado(id: int, pagina: int = Query(default=1, ge=1)):
    payload = _get(f"/deputados/{id}/frentes", {"pagina": pagina})
    return {"deputado_id": id, "dados": _data(payload)}


@router.get("/deputados/{id}/orgaos", summary="Órgãos/comissões de um deputado")
def orgaos_deputado(
    id: int,
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/deputados/{id}/orgaos", {
        "dataInicio": dataInicio, "dataFim": dataFim,
        "pagina": pagina, "itens": itens,
    })
    return {"deputado_id": id, "dados": _data(payload)}


@router.get("/deputados/{id}/historico", summary="Histórico parlamentar de um deputado")
def historico_deputado(
    id: int,
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/deputados/{id}/historico", {"pagina": pagina, "itens": itens})
    return {"deputado_id": id, "dados": _data(payload)}


@router.get("/deputados/{id}/profissoes", summary="Profissões declaradas por um deputado")
def profissoes_deputado(id: int, pagina: int = Query(default=1, ge=1)):
    payload = _get(f"/deputados/{id}/profissoes", {"pagina": pagina})
    return {"deputado_id": id, "dados": _data(payload)}


# ---------------------------------------------------------------------------
# Partidos
# ---------------------------------------------------------------------------

@router.get("/partidos", summary="Lista partidos políticos")
def listar_partidos(
    sigla: str | None = Query(default=None, description="Sigla do partido"),
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
    idLegislatura: int | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get("/partidos", {
        "sigla": sigla, "dataInicio": dataInicio, "dataFim": dataFim,
        "idLegislatura": idLegislatura, "pagina": pagina, "itens": itens,
        "ordem": "ASC", "ordenarPor": "sigla",
    })
    return {"dados": _data(payload), "fonte": "Câmara API"}


@router.get("/partidos/{id}", summary="Detalhes de um partido")
def detalhe_partido(id: int):
    payload = _get(f"/partidos/{id}")
    return _data(payload)


@router.get("/partidos/{id}/membros", summary="Deputados de um partido")
def membros_partido(
    id: int,
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
    idLegislatura: int | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/partidos/{id}/membros", {
        "dataInicio": dataInicio, "dataFim": dataFim,
        "idLegislatura": idLegislatura, "pagina": pagina, "itens": itens,
    })
    return {"partido_id": id, "dados": _data(payload)}


@router.get("/partidos/{id}/lideres", summary="Líderes de um partido")
def lideres_partido(
    id: int,
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/partidos/{id}/lideres", {"pagina": pagina, "itens": itens})
    return {"partido_id": id, "dados": _data(payload)}


# ---------------------------------------------------------------------------
# Proposições
# ---------------------------------------------------------------------------

@router.get("/proposicoes", summary="Lista proposições (PL, PEC, MPV...)")
def listar_proposicoes(
    siglaTipo: str | None = Query(default=None, description="Tipo: PL, PEC, MPV, PDC..."),
    numero: int | None = Query(default=None),
    ano: int | None = Query(default=None),
    autor: str | None = Query(default=None, description="Nome parcial do autor"),
    siglaPartidoAutor: str | None = Query(default=None),
    keywords: str | None = Query(default=None, description="Palavras-chave"),
    dataApresentacaoInicio: date | None = Query(default=None),
    dataApresentacaoFim: date | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get("/proposicoes", {
        "siglaTipo": siglaTipo, "numero": numero, "ano": ano,
        "autor": autor, "siglaPartidoAutor": siglaPartidoAutor,
        "keywords": keywords,
        "dataApresentacaoInicio": dataApresentacaoInicio,
        "dataApresentacaoFim": dataApresentacaoFim,
        "pagina": pagina, "itens": itens,
        "ordem": "DESC", "ordenarPor": "id",
    })
    return {"dados": _data(payload), "fonte": "Câmara API"}


@router.get("/proposicoes/{id}", summary="Detalhes de uma proposição")
def detalhe_proposicao(id: int):
    payload = _get(f"/proposicoes/{id}")
    return _data(payload)


@router.get("/proposicoes/{id}/autores", summary="Autores de uma proposição")
def autores_proposicao(id: int, pagina: int = Query(default=1, ge=1)):
    payload = _get(f"/proposicoes/{id}/autores", {"pagina": pagina})
    return {"proposicao_id": id, "dados": _data(payload)}


@router.get("/proposicoes/{id}/tramitacoes", summary="Tramitação legislativa de uma proposição")
def tramitacoes_proposicao(
    id: int,
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
):
    payload = _get(f"/proposicoes/{id}/tramitacoes", {
        "dataInicio": dataInicio, "dataFim": dataFim, "pagina": pagina,
    })
    return {"proposicao_id": id, "dados": _data(payload)}


@router.get("/proposicoes/{id}/votacoes", summary="Votações de uma proposição")
def votacoes_proposicao(
    id: int,
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/proposicoes/{id}/votacoes", {"pagina": pagina, "itens": itens})
    return {"proposicao_id": id, "dados": _data(payload)}


@router.get("/proposicoes/{id}/temas", summary="Temas de uma proposição")
def temas_proposicao(id: int, pagina: int = Query(default=1, ge=1)):
    payload = _get(f"/proposicoes/{id}/temas", {"pagina": pagina})
    return {"proposicao_id": id, "dados": _data(payload)}


@router.get("/proposicoes/{id}/relacionadas", summary="Proposições relacionadas")
def relacionadas_proposicao(id: int, pagina: int = Query(default=1, ge=1)):
    payload = _get(f"/proposicoes/{id}/relacionadas", {"pagina": pagina})
    return {"proposicao_id": id, "dados": _data(payload)}


# ---------------------------------------------------------------------------
# Votações
# ---------------------------------------------------------------------------

@router.get("/votacoes", summary="Lista votações da Câmara")
def listar_votacoes(
    idProposicao: int | None = Query(default=None),
    idEvento: int | None = Query(default=None),
    idOrgao: int | None = Query(default=None),
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get("/votacoes", {
        "idProposicao": idProposicao, "idEvento": idEvento, "idOrgao": idOrgao,
        "dataInicio": dataInicio, "dataFim": dataFim,
        "pagina": pagina, "itens": itens, "ordem": "DESC", "ordenarPor": "dataHoraRegistro",
    })
    return {"dados": _data(payload), "fonte": "Câmara API"}


@router.get("/votacoes/{id}", summary="Detalhes de uma votação")
def detalhe_votacao(id: str):
    payload = _get(f"/votacoes/{id}")
    return _data(payload)


@router.get("/votacoes/{id}/votos", summary="Como cada deputado votou")
def votos_votacao(
    id: str,
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/votacoes/{id}/votos", {"pagina": pagina, "itens": itens})
    return {"votacao_id": id, "dados": _data(payload)}


@router.get("/votacoes/{id}/orientacoes", summary="Orientações dos líderes em uma votação")
def orientacoes_votacao(id: str, pagina: int = Query(default=1, ge=1)):
    payload = _get(f"/votacoes/{id}/orientacoes", {"pagina": pagina})
    return {"votacao_id": id, "dados": _data(payload)}


# ---------------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------------

@router.get("/eventos", summary="Lista eventos (sessões, reuniões de comissão...)")
def listar_eventos(
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
    idOrgao: int | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get("/eventos", {
        "dataInicio": dataInicio, "dataFim": dataFim,
        "idOrgao": idOrgao, "pagina": pagina, "itens": itens,
        "ordem": "DESC", "ordenarPor": "dataHoraInicio",
    })
    return {"dados": _data(payload), "fonte": "Câmara API"}


@router.get("/eventos/{id}", summary="Detalhes de um evento")
def detalhe_evento(id: int):
    payload = _get(f"/eventos/{id}")
    return _data(payload)


@router.get("/eventos/{id}/pauta", summary="Pauta de um evento")
def pauta_evento(id: int, pagina: int = Query(default=1, ge=1)):
    payload = _get(f"/eventos/{id}/pauta", {"pagina": pagina})
    return {"evento_id": id, "dados": _data(payload)}


@router.get("/eventos/{id}/votacoes", summary="Votações de um evento")
def votacoes_evento(
    id: int,
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/eventos/{id}/votacoes", {"pagina": pagina, "itens": itens})
    return {"evento_id": id, "dados": _data(payload)}


@router.get("/eventos/{id}/deputados", summary="Deputados presentes em um evento")
def deputados_evento(id: int, pagina: int = Query(default=1, ge=1)):
    payload = _get(f"/eventos/{id}/deputados", {"pagina": pagina})
    return {"evento_id": id, "dados": _data(payload)}


# ---------------------------------------------------------------------------
# Órgãos / Comissões
# ---------------------------------------------------------------------------

@router.get("/orgaos", summary="Lista comissões e órgãos legislativos")
def listar_orgaos(
    sigla: str | None = Query(default=None),
    nome: str | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get("/orgaos", {
        "sigla": sigla, "nome": nome,
        "pagina": pagina, "itens": itens,
    })
    return {"dados": _data(payload), "fonte": "Câmara API"}


@router.get("/orgaos/{id}", summary="Detalhes de um órgão")
def detalhe_orgao(id: int):
    payload = _get(f"/orgaos/{id}")
    return _data(payload)


@router.get("/orgaos/{id}/membros", summary="Membros de um órgão/comissão")
def membros_orgao(
    id: int,
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
):
    payload = _get(f"/orgaos/{id}/membros", {
        "dataInicio": dataInicio, "dataFim": dataFim, "pagina": pagina,
    })
    return {"orgao_id": id, "dados": _data(payload)}


@router.get("/orgaos/{id}/votacoes", summary="Votações de um órgão/comissão")
def votacoes_orgao(
    id: int,
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
    idProposicao: int | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/orgaos/{id}/votacoes", {
        "dataInicio": dataInicio, "dataFim": dataFim,
        "idProposicao": idProposicao, "pagina": pagina, "itens": itens,
    })
    return {"orgao_id": id, "dados": _data(payload)}


# ---------------------------------------------------------------------------
# Frentes Parlamentares
# ---------------------------------------------------------------------------

@router.get("/frentes", summary="Lista frentes parlamentares")
def listar_frentes(
    idLegislatura: int | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
):
    payload = _get("/frentes", {"idLegislatura": idLegislatura, "pagina": pagina})
    return {"dados": _data(payload), "fonte": "Câmara API"}


@router.get("/frentes/{id}", summary="Detalhes de uma frente parlamentar")
def detalhe_frente(id: int):
    payload = _get(f"/frentes/{id}")
    return _data(payload)


@router.get("/frentes/{id}/membros", summary="Membros de uma frente parlamentar")
def membros_frente(id: int, pagina: int = Query(default=1, ge=1)):
    payload = _get(f"/frentes/{id}/membros", {"pagina": pagina})
    return {"frente_id": id, "dados": _data(payload)}


# ---------------------------------------------------------------------------
# Legislaturas
# ---------------------------------------------------------------------------

@router.get("/legislaturas", summary="Lista legislaturas")
def listar_legislaturas(
    data: date | None = Query(default=None, description="Retorna a legislatura ativa nessa data"),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get("/legislaturas", {
        "data": data, "pagina": pagina, "itens": itens,
        "ordem": "DESC", "ordenarPor": "id",
    })
    return {"dados": _data(payload), "fonte": "Câmara API"}


@router.get("/legislaturas/{id}", summary="Detalhes de uma legislatura")
def detalhe_legislatura(id: int):
    payload = _get(f"/legislaturas/{id}")
    return _data(payload)


@router.get("/legislaturas/{id}/mesa", summary="Mesa Diretora de uma legislatura")
def mesa_legislatura(
    id: int,
    dataInicio: date | None = Query(default=None),
    dataFim: date | None = Query(default=None),
):
    payload = _get(f"/legislaturas/{id}/mesa", {
        "dataInicio": dataInicio, "dataFim": dataFim,
    })
    return {"legislatura_id": id, "dados": _data(payload)}


@router.get("/legislaturas/{id}/lideres", summary="Líderes de uma legislatura")
def lideres_legislatura(
    id: int,
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get(f"/legislaturas/{id}/lideres", {"pagina": pagina, "itens": itens})
    return {"legislatura_id": id, "dados": _data(payload)}


# ---------------------------------------------------------------------------
# Blocos Partidários
# ---------------------------------------------------------------------------

@router.get("/blocos", summary="Lista blocos partidários")
def listar_blocos(
    idLegislatura: int | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=DEFAULT_ITENS, ge=1, le=MAX_ITENS),
):
    payload = _get("/blocos", {
        "idLegislatura": idLegislatura, "pagina": pagina, "itens": itens,
    })
    return {"dados": _data(payload), "fonte": "Câmara API"}


@router.get("/blocos/{id}", summary="Detalhes de um bloco partidário")
def detalhe_bloco(id: int):
    payload = _get(f"/blocos/{id}")
    return _data(payload)


@router.get("/blocos/{id}/partidos", summary="Partidos de um bloco")
def partidos_bloco(id: int, data: date | None = Query(default=None)):
    payload = _get(f"/blocos/{id}/partidos", {"data": data})
    return {"bloco_id": id, "dados": _data(payload)}


# ---------------------------------------------------------------------------
# Referências (tabelas de código/label)
# ---------------------------------------------------------------------------

@router.get("/referencias/situacoes-deputado", summary="Códigos de situação de deputado")
def ref_situacoes_deputado():
    return _data(_get("/referencias/deputados/codSituacao"))


@router.get("/referencias/tipos-proposicao", summary="Tipos de proposição (PL, PEC, MPV...)")
def ref_tipos_proposicao():
    try:
        return _data(_get("/referencias/proposicoes/siglaTipo"))
    except HTTPException:
        return [
            {"sigla": "PL", "nome": "Projeto de Lei"},
            {"sigla": "PEC", "nome": "Proposta de Emenda a Constituicao"},
            {"sigla": "MPV", "nome": "Medida Provisoria"},
            {"sigla": "PLP", "nome": "Projeto de Lei Complementar"},
            {"sigla": "PDL", "nome": "Projeto de Decreto Legislativo"},
        ]


@router.get("/referencias/temas-proposicao", summary="Temas/áreas das proposições")
def ref_temas_proposicao():
    try:
        return _data(_get("/referencias/proposicoes/codTema"))
    except HTTPException:
        return [
            {"cod": 40, "nome": "Economia"},
            {"cod": 46, "nome": "Saude"},
            {"cod": 62, "nome": "Educacao"},
            {"cod": 42, "nome": "Direitos Humanos"},
            {"cod": 53, "nome": "Administracao Publica"},
        ]


@router.get("/referencias/tipos-evento", summary="Tipos de evento")
def ref_tipos_evento():
    return _data(_get("/referencias/eventos/codTipoEvento"))


@router.get("/referencias/tipos-orgao", summary="Tipos de órgão/comissão")
def ref_tipos_orgao():
    return _data(_get("/referencias/orgaos/codTipoOrgao"))


@router.get("/referencias/tipos-voto", summary="Tipos de voto (Sim, Não, Abstenção...)")
def ref_tipos_voto():
    try:
        return _data(_get("/referencias/votacoes/tiposVoto"))
    except HTTPException:
        return [
            {"cod": "Sim", "nome": "Sim"},
            {"cod": "Nao", "nome": "Não"},
            {"cod": "Abstencao", "nome": "Abstenção"},
            {"cod": "Obstrucao", "nome": "Obstrução"},
            {"cod": "Artigo17", "nome": "Art. 17"},
        ]
