"""Tese 'urnas trocadas': urna efetivada (BWeb) x urna esperada da seção (csec) x urnas de contingência da zona (ccont)."""
import sys
from pathlib import Path
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
cesp, bweb, secs = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
key = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO"]
norm = lambda c: pl.col(c).str.replace_all(r"\D", "")  # cargas vêm com e sem pontos
strip0 = [pl.col(c).str.strip_chars_start("0") for c in ["CD_MUNICIPIO", "NR_ZONA"]]

lst = lambda pat: pl.concat([pl.read_csv(f, separator=";", encoding="latin1", infer_schema=False) for f in sorted(cesp.glob(pat))])
esp = lst("csec_*.csv").with_columns(*strip0, pl.col("NR_SECAO").str.strip_chars_start("0"),
                                     urna_esp=pl.col("NR_URNA_ESPERADA").cast(pl.Int64), carga_esp=norm("CD_CARGA_URNA_ESPERADA"))
cont = lst("ccont_*.csv").with_columns(*strip0, urna=pl.col("NR_URNA_ESPERADA").cast(pl.Int64), carga=norm("CD_CARGA_URNA_ESPERADA"))
print(f"esperadas por seção: {esp.height:,} | contingência: {cont.height:,}")

ef = pl.concat([pl.read_csv(f, separator=";", encoding="latin1", infer_schema=False,
                            columns=key + ["NR_URNA_EFETIVADA", "CD_CARGA_1_URNA_EFETIVADA", "CD_CARGA_2_URNA_EFETIVADA"]).unique()
                for f in sorted(bweb.glob("*.csv"))]).with_columns(
    # o código de carga esperado (24 dígitos) = carga 1 (18) + carga 2 (6) do BWeb
    urna=pl.col("NR_URNA_EFETIVADA").cast(pl.Int64), carga=norm("CD_CARGA_1_URNA_EFETIVADA") + norm("CD_CARGA_2_URNA_EFETIVADA"))
d = ef.join(esp.select(*key, "urna_esp", "carga_esp"), on=key, how="left")
d = d.join(cont.select("SG_UF", "CD_MUNICIPIO", "NR_ZONA", "urna", pl.lit(True).alias("eh_cont")).unique(),
           on=["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "urna"], how="left")
d = d.with_columns(situacao=pl.when(pl.col("urna_esp").is_null()).then(pl.lit("seção sem correspondência esperada"))
                   .when(pl.col("urna") == pl.col("urna_esp")).then(
                        # o csec grava a carga como número e perde os zeros à esquerda
                        pl.when(pl.col("carga").str.strip_chars_start("0") == pl.col("carga_esp").str.strip_chars_start("0"))
                        .then(pl.lit("1 urna esperada"))
                        .otherwise(pl.lit("2 urna esperada, carga diferente")))
                   .when(pl.col("eh_cont")).then(pl.lit("3 urna de contingência da zona"))
                   .when(pl.col("urna").is_in(cont["urna"].implode())).then(pl.lit("4 contingência de OUTRA zona"))
                   .when(pl.col("urna").is_in(esp["urna_esp"].implode())).then(pl.lit("5 urna esperada de OUTRA seção"))
                   .otherwise(pl.lit("6 urna fora de qualquer lista")))
s = pl.read_parquet(secs).join(d.select(*key, "situacao", "urna", "urna_esp"), on=key, how="left")
print(s.group_by("situacao").agg(secoes=pl.len(), comparec=pl.col("QT_COMPARECIMENTO").sum(),
                                 pct13=(100 * pl.col("lula").sum() / (pl.col("lula") + pl.col("flavio")).sum()).round(2)).sort("situacao"))
# Lula% das seções substituídas vs seções vizinhas do mesmo município
x = s.with_columns(sub=pl.col("situacao").str.slice(0, 1).is_in(["3", "4", "5", "6"]),
                   val=pl.col("lula") + pl.col("flavio")).filter(pl.col("val") > 0)
x = x.with_columns(dev=pl.col("lula") / pl.col("val") - (pl.col("lula").sum() / pl.col("val").sum()).over("SG_UF", "CD_MUNICIPIO"))
print("Lula% da seção menos a média do município, substituídas vs não:",
      x.group_by("sub").agg(((pl.col("dev") * pl.col("val")).sum() / pl.col("val").sum() * 100).round(2), pl.len()).rows())
outros = s.filter(pl.col("situacao").str.starts_with("6"))
if outros.height:
    print(outros.select("SG_UF", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "urna", "urna_esp", "QT_COMPARECIMENTO", "lula", "flavio").head(15))

estranhas = s.filter(~pl.col("situacao").str.slice(0, 1).is_in(["1", "3", "4"]))
print(f"seções sem explicação pelas listas (cat. 2, 5, 6 e sem correspondência): {estranhas.height}, "
      f"comparecimento {estranhas['QT_COMPARECIMENTO'].sum():,}, saldo Lula {estranhas['lula'].sum() - estranhas['flavio'].sum():+,}")
print("por UF:", estranhas.group_by("SG_UF").len().sort(["len", "SG_UF"], descending=[True, False]).head(8).rows())
