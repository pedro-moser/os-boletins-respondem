"""Todas as alegações do post aplicadas a 2018, 2022 e 2026.
Colunas: 'lula' = nº 13 (Haddad em 2018), 'flavio' = adversário (Bolsonaro 17 em 2018, 22 em 2022, Flávio 22 em 2026).
Em 2018 o horário de votação era local (8h-17h em cada fuso), então 'enc_brt' = horário local = relativo ao prazo."""
import sys
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(220); pl.Config.set_thousands_separator(".")
ELEICOES = {  # ano: (arquivo, dia do 2º turno, vencedor)
    "2018": (sys.argv[1], 28, "adv (Bolsonaro)"),
    "2022": (sys.argv[2], 30, "13 (Lula)"),
    "2026": (sys.argv[3], 25, "13 (Lula)"),
}

def pct13(l, a):
    x = 100 * l / (l + a)
    return round(x, 2) if isinstance(x, float) else x.round(2)

def corr_w(df, x, y, w):
    mx, my = df.select((pl.col(c) * pl.col(w)).sum() / pl.col(w).sum() for c in (x, y)).row(0)
    return df.select(((pl.col(w) * (pl.col(x) - mx) * (pl.col(y) - my)).sum()
                      / ((pl.col(w) * (pl.col(x) - mx) ** 2).sum() * (pl.col(w) * (pl.col(y) - my) ** 2).sum()).sqrt())).item()

resumo, grad = [], []
for ano, (arq, dia, venc) in ELEICOES.items():
    a = int(ano)
    s = pl.read_parquet(arq).with_columns(val=pl.col("lula") + pl.col("flavio"))
    br = s.filter(pl.col("SG_UF") != "ZZ")
    t = lambda h, m=0: pl.datetime(a, 10, dia, h, m)
    L, A = s["lula"].sum(), s["flavio"].sum()

    # Alegação 1: corte do post (minuto 17:00 local, exterior incluído)
    antes = s.filter(pl.col("encerramento") < t(17, 1)); depois = s.filter(pl.col("encerramento") >= t(17, 1))
    # Alegação 2: seções tardias
    tard = br.filter(pl.col("enc_brt") >= t(17, 16)); p19 = br.filter(pl.col("enc_brt") >= t(19))
    # Alegação 3: biometria
    v = br.filter(pl.col("val") > 0, pl.col("QT_COMPARECIMENTO") > 0, pl.col("biom_sem") >= 0).with_columns(
        p=pl.col("lula") / pl.col("val"), tb=pl.col("biom_sem") / pl.col("QT_COMPARECIMENTO"))
    dm = v.with_columns((pl.col(c) - pl.col(c).mean().over("SG_UF", "CD_MUNICIPIO")).alias(c + "m") for c in ("p", "tb"))
    # Alegação 4: unanimidade (≥ 90% dos válidos, mesmo critério do post)
    u = s.filter(pl.col("val") > 0).with_columns(p=pl.col("lula") / pl.col("val"))
    u13, uA = (u["p"] >= 0.9).sum(), (u["p"] <= 0.1).sum()

    resumo.append({
        "eleição": ano, "vencedor": venc, "13% nacional": float(pct13(L, A)),
        "corte post: 13% 'até 17h'": float(pct13(antes["lula"].sum(), antes["flavio"].sum())),
        "corte post: 13% 'após 17h'": float(pct13(depois["lula"].sum(), depois["flavio"].sum())),
        "corte post: seções 'até 17h'": antes.height,
        "seções ≥17h16": tard.height, "13% nas ≥17h16": float(pct13(tard["lula"].sum(), tard["flavio"].sum())),
        "seções ≥19h": p19.height,
        "liberados s/ biometria": int(s["biom_sem"].clip(0).sum()),
        "% s/ biometria": round(100 * s["biom_sem"].clip(0).sum() / s["QT_COMPARECIMENTO"].sum(), 2),
        "corr biom×13 bruta": round(corr_w(v, "tb", "p", "val"), 3),
        "corr biom×13 no município": round(corr_w(dm, "tbm", "pm", "val"), 3),
        "seções 100% 13": int((u["p"] == 1).sum()), "seções 100% adv": int((u["p"] == 0).sum()),
        "seções ≥90% 13": int(u13), "seções ≥90% adv": int(uA), "razão ≥90%": f"{u13/uA:.1f}:1",
    })
    g = (br.with_columns(min=pl.when(pl.col("enc_brt") >= t(17, 16)).then(pl.lit("17:16+"))
                         .otherwise(pl.col("enc_brt").dt.strftime("%H:%M")))
           .filter(pl.col("min") >= "17:00")
           .group_by("min").agg(pl.col("lula").sum(), pl.col("flavio").sum(), secoes=pl.len())
           .select("min", pl.col("secoes").alias(f"sec_{ano}"), pct13(pl.col("lula"), pl.col("flavio")).alias(f"13%_{ano}")))
    grad.append(g)

df = pl.DataFrame(resumo)
print(df.transpose(include_header=True, header_name="métrica", column_names="eleição"))
print("\nGradiente: % do nº 13 por minuto de encerramento (relativo ao prazo das 17h; Brasil)")
out = grad[0]
for g in grad[1:]:
    out = out.join(g, on="min", how="full", coalesce=True)
print(out.sort("min").filter(pl.col("min").is_in(["17:00","17:01","17:02","17:03","17:05","17:08","17:10","17:12","17:15","17:16+"])))
