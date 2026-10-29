"""'Matematicamente impossível': transferências do 1º para o 2º turno, 2026 vs 2022.
Regressão ecológica de Goodman por UF (sem intercepto): cada voto/abstenção do 2º turno é
modelado como combinação dos grupos do 1º turno na mesma seção; os coeficientes estimam as
taxas de transferência. Agregado nacional = média dos coeficientes por UF ponderada pelo tamanho do grupo."""
import sys
import numpy as np
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
key = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
casos = {"2026": (sys.argv[1], sys.argv[2], "Flávio"), "2022": (sys.argv[3], sys.argv[4], "Bolsonaro")}

for ano, (f1, f2, adv) in casos.items():
    t1 = pl.read_parquet(f1)
    t2 = pl.read_parquet(f2).select(*key, "lula", "flavio", "brancos", "nulos", "QT_APTOS", "QT_COMPARECIMENTO")
    d = t1.join(t2, on=key, how="inner").filter(pl.col("SG_UF") != "ZZ")
    cand = [c for c in t1.columns if c.startswith("c") and c[1:].isdigit()]
    d = d.with_columns(
        resto1=pl.col("outros1") - pl.sum_horizontal(cand), bn1=pl.col("brancos1") + pl.col("nulos1"),
        abst1=pl.col("aptos1") - pl.col("comp1"), bn2=pl.col("brancos") + pl.col("nulos"),
        abst2=pl.col("QT_APTOS") - pl.col("QT_COMPARECIMENTO"))
    print(f"\n################ {ano} (13 × {adv}) — {d.height:,} seções pareadas de {t1.height:,} ################")
    tot = d.select(pl.col("lula1", "flavio1", "outros1", "bn1", "comp1", "lula", "flavio", "bn2", "QT_COMPARECIMENTO").sum()).row(0, named=True)
    pool = tot["outros1"] + (tot["bn1"] - tot["bn2"]) + (tot["QT_COMPARECIMENTO"] - tot["comp1"])
    dl, dfv = tot["lula"] - tot["lula1"], tot["flavio"] - tot["flavio1"]
    print(f"Δ13 = {dl:+,} | Δ{adv} = {dfv:+,} | estoque (terceiros {tot['outros1']:,} + queda B/N {tot['bn1']-tot['bn2']:,} "
          f"+ Δcomparecimento {tot['QT_COMPARECIMENTO']-tot['comp1']:,}) = {pool:,}")
    print(f"fatia do estoque: 13 = {100*dl/pool:.1f}% | {adv} = {100*dfv/pool:.1f}%")

    # Regressão ecológica por UF
    X_cols = ["lula1", "flavio1", *cand, "resto1", "bn1", "abst1"]
    Y_cols = ["lula", "flavio", "bn2", "abst2"]
    acc = {x: np.zeros(len(Y_cols)) for x in X_cols}; peso = {x: 0.0 for x in X_cols}
    for (uf,), g in d.group_by("SG_UF"):
        X = g.select(X_cols).to_numpy().astype(float); Y = g.select(Y_cols).to_numpy().astype(float)
        B, *_ = np.linalg.lstsq(X, Y, rcond=None)
        for i, x in enumerate(X_cols):
            w = X[:, i].sum(); acc[x] += B[i] * w; peso[x] += w
    nomes = dict(zip(t1.columns, t1.columns))
    print("Taxas de transferência estimadas (linha = grupo no 1º turno; colunas = destino no 2º):")
    rows = [{"grupo 1º turno": x, "tamanho": int(peso[x]), **{f"→{y}": round(float(acc[x][j] / peso[x]), 3) for j, y in enumerate(Y_cols)}}
            for x in X_cols]
    print(pl.DataFrame(rows))

    # Limite rígido por seção: ganho maior que tudo o que estava disponível exige troca direta 13 <-> adv
    lim = pl.col("outros1") + pl.col("bn1") + pl.col("abst1")
    v = d.with_columns(exc13=(pl.col("lula") - pl.col("lula1")) - lim, excA=(pl.col("flavio") - pl.col("flavio1")) - lim)
    for c, n in [("exc13", "13"), ("excA", adv)]:
        x = v.filter(pl.col(c) > 0)
        print(f"seções em que o ganho do {n} excede terceiros+B/N+abstenção do 1º turno: {x.height:,} "
              f"({100*x.height/d.height:.2f}%), excesso total {x[c].sum():,} votos")
