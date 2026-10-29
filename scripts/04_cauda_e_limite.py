"""Alegação 2 (seções tardias), limite aritmético e composição por UF dos minutos tardios."""
import sys
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
s26, s22 = pl.read_parquet(sys.argv[1]), pl.read_parquet(sys.argv[2])
b26, b22 = (x.filter(pl.col("SG_UF") != "ZZ") for x in (s26, s22))

def agg(df, by):
    return (df.group_by(by).agg(secoes=pl.len(), comparec=pl.col("QT_COMPARECIMENTO").sum(),
                                lula=pl.col("lula").sum(), n22=pl.col("flavio").sum())
              .with_columns(pct_lula=(100 * pl.col("lula") / (pl.col("lula") + pl.col("n22"))).round(2),
                            saldo_lula=pl.col("lula") - pl.col("n22")))

c19 = pl.datetime(2026, 10, 25, 19, 0)
print("== 2026: seções encerradas >= 19h00 (Brasília) por UF ==")
print(agg(b26.filter(pl.col("enc_brt") >= c19), "SG_UF").sort("secoes", descending=True).head(12))

print("\n== 2026: encerramento depois das 19h30 (Brasília) ==")
late = b26.filter(pl.col("enc_brt") > pl.datetime(2026, 10, 25, 19, 30))
print(agg(late.with_columns(h=pl.col("enc_brt").dt.hour()), "h").sort("h"))
print(late.sort("enc_brt", descending=True).select("SG_UF", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "QT_APTOS",
      "QT_COMPARECIMENTO", "lula", "flavio", "abertura", "enc_brt", "DS_SECOES_AGREGADAS").head(8))

print("\n== Limite aritmético (2026) ==")
margem = s26["lula"].sum() - s26["flavio"].sum()
tard = b26.filter(pl.col("enc_brt") >= pl.datetime(2026, 10, 25, 17, 16))
L, F, C = tard["lula"].sum(), tard["flavio"].sum(), tard["QT_COMPARECIMENTO"].sum()
print(f"margem oficial: {margem:,}")
print(f"seções >=17h16: {tard.height:,}  comparecimento {C:,}  Lula {L:,}  Flávio {F:,}  saldo {L-F:,}")
print(f"(a) anular essas seções inteiras -> margem {margem-(L-F):,}")
print(f"(b) dar TODOS os votos de Lula delas ao Flávio -> margem {margem-2*L:,}")
print(f"(c) anular os votos de Lula delas e manter os do Flávio -> margem {margem-L:,}")

print("\n== Composição por UF das seções que fecharam 17h05-17h15 (Brasília): 2026 vs 2022 ==")
def comp(b, ano, d):
    x = b.filter(pl.col("enc_brt").is_between(pl.datetime(ano, 10, d, 17, 5), pl.datetime(ano, 10, d, 17, 15, 59)))
    return agg(x, "SG_UF").with_columns(share=(100 * pl.col("secoes") / pl.col("secoes").sum()).round(1)).select("SG_UF", "share", "pct_lula")
c = comp(b26, 2026, 25).rename({"share": "share26", "pct_lula": "lula26"}).join(
    comp(b22, 2022, 30).rename({"share": "share22", "pct_lula": "lula22"}), on="SG_UF", how="full", coalesce=True)
print(c.sort("share26", descending=True).head(10))

print("\n== Gradiente DENTRO de cada UF (2026 vs 2022): Lula% em seções que fecham 17h00 vs 17h05+ (até 17h59) ==")
def grad(b, ano, d):
    x = b.filter(pl.col("enc_brt") < pl.datetime(ano, 10, d, 18, 0)).with_columns(
        tarde=pl.col("enc_brt") >= pl.datetime(ano, 10, d, 17, 5))
    a = agg(x, ["SG_UF", "tarde"]).pivot(on="tarde", index="SG_UF", values="pct_lula")
    return a.select("SG_UF", (pl.col("true") - pl.col("false")).round(2).alias(f"dif_{ano}"))
print(grad(b26, 2026, 25).join(grad(b22, 2022, 30), on="SG_UF").sort("SG_UF"))
