"""Distribuição nacional dos números de série das urnas efetivadas (2T 2026) e comparação com 2022."""
import sys
from pathlib import Path
import polars as pl

pl.Config.set_tbl_rows(60); pl.Config.set_thousands_separator(".")
for ano, d in [("2026", sys.argv[1]), ("2022", sys.argv[2])]:
    u = pl.concat([pl.read_csv(f, separator=";", encoding="latin1", infer_schema=False,
                               columns=["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "NR_URNA_EFETIVADA"]).unique()
                   for f in sorted(Path(d).glob("*.csv"))]).with_columns(serie=pl.col("NR_URNA_EFETIVADA").cast(pl.Int64))
    print(f"\n## {ano}: {u.height:,} seções; série min {u['serie'].min():,} max {u['serie'].max():,}")
    print(u.with_columns(faixa=(pl.col("serie") // 100_000) * 100_000).group_by("faixa").len().sort("faixa"))
