import sys
import json
import time
import threading
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")


def run_server():
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8004, log_level="critical")


threading.Thread(target=run_server, daemon=True).start()
time.sleep(5)

BASE = "http://127.0.0.1:8004"
tests = [
    "/health",
    "/api/v1/gastos/resumo",
    "/api/v1/gastos?page_size=3",
    "/api/v1/gastos/top-fornecedores?limit=3",
    "/api/v1/stats/por-funcao",
    "/api/v1/stats/por-uf",
    "/api/v1/stats/por-categoria",
    "/api/v1/stats/evolucao-mensal",
    "/api/v1/stats/por-elemento",
    "/api/v1/stats/por-partido",
    "/api/v1/municipios",
    "/api/v1/gastos/export/csv",
]

ok = 0
for path in tests:
    try:
        r = urllib.request.urlopen(BASE + path, timeout=5)
        body = r.read().decode("utf-8")
        ok += 1
        if path.endswith("/csv"):
            lines = body.strip().split("\n")
            print(f"PASS {path}  => CSV {len(lines)} linhas")
        else:
            data = json.loads(body)
            if isinstance(data, list):
                print(f"PASS {path}  => {len(data)} items")
            else:
                print(f"PASS {path}  => keys={list(data.keys())[:4]}")
    except Exception as e:
        print(f"FAIL {path}  => {e}")

print(f"\n{ok}/{len(tests)} passed")
