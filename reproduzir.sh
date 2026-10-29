#!/usr/bin/env bash
# Reproduz a análise do zero: baixa os arquivos do TSE (dados/urls_*.txt), confere o SHA-512, extrai os CSVs,
# monta as tabelas por seção, roda as análises (saída em resultados/) e gera a página (docs/index.html).
# Requer: bash, curl, unzip, sha512sum e uv (https://docs.astral.sh/uv/). Ocupa ~14 GB em dados/.
# É idempotente: arquivos já baixados e conferidos não são baixados de novo; etapas prontas são puladas.
set -euo pipefail
cd "$(dirname "$0")"
PY=(uv run -q --no-project --python 3.13 --with polars==2.1.0 --with numpy==2.5.4 python -I)
etapa() { printf '\n== %s\n' "$*"; }

# lista de URLs -> diretório em dados/
declare -A ORIGEM=(
  [urls_2t.txt]=bweb_2t [urls_1t.txt]=bweb_1t
  [urls_2022_2t.txt]=bweb_2022_2t [urls_2022_1t.txt]=bweb_2022_1t
  [urls_2018_2t.txt]=bweb_2018_2t [urls_cesp.txt]=cesp_2t [urls_arqurna_ac.txt]=arqurna_2t
)

etapa "1. Download (TSE, Portal de Dados Abertos)"
for lista in "${!ORIGEM[@]}"; do
  dir="dados/${ORIGEM[$lista]}"; mkdir -p "$dir"
  falta=$(while read -r u; do [ -s "$dir/$(basename "$u")" ] || echo "$u"; done < "dados/$lista")
  [ -z "$falta" ] && { echo "$dir: completo"; continue; }
  echo "$dir: baixando $(echo "$falta" | wc -l) arquivos"
  echo "$falta" | (cd "$dir" && xargs -P 8 -n 1 curl -sSfL --retry 3 -O)
done

etapa "2. Conferência do SHA-512"
for dir in "${ORIGEM[@]}"; do
  for z in "dados/$dir"/*.zip; do
    if [ -f "$z.sha512" ]; then  # publicado pelo TSE
      esp=$(grep -oiE '^[0-9a-f]{128}' "$z.sha512" | head -1 | tr 'A-F' 'a-f')
    else  # o TSE não publica hash dos logs; vale o registrado quando a análise foi feita
      esp=$(grep -F " $(basename "$z")" dados/sha512_nao_oficial.txt | cut -d' ' -f1)
    fi
    [ -n "$esp" ] && [ "$esp" = "$(sha512sum "$z" | cut -d' ' -f1)" ] || { echo "FALHOU: $z"; exit 1; }
  done
  echo "dados/$dir: $(ls "dados/$dir"/*.zip | wc -l) arquivos OK"
done

etapa "3. Extração dos CSVs"
extrair() {  # zip_dir csv_dir [filtro de presidente]
  local de="dados/$1" para="dados/$2"
  [ -f "$para/.ok" ] && { echo "$para: pronto"; return; }
  mkdir -p "$para"
  for z in "$de"/*.zip; do
    if [ "${3:-}" = pres ]; then  # 1º turno: só o cargo 1 (o arquivo completo tem todos os cargos)
      unzip -p "$z" '*.csv' | grep -a -E '^"DT_GERACAO"|;"?1"?;"Presidente";' > "$para/$(basename "$z" .zip).csv"
    else
      unzip -qo -j "$z" '*.csv' -d "$para"
    fi
  done
  touch "$para/.ok"; echo "$para: $(ls "$para"/*.csv | wc -l) CSVs"
}
extrair bweb_2t csv_2t
extrair bweb_2022_2t csv_2022_2t
extrair bweb_2018_2t csv_2018_2t
extrair bweb_1t csv_1t_pres pres
extrair bweb_2022_1t csv_2022_1t_pres pres
extrair cesp_2t csv_cesp

etapa "4. Tabelas por seção"
[ -f dados/secoes_2t.parquet ]      || "${PY[@]}" scripts/01_build.py dados/csv_2t dados/secoes_2t.parquet
[ -f dados/secoes_2022_2t.parquet ] || "${PY[@]}" scripts/01_build.py dados/csv_2022_2t dados/secoes_2022_2t.parquet
[ -f dados/secoes_2018_2t.parquet ] || "${PY[@]}" scripts/01_build.py dados/csv_2018_2t dados/secoes_2018_2t.parquet 17
[ -f dados/secoes_1t.parquet ]      || "${PY[@]}" scripts/07_build_1t.py dados/csv_1t_pres dados/secoes_1t.parquet dados/candidatos_1t.parquet
[ -f dados/secoes_2022_1t.parquet ] || "${PY[@]}" scripts/07_build_1t.py dados/csv_2022_1t_pres dados/secoes_2022_1t.parquet dados/candidatos_2022_1t.parquet
[ -f dados/modelo_ac.parquet ]      || "${PY[@]}" scripts/11_modelo_ac.py dados/arqurna_2t/bu_imgbu_logjez_rdv_vscmr_2026_2t_AC.zip dados/modelo_ac.parquet
echo "ok"

etapa "5. Análises (saída de cada script em resultados/)"
mkdir -p resultados
d=dados
analise() { local nome; nome=$(basename "$1" .py); echo "$nome"; "${PY[@]}" "$@" > "resultados/$nome.txt"; }
analise scripts/02_horario.py $d/secoes_2t.parquet
analise scripts/03_controle.py $d/secoes_2t.parquet $d/secoes_2022_2t.parquet
analise scripts/04_cauda_e_limite.py $d/secoes_2t.parquet $d/secoes_2022_2t.parquet
analise scripts/05_biometria_unanimidade.py $d/secoes_2t.parquet $d/secoes_2022_2t.parquet
analise scripts/06_tres_eleicoes.py $d/secoes_2018_2t.parquet $d/secoes_2022_2t.parquet $d/secoes_2t.parquet
analise scripts/08_turnos.py $d/secoes_1t.parquet $d/secoes_2t.parquet $d/secoes_2022_1t.parquet $d/secoes_2022_2t.parquet
analise scripts/09_comparecimento_zeros.py $d/secoes_2t.parquet $d/secoes_2022_2t.parquet $d/secoes_2018_2t.parquet $d/secoes_1t.parquet $d/secoes_2022_1t.parquet
analise scripts/10_virada.py $d/secoes_2t.parquet
analise scripts/10b_virada_controle.py $d/secoes_2t.parquet $d/secoes_2022_2t.parquet
analise scripts/12_series.py $d/csv_2t $d/csv_2022_2t
analise scripts/13_urnas_antigas.py $d/secoes_2t.parquet $d/csv_2t $d/secoes_2022_2t.parquet $d/csv_2022_2t
analise scripts/14_urnas_trocadas.py $d/csv_cesp $d/csv_2t $d/secoes_2t.parquet
analise scripts/16_crescimento_uf.py $d/secoes_1t.parquet $d/secoes_2t.parquet $d/secoes_2022_1t.parquet $d/secoes_2022_2t.parquet
analise scripts/17_ordem_aleatoria.py $d/secoes_2022_2t.parquet $d/secoes_2t.parquet

etapa "6. Página"
"${PY[@]}" scripts/15_dados_pagina.py $d/secoes_2018_2t.parquet $d/secoes_2022_2t.parquet $d/secoes_2t.parquet $d/pagina_series.json > resultados/15_dados_pagina.txt
./build.sh
echo; echo "Pronto. Compare com a versão publicada: git diff --stat resultados/ dados/pagina_series.json docs/"
