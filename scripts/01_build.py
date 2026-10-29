"""Lê os CSVs BWeb do 2º turno (presidente) e gera uma tabela por seção.

Uso: 01_build.py <csv_dir> <saida.parquet> [nº do adversário do 13, padrão 22]
As colunas 'lula' e 'flavio' guardam, respectivamente, o nº 13 e o adversário
(2026: Lula × Flávio; 2022: Lula × Bolsonaro; 2018: Haddad × Bolsonaro, nº 17)."""
import sys
from pathlib import Path
import polars as pl

csv_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
adv = sys.argv[3] if len(sys.argv) > 3 else "22"
cols = ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "NR_LOCAL_VOTACAO",
        "CD_CARGO_PERGUNTA", "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES", "DS_TIPO_URNA",
        "DS_TIPO_VOTAVEL", "NR_VOTAVEL", "QT_VOTOS", "DS_SECOES_AGREGADAS",
        "DT_ABERTURA", "DT_ENCERRAMENTO", "QT_ELEI_BIOM_SEM_HABILITACAO", "DT_BU_RECEBIDO"]

RENAME = {"SG_ UF": "SG_UF", "DS_AGREGADAS": "DS_SECOES_AGREGADAS", "QT_ELEITORES_BIOMETRIA_NH": "QT_ELEI_BIOM_SEM_HABILITACAO"}
frames = []
for f in sorted(csv_dir.glob("*.csv")):
    df = pl.read_csv(f, separator=";", encoding="latin1", infer_schema=False)
    # Nomes de 2022 -> nomes de 2026
    df = df.rename({k: v for k, v in RENAME.items() if k in df.columns})
    # 2018 não tem DT_BU_RECEBIDO
    df = df.with_columns(pl.lit(None, pl.String).alias(c) for c in cols if c not in df.columns).select(cols)
    df = df.with_columns(pl.col("CD_MUNICIPIO").str.strip_chars_start("0"))
    frames.append(df.filter(pl.col("CD_CARGO_PERGUNTA") == "1"))
raw = pl.concat(frames)

key = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
votos = raw.with_columns(pl.col("QT_VOTOS").cast(pl.Int64))
pivot = votos.group_by(key).agg(
    lula=pl.col("QT_VOTOS").filter(pl.col("NR_VOTAVEL") == "13").sum(),
    flavio=pl.col("QT_VOTOS").filter(pl.col("NR_VOTAVEL") == adv).sum(),
    brancos=pl.col("QT_VOTOS").filter(pl.col("DS_TIPO_VOTAVEL") == "Branco").sum(),
    nulos=pl.col("QT_VOTOS").filter(pl.col("DS_TIPO_VOTAVEL") == "Nulo").sum(),
    outros_votaveis=pl.col("NR_VOTAVEL").filter(~pl.col("NR_VOTAVEL").is_in(["13", adv, "95", "96"])).unique().implode(),
)
meta = raw.group_by(key).agg(
    pl.col(c).first() for c in ["NM_MUNICIPIO", "NR_LOCAL_VOTACAO", "QT_APTOS", "QT_COMPARECIMENTO",
                                 "QT_ABSTENCOES", "DS_TIPO_URNA", "DS_SECOES_AGREGADAS", "DT_ABERTURA",
                                 "DT_ENCERRAMENTO", "QT_ELEI_BIOM_SEM_HABILITACAO", "DT_BU_RECEBIDO"]
)
sec = pivot.join(meta, on=key).with_columns(
    pl.col("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES").cast(pl.Int64),
    biom_sem=pl.col("QT_ELEI_BIOM_SEM_HABILITACAO").cast(pl.Int64, strict=False),
    abertura=pl.coalesce(pl.col("DT_ABERTURA").str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False), pl.col("DT_ABERTURA").str.to_datetime("%d/%m/%Y %H:%M:%S", strict=False)),
    encerramento=pl.coalesce(pl.col("DT_ENCERRAMENTO").str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False), pl.col("DT_ENCERRAMENTO").str.to_datetime("%d/%m/%Y %H:%M:%S", strict=False)),
)
# Fuso: todas as urnas no Brasil abrem às 08h de Brasília. A hora modal de abertura por
# município revela o deslocamento local -> Brasília (06h = -2h, 07h = -1h, 09h = +1h).
tz = (sec.filter(pl.col("SG_UF") != "ZZ", pl.col("abertura").is_not_null())
      .group_by("SG_UF", "CD_MUNICIPIO")
      .agg(hora_abert=pl.col("abertura").dt.hour().mode().first())
      .with_columns(offset_h=(8 - pl.col("hora_abert")).cast(pl.Int64)))
sec = sec.join(tz.select("SG_UF", "CD_MUNICIPIO", "offset_h"), on=["SG_UF", "CD_MUNICIPIO"], how="left")
sec = sec.with_columns(
    enc_brt=pl.col("encerramento") + pl.duration(hours=pl.col("offset_h").fill_null(0)),
)
sec.drop("QT_ELEI_BIOM_SEM_HABILITACAO").write_parquet(out)
print(sec.height, "seções;", sec["lula"].sum(), "Lula;", sec["flavio"].sum(), "Flávio")
print(tz.group_by("offset_h").len().sort("offset_h"))
