"""Extrai (seção, nº de série da urna, modelo) dos logs do arquivo do AC, para calibrar série -> modelo."""
import io, re, sys, zipfile
import polars as pl

zpath, out = sys.argv[1], sys.argv[2]
pat_mod = re.compile(rb"Identifica\xe7\xe3o do Modelo de Urna: (UE\d+)")
nome = re.compile(r"o\d{5}([a-z]{2})(\d{5})(\d{4})(\d{4})-log\.jez")
rows = []
with zipfile.ZipFile(zpath) as z:
    for n in z.namelist():
        m = nome.match(n)
        if not m:
            continue
        with zipfile.ZipFile(io.BytesIO(z.read(n))) as inner:
            txt = inner.read(inner.namelist()[0])
        # o modelo da urna que votou no dia 25/10 (última identificação no log)
        mods = pat_mod.findall(txt)
        serie = None
        for line in txt.splitlines()[::-1]:
            if line.startswith(b"25/10/2026") and b"\tVOTA\t" in line:
                serie = line.split(b"\t")[2].decode(); break
        rows.append({"SG_UF": m[1].upper(), "CD_MUNICIPIO": m[2].lstrip("0"), "NR_ZONA": m[3].lstrip("0"),
                     "NR_SECAO": m[4].lstrip("0"), "modelo": mods[-1].decode() if mods else None, "serie_log": serie})
df = pl.DataFrame(rows); df.write_parquet(out)
print(df.group_by("modelo").len().sort("modelo"))
