"""Alegações 1 e 2: votação por horário de encerramento da urna."""
import sys
import polars as pl

pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(200); pl.Config.set_thousands_separator(".")
s = pl.read_parquet(sys.argv[1])
br = s.filter(pl.col("SG_UF") != "ZZ")

def resumo(df, by):
    return (df.group_by(by).agg(secoes=pl.len(), comparec=pl.col("QT_COMPARECIMENTO").sum(),
                                lula=pl.col("lula").sum(), flavio=pl.col("flavio").sum())
              .with_columns(pct_lula=(100 * pl.col("lula") / (pl.col("lula") + pl.col("flavio"))).round(2),
                            saldo_lula=pl.col("lula") - pl.col("flavio"))
              .sort(by))

def faixa(col):
    m = pl.col(col).dt.hour().cast(pl.Int32) * 60 + pl.col(col).dt.minute().cast(pl.Int32) + (pl.col(col).dt.second() > 0).cast(pl.Int32) / 100
    return (pl.when(pl.col(col).is_null()).then(pl.lit("0 sem horário"))
            .when(m <= 17 * 60).then(pl.lit("1 até 17h00"))
            .when(m <= 17 * 60 + 15).then(pl.lit("2 17h00:01-17h15:00"))
            .when(m <= 18 * 60 + 59).then(pl.lit("3 17h15:01-18h59:00"))
            .otherwise(pl.lit("4 >= 18h59:01")))  # faixas por segundo; os scripts 03/04 usam minuto cheio

print("== Tipos de urna ==")
print(s.group_by("DS_TIPO_URNA").agg(pl.len(), pl.col("QT_COMPARECIMENTO").sum()))

for col, nome in [("encerramento", "HORÁRIO LOCAL (como está no CSV)"), ("enc_brt", "HORÁRIO DE BRASÍLIA (fuso corrigido)")]:
    print(f"\n== Brasil, por faixa de encerramento — {nome} ==")
    print(resumo(br.with_columns(faixa=faixa(col)), "faixa"))

print("\n== Corte simples no horário local: até 17h00:00 vs depois ==")
t = br.with_columns(antes=pl.col("encerramento") <= pl.datetime(2026, 10, 25, 17, 0, 0))
print(resumo(t, "antes"))
print("\n== Mesmo corte, em minutos inteiros (17:00:59 conta como 17h00) ==")
t = br.with_columns(antes=pl.col("encerramento") < pl.datetime(2026, 10, 25, 17, 1, 0))
print(resumo(t, "antes"))

print("\n== Quem está no grupo 'até 17h' em horário local? (por UF) ==")
t = br.filter(pl.col("encerramento") <= pl.datetime(2026, 10, 25, 17, 0, 0))
print(resumo(t, "SG_UF").sort("comparec", descending=True).head(15))

print("\n== Distribuição do encerramento (Brasília), minuto a minuto, 16h55-17h30 ==")
d = (br.filter(pl.col("enc_brt").is_between(pl.datetime(2026,10,25,16,55), pl.datetime(2026,10,25,17,30)))
       .with_columns(min=pl.col("enc_brt").dt.strftime("%H:%M")))
print(resumo(d, "min").select("min", "secoes", "comparec", "pct_lula"))

print("\n== Cauda: seções encerradas após 17h30 (Brasília), por UF ==")
tail = br.filter(pl.col("enc_brt") > pl.datetime(2026, 10, 25, 17, 30))
print(resumo(tail, "SG_UF").sort("secoes", descending=True))
print("máximo enc_brt:", br["enc_brt"].max(), "| máximo local:", br["encerramento"].max())
print("\n== Grupo 'até 17h00' do post (minuto 17:00 local) — composição ==")
g = br.with_columns(post_antes=pl.col("encerramento") < pl.datetime(2026, 10, 25, 17, 1),
                    oeste=pl.col("offset_h") != 0)
print(resumo(g, ["post_antes", "oeste"]))
print("\n== Mesmo corte incluindo exterior (ZZ) ==")
print(resumo(s.with_columns(post_antes=pl.col("encerramento") < pl.datetime(2026, 10, 25, 17, 1)), "post_antes")
      .with_columns(pct_flavio=(100 - pl.col("pct_lula")).round(2)))
