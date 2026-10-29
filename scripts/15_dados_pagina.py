"""Séries para os gráficos da página: gradiente por minuto (2018/2022/2026) e curva da apuração (2022/2026)."""
import json, sys
import polars as pl

out = {}
anos = {"2018": (sys.argv[1], 28), "2022": (sys.argv[2], 30), "2026": (sys.argv[3], 25)}
out["gradiente"] = {}
for ano, (f, dia) in anos.items():
    s = pl.read_parquet(f).filter(pl.col("SG_UF") != "ZZ")
    g = (s.filter(pl.col("enc_brt").is_between(pl.datetime(int(ano), 10, dia, 17, 0), pl.datetime(int(ano), 10, dia, 17, 15, 59)))
          .with_columns(m=pl.col("enc_brt").dt.minute())
          .group_by("m").agg(n=pl.len(), p=(100 * pl.col("lula").sum() / (pl.col("lula") + pl.col("flavio")).sum()).round(2)).sort("m"))
    out["gradiente"][ano] = g.rows()
out["apuracao"] = {}
for ano in ["2022", "2026"]:
    f, dia = anos[ano]
    s = pl.read_parquet(f).with_columns(rec=pl.coalesce(
        pl.col("DT_BU_RECEBIDO").str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False),
        pl.col("DT_BU_RECEBIDO").str.to_datetime("%d/%m/%Y %H:%M:%S", strict=False))).sort(["rec", "SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"])  # desempate fixo: muitos BUs chegam no mesmo segundo
    s = s.with_columns(L=pl.col("lula").cum_sum(), F=pl.col("flavio").cum_sum(), i=pl.int_range(1, pl.len() + 1))
    s = s.with_columns(pct=100 * pl.col("i") / pl.len(), p=100 * pl.col("L") / (pl.col("L") + pl.col("F")))
    pts = []
    for q in [x / 2 for x in range(2, 201)]:
        r = s.filter(pl.col("pct") >= q).head(1).row(0, named=True)
        pts.append([q, round(r["p"], 3), r["rec"].strftime("%H:%M")])
    lid = s.with_columns(l=pl.col("L") > pl.col("F")).filter(pl.col("l") != pl.col("l").shift(1)).tail(1).row(0, named=True)
    out["apuracao"][ano] = {"pts": pts, "virada_pct": round(lid["pct"], 2), "virada_hora": lid["rec"].strftime("%H:%M")}
    print(ano, out["apuracao"][ano]["virada_pct"], out["apuracao"][ano]["virada_hora"], pts[0], pts[-1])
json.dump(out, open(sys.argv[4], "w"))
print({k: v[:3] for k, v in out["gradiente"].items()})
