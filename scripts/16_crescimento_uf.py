"""'Lula cresceu X% em estado bolsonarista': crescimento do 1º para o 2º turno por UF, 2026 e o espelho de 2022.
Compara três métricas: crescimento percentual (Δ/base, inflado por base pequena), votos absolutos e
fatia do estoque (terceiros + queda de brancos/nulos + Δcomparecimento) que ficou com cada candidato.
Seções pareadas entre os turnos, como em 08_turnos.py; exterior (ZZ) fora.

Uso: 16_crescimento_uf.py <secoes_1t> <secoes_2t> <secoes_2022_1t> <secoes_2022_2t>"""
import sys
import numpy as np
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
key = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
casos = {"2026": (sys.argv[1], sys.argv[2], "Flávio"), "2022": (sys.argv[3], sys.argv[4], "Bolsonaro")}

for ano, (f1, f2, adv) in casos.items():
    t1 = pl.read_parquet(f1)
    t2 = pl.read_parquet(f2).select(*key, "lula", "flavio", "brancos", "nulos", "QT_COMPARECIMENTO")
    d = (t1.join(t2, on=key, how="inner").filter(pl.col("SG_UF") != "ZZ")
           .group_by("SG_UF").agg(pl.col("lula1", "flavio1", "outros1", "brancos1", "nulos1", "comp1",
                                         "lula", "flavio", "brancos", "nulos", "QT_COMPARECIMENTO").sum()))
    d = d.with_columns(
        dl=pl.col("lula") - pl.col("lula1"), df=pl.col("flavio") - pl.col("flavio1"),
        estoque=pl.col("outros1") + (pl.col("brancos1") + pl.col("nulos1") - pl.col("brancos") - pl.col("nulos"))
                + (pl.col("QT_COMPARECIMENTO") - pl.col("comp1"))).with_columns(
        lula1_pct=(100 * pl.col("lula1") / (pl.col("lula1") + pl.col("flavio1") + pl.col("outros1"))).round(1),
        terc_pct=(100 * pl.col("outros1") / (pl.col("lula1") + pl.col("flavio1") + pl.col("outros1"))).round(1),
        cresc_13=(100 * pl.col("dl") / pl.col("lula1")).round(1),
        cresc_adv=(100 * pl.col("df") / pl.col("flavio1")).round(1),
        dl_mil=(pl.col("dl") / 1e3).round(0), df_mil=(pl.col("df") / 1e3).round(0),
        # A fatia só tem leitura direta quando os dois cresceram; senão o estoque é pequeno ou negativo e a razão explode.
        fatia_13=pl.when((pl.col("dl") >= 0) & (pl.col("df") >= 0)).then((100 * pl.col("dl") / pl.col("estoque")).round(1)),
    ).sort("lula1_pct")
    tot = d.select(pl.col("dl", "estoque").sum()).row(0, named=True)
    print(f"\n################ {ano} (13 × {adv}) ################")
    print(f"fatia nacional do estoque para o 13: {100 * tot['dl'] / tot['estoque']:.1f}%")
    print(d.select("SG_UF", "lula1_pct", "terc_pct", "cresc_13", "cresc_adv", "dl_mil", "df_mil", "fatia_13"))
    for c in ["cresc_13", "cresc_adv", "fatia_13", "terc_pct"]:
        x = d.drop_nulls(c)
        print(f"r(lula1_pct, {c}) = {np.corrcoef(x['lula1_pct'], x[c])[0, 1]:+.2f}  (n = {x.height})")
