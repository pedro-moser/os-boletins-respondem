# Os Boletins Respondem

Checagem, com os boletins de urna oficiais do TSE, das teses de fraude que circulam sobre o
2º turno de 2026 (com 2022 e 2018 como controle).

- **Página:** https://pedro-moser.github.io/os-boletins-respondem/
- **Relatório completo:** [`RELATORIO.md`](RELATORIO.md)

## Reproduzir do zero

Requer Linux ou macOS com `bash`, `curl`, `unzip`, `sha512sum` e [uv](https://docs.astral.sh/uv/)
(que instala Python 3.13, polars 2.1.0 e numpy 2.5.4 sozinho). Ocupa ~14 GB.

```bash
git clone https://github.com/pedro-moser/os-boletins-respondem
cd os-boletins-respondem
./reproduzir.sh
git diff --stat   # nada mudou = você obteve os mesmos números
```

O script:

1. baixa os arquivos listados em `dados/urls_*.txt` do Portal de Dados Abertos do TSE;
2. confere o SHA-512 de cada arquivo contra o `.sha512` publicado pelo TSE e para se algum
   não bater. O TSE não publica hash dos logs das urnas (usados só para calibrar o modelo da urna
   pelo número de série, seção 13); para esse arquivo vale o hash registrado em
   `dados/sha512_nao_oficial.txt` no dia do download;
3. extrai os CSVs (no 1º turno, só o cargo de presidente) e monta as tabelas por seção;
4. roda cada análise e grava a saída em `resultados/NN_*.txt`. São esses os números citados no
   relatório e na página;
5. gera `dados/pagina_series.json` e `docs/index.html`.

Pode ser interrompido e retomado: o que já foi baixado e conferido não é baixado de novo.

## Atualizar a página

1. Rodar o script da nova análise e escrever a seção no `RELATORIO.md`.
2. Editar `pagina/fonte.html` (o template; os dados dos gráficos entram no lugar de `__DADOS__`).
3. Acrescentar a análise ao `reproduzir.sh`.
4. `./build.sh` → `docs/index.html`, que é o que o GitHub Pages serve.
