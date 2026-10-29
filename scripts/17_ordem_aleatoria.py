"""Vídeo do 'algoritmo que penaliza' (live de 2022, repostada em 2026): a curva acumulada da apuração
deveria cruzar várias vezes se o envio fosse aleatório? Simula ordens aleatórias de chegada das seções
e conta trocas de liderança; compara com a ordem real (DT_BU_RECEBIDO).

Uso: 17_ordem_aleatoria.py <secoes_2022_2t> <secoes_2026_2t> [n_simulacoes, padrão 200]"""
import sys
import numpy as np
import polars as pl

n_sim = int(sys.argv[3]) if len(sys.argv) > 3 else 200
rng = np.random.default_rng(2022)


def trocas(L, F):
    """Posições (1-based, em nº de seções) em que a liderança acumulada muda de lado."""
    s = np.sign(np.cumsum(L) - np.cumsum(F))
    i = np.nonzero(s)[0]
    return i[1:][s[i][1:] != s[i][:-1]] + 1


for ano, f in [("2022", sys.argv[1]), ("2026", sys.argv[2])]:
    s = pl.read_parquet(f).with_columns(rec=pl.coalesce(
        pl.col("DT_BU_RECEBIDO").str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False),
        pl.col("DT_BU_RECEBIDO").str.to_datetime("%d/%m/%Y %H:%M:%S", strict=False))).sort("rec")
    L, F = s["lula"].to_numpy().astype(float), s["flavio"].to_numpy().astype(float)
    n = len(L)
    print(f"\n################ {ano}: {n:,} seções, 13 final = {100 * L.sum() / (L.sum() + F.sum()):.3f}% ################")
    real = trocas(L, F)
    print(f"ordem real: {len(real)} trocas de liderança; última na seção {real[-1]:,} ({100 * real[-1] / n:.1f}%)")
    n_tr, ult, faixa = [], [], []
    for _ in range(n_sim):
        i = rng.permutation(n)
        t = trocas(L[i], F[i])
        n_tr.append(len(t)); ult.append(t[-1] if len(t) else 0)
        p = np.cumsum(L[i]) / (np.cumsum(L[i]) + np.cumsum(F[i]))
        faixa.append(100 * (p[70_000:110_000].max() - p[70_000:110_000].min()))
    n_tr, ult = np.array(n_tr), np.array(ult)
    print(f"{n_sim} ordens aleatórias: trocas mediana {np.median(n_tr):.0f} (p95 {np.percentile(n_tr, 95):.0f}, máx {n_tr.max()})")
    print(f"  última troca: mediana na seção {np.median(ult):.0f}, p95 {np.percentile(ult, 95):.0f}, máx {ult.max():,} "
          f"({100 * ult.max() / n:.2f}% da apuração)")
    print(f"  amplitude da curva entre as seções 70 mil e 110 mil: mediana {np.median(faixa):.3f} ponto, máx {max(faixa):.3f}")
