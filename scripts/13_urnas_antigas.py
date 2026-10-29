"""Tese 'urnas antigas votaram mais no Lula' (relatório do PL, 2022): 2026 e 2022.
Geração da urna inferida pela faixa do nº de série (calibrada no AC 2026: UE2020 ~2,01-2,10 mi; UE2022 ~2,25-2,47 mi)."""
import sys
from pathlib import Path
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
key = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]

def faixa(s):
    return (pl.when(s < 1_500_000).then(pl.lit("a) <1,5 mi (≈UE2009-2011)"))
            .when(s < 2_000_000).then(pl.lit("b) 1,5-2,0 mi (≈UE2013-2015)"))
            .when(s < 2_200_000).then(pl.lit("c) 2,0-2,2 mi (≈UE2020)"))
            .otherwise(pl.lit("d) ≥2,2 mi (≈UE2022)")))

for ano, sec, csvd in [("2026", sys.argv[1], sys.argv[2]), ("2022", sys.argv[3], sys.argv[4])]:
    ser = pl.concat([pl.read_csv(f, separator=";", encoding="latin1", infer_schema=False, columns=key + ["NR_URNA_EFETIVADA"]).unique()
                     for f in sorted(Path(csvd).glob("*.csv"))]).with_columns(serie=pl.col("NR_URNA_EFETIVADA").cast(pl.Int64))
    s = pl.read_parquet(sec).join(ser.select(*key, "serie"), on=key).filter(pl.col("SG_UF") != "ZZ", pl.col("serie") > 0)
    s = s.with_columns(faixa=faixa(pl.col("serie")), val=pl.col("lula") + pl.col("flavio"),
                       antiga=pl.col("serie") < 2_000_000).filter(pl.col("val") > 0)
    s = s.with_columns(p=pl.col("lula") / pl.col("val"))
    print(f"\n######## {ano} ########")
    print(s.group_by("faixa").agg(secoes=pl.len(), pct13=(100 * pl.col("lula").sum() / pl.col("val").sum()).round(2),
                                  pct_NE=(100 * pl.col("SG_UF").is_in(["BA","PE","CE","MA","PI","PB","RN","AL","SE"]).mean()).round(1))
           .sort("faixa"))
    # diferença antiga - nova: bruta, dentro do município e dentro do local de votação (ponderada por votos válidos)
    for nivel, grp in [("bruta", None), ("dentro do município", ["SG_UF", "CD_MUNICIPIO"]),
                       ("dentro do local de votação", ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_LOCAL_VOTACAO"])]:
        x = s
        if grp:
            # só grupos que têm urna antiga E nova; compara cada seção com a média do seu grupo
            x = x.filter(pl.col("antiga").any().over(grp) & (~pl.col("antiga")).any().over(grp))
            x = x.with_columns(p=pl.col("p") - (pl.col("lula").sum() / pl.col("val").sum()).over(grp))
        r = x.group_by("antiga").agg(m=(pl.col("p") * pl.col("val")).sum() / pl.col("val").sum(), n=pl.len())
        d = dict(zip(r["antiga"], r["m"])); n = dict(zip(r["antiga"], r["n"]))
        print(f"antiga − nova, {nivel:28s}: {100*(d[True]-d[False]):+.2f} p.p.  (seções: {n[True]:,} antigas, {n[False]:,} novas)")
