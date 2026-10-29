"""Corte do post e gradiente por minuto: 2026 (com prorrogação) vs 2022 (sem prorrogação).
Na base de 2022 a coluna 'flavio' contém os votos do nº 22 (Bolsonaro)."""
import sys
import polars as pl

pl.Config.set_tbl_rows(60); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
anos = {"2026": pl.read_parquet(sys.argv[1]), "2022": pl.read_parquet(sys.argv[2])}

def agg(df, by):
    return (df.group_by(by).agg(secoes=pl.len(), comparec=pl.col("QT_COMPARECIMENTO").sum(),
                                lula=pl.col("lula").sum(), n22=pl.col("flavio").sum())
              .with_columns(pct_lula=(100 * pl.col("lula") / (pl.col("lula") + pl.col("n22"))).round(2),
                            saldo_lula=pl.col("lula") - pl.col("n22")).sort(by))

for ano, s in anos.items():
    d = s.with_columns(ano=pl.lit(ano))
    print(f"\n===== {ano}: corte do post (encerramento LOCAL < 17:01, exterior incluído) =====")
    print(agg(d.with_columns(minuto_17h00_local=pl.col("encerramento") < pl.datetime(int(ano), 10, 25 if ano == "2026" else 30, 17, 1)),
              "minuto_17h00_local").with_columns(pct_n22=(100 - pl.col("pct_lula")).round(2)))

print("\n===== Gradiente por minuto de encerramento (Brasília, só Brasil) — 2026 vs 2022 =====")
rows = []
for ano, s in anos.items():
    b = s.filter(pl.col("SG_UF") != "ZZ").with_columns(
        min=pl.when(pl.col("enc_brt").dt.hour() >= 19).then(pl.lit("19:00+"))
             .when(pl.col("enc_brt").dt.hour() >= 18).then(pl.lit("18:00-18:59"))
             .when((pl.col("enc_brt").dt.hour() == 17) & (pl.col("enc_brt").dt.minute() >= 16)).then(pl.lit("17:16-17:59"))
             .otherwise(pl.col("enc_brt").dt.strftime("%H:%M")))
    rows.append(agg(b, "min").select("min", pl.col("secoes").alias(f"sec_{ano}"), pl.col("comparec").alias(f"comp_{ano}"), pl.col("pct_lula").alias(f"lula_{ano}")))
print(rows[0].join(rows[1], on="min", how="full", coalesce=True).sort("min"))

print("\n===== Lula% nacional de referência =====")
for ano, s in anos.items():
    print(ano, round(100 * s["lula"].sum() / (s["lula"].sum() + s["flavio"].sum()), 2))
