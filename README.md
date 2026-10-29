# Os Boletins Respondem

Checagem, com os boletins de urna oficiais do TSE, das teses de fraude que circulam sobre o
2º turno de 2026 (com 2022 e 2018 como controle).

- **Página:** https://pedro-moser.github.io/os-boletins-respondem/
- **Relatório completo:** [`RELATORIO.md`](RELATORIO.md)

## Reproduzir

Os dados brutos (~14 GB) não estão no repositório. As listas de arquivos do Portal de Dados
Abertos do TSE estão em `dados/urls_*.txt`; os scripts em `scripts/` são numerados na ordem
de execução e cada um documenta, no topo, a entrada e a saída.

## Atualizar a página

1. Rodar o script da nova análise e escrever a seção no `RELATORIO.md`.
2. Editar `pagina/fonte.html` (o template; os dados dos gráficos entram no lugar de `__DADOS__`).
3. Se os gráficos mudaram: `scripts/15_dados_pagina.py` → `dados/pagina_series.json`.
4. `./build.sh` → `docs/index.html`, que é o que o GitHub Pages serve.
