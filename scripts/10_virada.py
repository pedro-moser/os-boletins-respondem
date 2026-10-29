"""Tese 'a virada às 20h24': reconstrói a totalização pela ordem de chegada dos BUs (DT_BU_RECEBIDO)."""
import sys
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
s = pl.read_parquet(sys.argv[1]).with_columns(rec=pl.col("DT_BU_RECEBIDO").str.to_datetime("%Y-%m-%d %H:%M:%S"))
NE = ["BA", "PE", "CE", "MA", "PI", "PB", "RN", "AL", "SE"]
s = s.sort("rec").with_columns(
    L=pl.col("lula").cum_sum(), F=pl.col("flavio").cum_sum(), n=pl.int_range(1, pl.len() + 1),
    ne=pl.col("SG_UF").is_in(NE))
s = s.with_columns(pct_urnas=(100 * pl.col("n") / pl.len()).round(2), lider=pl.when(pl.col("L") > pl.col("F")).then(pl.lit("Lula")).otherwise(pl.lit("Flávio")))
trocas = s.filter(pl.col("lider") != pl.col("lider").shift(1))
print("Trocas de liderança na totalização:")
print(trocas.select("rec", "pct_urnas", "L", "F", "lider"))
print("\nAndamento a cada 15 min, e participação do Nordeste nos BUs que chegaram em cada janela:")
j = s.group_by_dynamic("rec", every="15m").agg(
    bus=pl.len(), ne_pct=(100 * pl.col("ne").mean()).round(1),
    lula_janela=(100 * pl.col("lula").sum() / (pl.col("lula") + pl.col("flavio")).sum()).round(1),
    pct_urnas=pl.col("pct_urnas").last(), L=pl.col("L").last(), F=pl.col("F").last())
print(j.with_columns(lula_acum=(100 * pl.col("L") / (pl.col("L") + pl.col("F"))).round(2)).drop("L", "F"))
print("\nMediana do horário de chegada do BU por região:",
      s.group_by("ne").agg(pl.col("rec").median()).rows())
print("Mediana por UF (5 mais tardias):",
      s.group_by("SG_UF").agg(pl.col("rec").median()).sort("rec", descending=True).head(5).rows())
