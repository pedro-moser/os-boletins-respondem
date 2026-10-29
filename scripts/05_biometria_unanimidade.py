"""Alegações 3 (liberação sem biometria) e 4 (seções quase unânimes): 2026 vs 2022."""
import sys
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
anos = {"2026": pl.read_parquet(sys.argv[1]), "2022": pl.read_parquet(sys.argv[2])}

def corr_w(df, x, y, w):
    m = df.select(mx=(pl.col(x) * pl.col(w)).sum() / pl.col(w).sum(), my=(pl.col(y) * pl.col(w)).sum() / pl.col(w).sum()).row(0)
    return df.select(((pl.col(w) * (pl.col(x) - m[0]) * (pl.col(y) - m[1])).sum()
                      / ((pl.col(w) * (pl.col(x) - m[0]) ** 2).sum() * (pl.col(w) * (pl.col(y) - m[1]) ** 2).sum()).sqrt())).item()

for ano, s in anos.items():
    s = s.with_columns(validos=pl.col("lula") + pl.col("flavio"))
    s = s.with_columns(pct_lula=pl.col("lula") / pl.col("validos"),
                       taxa_bio=pl.col("biom_sem") / pl.col("QT_COMPARECIMENTO"))
    print(f"\n######## {ano} ########")
    print(f"biom_sem nulo/negativo: {s.filter(pl.col('biom_sem').is_null() | (pl.col('biom_sem') < 0)).height}")
    tot = s["biom_sem"].clip(0).sum(); comp = s["QT_COMPARECIMENTO"].sum()
    print(f"liberados sem biometria: {tot:,} = {100*tot/comp:.2f}% do comparecimento ({comp:,})")
    v = s.filter(pl.col("validos") > 0, pl.col("QT_COMPARECIMENTO") > 0, pl.col("biom_sem") >= 0)
    r = corr_w(v, "taxa_bio", "pct_lula", "validos")
    # mesma correlação, mas dentro de cada município (remove o efeito região/estado)
    dm = v.with_columns((pl.col(c) - pl.col(c).mean().over("SG_UF", "CD_MUNICIPIO")).alias(c + "_dm") for c in ["taxa_bio", "pct_lula"])
    r_mun = corr_w(dm, "taxa_bio_dm", "pct_lula_dm", "validos")
    dl = v.with_columns((pl.col(c) - pl.col(c).mean().over("SG_UF", "CD_MUNICIPIO", "NR_LOCAL_VOTACAO")).alias(c + "_dl") for c in ["taxa_bio", "pct_lula"])
    r_loc = corr_w(dl, "taxa_bio_dl", "pct_lula_dl", "validos")
    print(f"corr(taxa sem biometria, Lula%) ponderada: bruta {r:.3f} | dentro do município {r_mun:.3f} | dentro do mesmo local de votação {r_loc:.3f}")
    print("Lula% por faixa de taxa de liberação sem biometria:")
    print(v.with_columns(faixa=pl.col("taxa_bio").cut([0.02, 0.05, 0.1, 0.2, 0.3, 0.5], left_closed=True))
           .group_by("faixa").agg(secoes=pl.len(), lula=pl.col("lula").sum(), n22=pl.col("flavio").sum(),
                                   pct_NE=(100 * pl.col("SG_UF").is_in(["BA","PE","CE","MA","PI","PB","RN","AL","SE"]).mean()).round(1))
           .with_columns(pct_lula=(100 * pl.col("lula") / (pl.col("lula") + pl.col("n22"))).round(2)).sort("faixa"))

    print("Seções quase unânimes (válidos >= 1):")
    q = v.select(
        lula100=(pl.col("pct_lula") == 1).sum(), n22_100=(pl.col("pct_lula") == 0).sum(),
        lula90=(pl.col("pct_lula") > 0.9).sum(), n22_90=(pl.col("pct_lula") < 0.1).sum(),
        lula80=(pl.col("pct_lula") > 0.8).sum(), n22_80=(pl.col("pct_lula") < 0.2).sum())
    print(q)
    print("mediana de votos válidos nas seções 100%:",
          v.filter((pl.col("pct_lula") == 1) | (pl.col("pct_lula") == 0))["validos"].median())
    print("UF das seções >90% Lula (top 6):",
          v.filter(pl.col("pct_lula") > 0.9).group_by("SG_UF").len().sort("len", descending=True).head(6).rows())
    print("UF das seções >90% n22 (top 6):",
          v.filter(pl.col("pct_lula") < 0.1).group_by("SG_UF").len().sort("len", descending=True).head(6).rows())
