"""Teses: comparecimento impossível, seções com zero votos para o adversário e
comparecimento crescendo em redutos (1º -> 2º turno). 2026 vs 2022 (vs 2018 quando possível)."""
import sys
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
key = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
s26, s22, s18 = (pl.read_parquet(f) for f in sys.argv[1:4])
t1_26, t1_22 = pl.read_parquet(sys.argv[4]), pl.read_parquet(sys.argv[5])

print("== Comparecimento 'impossível' (2º turno, só Brasil) ==")
rows = []
for ano, s in [("2018", s18), ("2022", s22), ("2026", s26)]:
    b = s.filter(pl.col("SG_UF") != "ZZ", pl.col("QT_APTOS") > 0).with_columns(tx=pl.col("QT_COMPARECIMENTO") / pl.col("QT_APTOS"))
    rows.append({"ano": ano, "seções": b.height, "comparec > aptos": int((b["QT_COMPARECIMENTO"] > b["QT_APTOS"]).sum()),
                 "abstenção zero": int((b["QT_ABSTENCOES"] == 0).sum()), "comparec ≥ 98%": int((b["tx"] >= 0.98).sum()),
                 "comparec ≥ 95%": int((b["tx"] >= 0.95).sum()), "comparec médio %": round(100 * b["QT_COMPARECIMENTO"].sum() / b["QT_APTOS"].sum(), 2)})
print(pl.DataFrame(rows))
z = s26.filter(pl.col("SG_UF") != "ZZ", pl.col("QT_ABSTENCOES") == 0)
print("2026, seções com abstenção zero:")
print(z.select("SG_UF", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "QT_APTOS", "QT_COMPARECIMENTO", "lula", "flavio").sort("QT_APTOS", descending=True).head(10))
print("Lula% nessas seções:", round(100 * z["lula"].sum() / (z["lula"].sum() + z["flavio"].sum()), 2), "| aptos medianos:", z["QT_APTOS"].median())

print("\n== Seções com ZERO votos para o adversário do 13 (2º turno) ==")
for ano, s in [("2018", s18), ("2022", s22), ("2026", s26)]:
    zz = s.filter(pl.col("flavio") == 0, pl.col("lula") > 0)
    z13 = s.filter(pl.col("lula") == 0, pl.col("flavio") > 0)
    print(f"{ano}: zero p/ adversário = {zz.height} (mediana {zz['lula'].median()} votos no 13) | zero p/ 13 = {z13.height}")
zz = s26.filter(pl.col("flavio") == 0, pl.col("lula") > 0).join(t1_26.select(*key, "lula1", "flavio1", "outros1"), on=key, how="left")
print("2026, 106 seções sem voto no Flávio — por UF:", zz.group_by("SG_UF").len().sort("len", descending=True).rows())
print("Flávio tinha zero também no 1º turno em", zz.filter(pl.col("flavio1") == 0).height, "delas; votos do Flávio no 1T nelas:",
      zz["flavio1"].sum(), "| Lula 1T:", zz["lula1"].sum(), "→ 2T:", zz["lula"].sum())
print(zz.select("SG_UF", "NM_MUNICIPIO", "NR_SECAO", "QT_APTOS", "lula1", "flavio1", "outros1", "lula", "flavio").sort("lula", descending=True).head(8))

print("\n== Comparecimento do 1º para o 2º turno por reduto (decil de Lula% no 1T) ==")
def red(t1, t2, ano):
    d = t1.join(t2.select(*key, "QT_COMPARECIMENTO", "QT_APTOS", "lula", "flavio"), on=key).filter(pl.col("SG_UF") != "ZZ", pl.col("aptos1") > 0)
    d = d.with_columns(p1=pl.col("lula1") / (pl.col("lula1") + pl.col("flavio1") + pl.col("outros1")))
    d = d.with_columns(decil=pl.col("p1").qcut(10, labels=[f"D{i:02d}" for i in range(1, 11)]))
    return d.group_by("decil").agg(
        lula1_pct=(100 * pl.col("lula1").sum() / (pl.col("lula1") + pl.col("flavio1") + pl.col("outros1")).sum()).round(1),
        comp1=(100 * pl.col("comp1").sum() / pl.col("aptos1").sum()).round(2),
        comp2=(100 * pl.col("QT_COMPARECIMENTO").sum() / pl.col("QT_APTOS").sum()).round(2),
        delta_comp=(pl.col("QT_COMPARECIMENTO").sum() - pl.col("comp1").sum())).with_columns(
        dif_pp=(pl.col("comp2") - pl.col("comp1")).round(2)).sort("decil").rename(
        {c: f"{c}_{ano}" for c in ["lula1_pct", "comp1", "comp2", "delta_comp", "dif_pp"]})
r = red(t1_26, s26, "26").join(red(t1_22, s22, "22"), on="decil")
print(r.select("decil", "lula1_pct_26", "comp1_26", "comp2_26", "dif_pp_26", "delta_comp_26", "lula1_pct_22", "dif_pp_22"))

print("\n== Δcomparecimento 1T→2T por UF (2026), com Lula% 2T ==")
d = t1_26.join(s26.select(*key, "QT_COMPARECIMENTO", "QT_APTOS", "lula", "flavio"), on=key)
u = d.group_by("SG_UF").agg(delta=(pl.col("QT_COMPARECIMENTO") - pl.col("comp1")).sum(),
                            dif_pp=(100 * (pl.col("QT_COMPARECIMENTO").sum() / pl.col("QT_APTOS").sum() - pl.col("comp1").sum() / pl.col("aptos1").sum())).round(2),
                            lula2=(100 * pl.col("lula").sum() / (pl.col("lula") + pl.col("flavio")).sum()).round(1))
print(u.sort("delta", descending=True).head(10)); print(u.sort("delta").head(5))
