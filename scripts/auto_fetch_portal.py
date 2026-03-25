import argparse
import csv
import json
import os
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = os.getenv("PORTAL_TRANSPARENCIA_BASE_URL", "https://api.portaldatransparencia.gov.br")
API_KEY = os.getenv("PORTAL_TRANSPARENCIA_API_KEY", "")
OUTPUT_DIR = Path(os.getenv("PORTAL_OUTPUT_DIR", "data"))


def parse_float(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def request_page(page, data_inicio, data_fim):
    params = {"pagina": page}
    if data_inicio:
        params["dataInicial"] = data_inicio
    if data_fim:
        params["dataFinal"] = data_fim
    url = f"{BASE_URL}/api-de-dados/despesas?{urlencode(params)}"
    req = Request(url, headers={"Accept": "application/json", "chave-api-dados": API_KEY}, method="GET")
    with urlopen(req, timeout=40) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload if isinstance(payload, list) else []


def normalize(raw):
    return {
        "data": raw.get("dataDocumento") or raw.get("data") or raw.get("dataPagamento"),
        "ente": raw.get("nomeOrgaoSuperior") or raw.get("nomeUnidadeGestora") or "Executivo Federal",
        "favorecido": raw.get("nomeFornecedor") or raw.get("favorecido") or raw.get("nomeFavorecido") or "NAO INFORMADO",
        "valor": parse_float(raw.get("valor") or raw.get("valorDocumento") or raw.get("valorPago")),
        "status": "Processado",
        "categoria": "Executivo Federal",
        "origem": "Portal da Transparencia",
    }


def run_once(data_inicio, data_fim, paginas):
    rows = []
    for page in range(1, paginas + 1):
        batch = request_page(page, data_inicio, data_fim)
        if not batch:
            break
        rows.extend(normalize(item) for item in batch)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUTPUT_DIR / f"portal_transparencia_{stamp}.json"
    csv_path = OUTPUT_DIR / f"portal_transparencia_{stamp}.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["data", "ente", "favorecido", "valor", "status", "categoria", "origem"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Coleta concluida: {len(rows)} registros")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Automatiza coleta do Portal da Transparencia")
    parser.add_argument("--data-inicio", default=date.today().isoformat())
    parser.add_argument("--data-fim", default=date.today().isoformat())
    parser.add_argument("--paginas", type=int, default=3)
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval-min", type=int, default=60)
    args = parser.parse_args()

    if not API_KEY:
        print("ERRO: defina PORTAL_TRANSPARENCIA_API_KEY")
        return 2

    if not args.loop:
        run_once(args.data_inicio, args.data_fim, args.paginas)
        return 0

    while True:
        try:
            run_once(args.data_inicio, args.data_fim, args.paginas)
        except Exception as exc:
            print(f"[{datetime.now().isoformat()}] FALHA: {exc}")
        time.sleep(max(1, args.interval_min) * 60)


if __name__ == "__main__":
    raise SystemExit(main())
