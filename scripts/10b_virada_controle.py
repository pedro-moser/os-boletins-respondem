"""Virada: 2026 vs 2022 e efeito de composição dentro de cada UF (capital x interior)."""
import sys
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
CAP = {"AC": "RIO BRANCO", "AL": "MACEIÓ", "AM": "MANAUS", "AP": "MACAPÁ", "BA": "SALVADOR", "CE": "FORTALEZA",
       "DF": "BRASÍLIA", "ES": "VITÓRIA", "GO": "GOIÂNIA", "MA": "SÃO LUÍS", "MG": "BELO HORIZONTE", "MS": "CAMPO GRANDE",
       "MT": "CUIABÁ", "PA": "BELÉM", "PB": "JOÃO PESSOA", "PE": "RECIFE", "PI": "TERESINA", "PR": "CURITIBA",
       "RJ": "RIO DE JANEIRO", "RN": "NATAL", "RO": "PORTO VELHO", "RR": "BOA VISTA", "RS": "PORTO ALEGRE",
       "SC": "FLORIANÓPOLIS", "SE": "ARACAJU", "SP": "SÃO PAULO", "TO": "PALMAS"}
cap = pl.DataFrame({"SG_UF": list(CAP), "NM_MUNICIPIO": list(CAP.values()), "capital": [True] * len(CAP)})
for ano, f in [("2026", sys.argv[1]), ("2022", sys.argv[2])]:
    s = pl.read_parquet(f).filter(pl.col("SG_UF") != "ZZ").with_columns(
        rec=pl.coalesce(pl.col("DT_BU_RECEBIDO").str.to_datetime("%Y-%m-%d %H:%M:%S", strict=False),
                        pl.col("DT_BU_RECEBIDO").str.to_datetime("%d/%m/%Y %H:%M:%S", strict=False)))
    s = s.join(cap, on=["SG_UF", "NM_MUNICIPIO"], how="left").with_columns(pl.col("capital").fill_null(False))
    s = s.sort("rec").with_columns(L=pl.col("lula").cum_sum(), F=pl.col("flavio").cum_sum(),
                                   pct=(100 * pl.int_range(1, pl.len() + 1) / pl.len()).round(2))
    s = s.with_columns(lider=pl.when(pl.col("L") > pl.col("F")).then(pl.lit("13")).otherwise(pl.lit("22")))
    ult = s.filter(pl.col("lider") != pl.col("lider").shift(1)).tail(1)
    print(f"\n##### {ano}: última troca de liderança em {ult['rec'][0]} com {ult['pct'][0]}% dos BUs; vencedor final {s['lider'][-1]}")
    # quartil de chegada DENTRO de cada UF
    s = s.with_columns(q=(pl.col("rec").rank("ordinal").over("SG_UF") * 4 / pl.len().over("SG_UF")).ceil().cast(pl.Int8))
    print("% do 13 por quartil de chegada dentro da própria UF (Q1 = primeiros 25% da UF):")
    print(s.group_by("q").agg(pct13=(100 * pl.col("lula").sum() / (pl.col("lula") + pl.col("flavio")).sum()).round(2),
                              capital_pct=(100 * pl.col("capital").mean()).round(1),
                              eleitores_med=pl.col("QT_APTOS").median()).sort("q"))
    print("capital x interior, % do 13 e mediana de chegada:",
          s.group_by("capital").agg((100 * pl.col("lula").sum() / (pl.col("lula") + pl.col("flavio")).sum()).round(2), pl.col("rec").median()).rows())
