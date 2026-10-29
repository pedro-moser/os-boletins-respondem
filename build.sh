#!/usr/bin/env bash
# Injeta dados/pagina_series.json em pagina/fonte.html e grava docs/index.html (servido pelo GitHub Pages).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p docs
python3 - pagina/fonte.html dados/pagina_series.json docs/index.html <<'PY'
import json, sys
fonte, dados, saida = sys.argv[1:]
html = open(fonte, encoding="utf-8").read()
assert html.count("__DADOS__") == 1, "fonte.html deve ter exatamente um __DADOS__"
open(saida, "w", encoding="utf-8").write(html.replace("__DADOS__", json.dumps(json.load(open(dados, encoding="utf-8")), ensure_ascii=False, separators=(",", ":"))))
PY
touch docs/.nojekyll
echo "ok: docs/index.html"
