"""1º turno (presidente; 2026 ou 2022): tabela por seção com Lula, Flávio, demais candidatos, brancos e nulos.
Entrada: CSVs BWeb já filtrados para CD_CARGO_PERGUNTA=1."""
import sys
from pathlib import Path
import polars as pl

csv_dir, out_sec, out_cand = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
cols = ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "NR_LOCAL_VOTACAO", "QT_APTOS",
        "QT_COMPARECIMENTO", "DS_TIPO_VOTAVEL", "NR_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS", "NR_URNA_EFETIVADA",
        "DT_ENCERRAMENTO", "QT_ELEI_BIOM_SEM_HABILITACAO"]
RENAME = {"QT_ELEITORES_BIOMETRIA_NH": "QT_ELEI_BIOM_SEM_HABILITACAO"}  # nome de 2022
def ler(f):
    df = pl.read_csv(f, separator=";", encoding="latin1", infer_schema=False)
    return df.rename({k: v for k, v in RENAME.items() if k in df.columns}).select(cols)
raw = pl.concat([ler(f) for f in sorted(csv_dir.glob("*.csv"))]).with_columns(
    pl.col("QT_VOTOS", "QT_APTOS", "QT_COMPARECIMENTO").cast(pl.Int64))
key = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
raw.group_by("NR_VOTAVEL", "NM_VOTAVEL").agg(pl.col("QT_VOTOS").sum()).sort("QT_VOTOS", descending=True).write_parquet(out_cand)
nominal = pl.col("DS_TIPO_VOTAVEL") == "Nominal"
sec = raw.group_by(key).agg(
    lula1=pl.col("QT_VOTOS").filter(pl.col("NR_VOTAVEL") == "13").sum(),
    flavio1=pl.col("QT_VOTOS").filter(pl.col("NR_VOTAVEL") == "22").sum(),
    outros1=pl.col("QT_VOTOS").filter(nominal & ~pl.col("NR_VOTAVEL").is_in(["13", "22"])).sum(),
    brancos1=pl.col("QT_VOTOS").filter(pl.col("DS_TIPO_VOTAVEL") == "Branco").sum(),
    nulos1=pl.col("QT_VOTOS").filter(pl.col("DS_TIPO_VOTAVEL") == "Nulo").sum(),
    aptos1=pl.col("QT_APTOS").first(), comp1=pl.col("QT_COMPARECIMENTO").first(),
    urna1=pl.col("NR_URNA_EFETIVADA").first(),
    biom_sem1=pl.col("QT_ELEI_BIOM_SEM_HABILITACAO").first().cast(pl.Int64, strict=False),
)
# votos de cada candidato "menor", para estimar transferências
cand = raw.filter(nominal, ~pl.col("NR_VOTAVEL").is_in(["13", "22"])).group_by("NR_VOTAVEL").agg(pl.col("QT_VOTOS").sum())
for nr in cand.sort("QT_VOTOS", descending=True)["NR_VOTAVEL"].head(4):
    sec = sec.join(raw.filter(pl.col("NR_VOTAVEL") == nr).group_by(key).agg(pl.col("QT_VOTOS").sum().alias(f"c{nr}")),
                   on=key, how="left")
sec = sec.with_columns(pl.col("^c\\d+$").fill_null(0))
sec.sort(key).write_parquet(out_sec)  # ordem fixa: o group_by não garante ordem
print(sec.height, "seções | Lula", sec["lula1"].sum(), "| Flávio", sec["flavio1"].sum(), "| outros", sec["outros1"].sum(),
      "| brancos", sec["brancos1"].sum(), "| nulos", sec["nulos1"].sum(), "| comparec", sec["comp1"].sum())
print(pl.read_parquet(out_cand))
