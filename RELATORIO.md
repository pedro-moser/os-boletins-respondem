# Checagem do "Relatório Pericial Independente — Eleições 2026"

Post do Instagram (@joeymannarinous, 28/10/2026), prints em `prints-tese-golpista/`.
Análise feita em 28/10/2026 com os Boletins de Urna (BWeb) oficiais do TSE.

## Dados

- **2º turno 2026:** `bweb_2t_{UF}_261020260742.zip`, 27 UFs + exterior (ZZ), baixados do
  [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna).
  SHA-512 conferido nos 28 arquivos.
- **Controle: 2º turno 2022** (Lula × Bolsonaro, **sem prorrogação de horário**), mesmo formato, SHA-512 conferido.
- Totais reconstruídos batem com o oficial: 2026 = 499.205 seções, Lula 64.256.232, Flávio 59.826.041
  (margem 4.430.191); 2022 = Lula 60.345.999, Bolsonaro 58.206.354.
- `DT_ABERTURA`/`DT_ENCERRAMENTO` estão em **horário local**. O fuso de cada município foi inferido
  pela hora modal de abertura (todas as urnas abrem às 8h de Brasília). As seções do exterior (ZZ)
  seguem o horário local de cada país e ficaram fora das análises de horário (27 delas não têm
  horário de encerramento no arquivo).

Scripts em `scripts/` (rodar com `uv run --with polars python -I scripts/NN_*.py ...`):
`01_build.py` (tabela por seção), `02_horario.py`, `03_controle.py`, `04_cauda_e_limite.py`,
`05_biometria_unanimidade.py`.

## Veredito curto

Os números do post estão **em boa parte corretos como contagens**: deu para reproduzir o 52,39%, os
8.632.488, o 106 × 4 e a tabela por estado. **As conclusões é que não se sustentam.** Cada "anomalia"
aparece com a mesma forma, ou mais forte, no 2º turno de 2022, que não teve prorrogação, ou então se
explica por fuso horário e geografia. A prorrogação existiu, mas mesmo no cenário mais hostil ela não
consegue mudar o resultado.

## 1. "Até as 17h Flávio venceu com 52,39%" — FALSO como inferência

O número é reproduzido exatamente com este corte: **seções cujo `DT_ENCERRAMENTO` em horário local
cai no minuto 17:00, exterior incluído**.

| Corte "minuto 17:00 local" | Seções | Lula % | Nº 22 % | Saldo Lula no resto |
|---|---:|---:|---:|---:|
| **2026** | 150.771 | 47,61 | **52,39** | +6.177.738 |
| **2022 (sem prorrogação)** | 195.818 | 48,91 | **51,09** | +3.179.787 |

Bolsonaro também "venceu até as 17h" em 2022. O corte é um artefato, e são três os erros dele:

1. **Fuso horário.** 32 mil seções de MT, MS, RO, AC, RR e AM fecham às 15h ou 16h locais (que são
   17h em Brasília) e caem todas no grupo "até 17h". São estados majoritariamente de Flávio
   (40,3% Lula, saldo de −1,44 milhão).
2. **Fechar às 17h01 não é votar fora do prazo.** Quem está na fila às 17h vota normalmente, e a urna
   só é encerrada depois. Em Brasília, nenhuma seção fechou antes de 17h00:00. O grupo "após 17h" do
   post reúne 70% das seções do país, quase todas fechadas entre 17h01 e 17h05.
3. **Fila se correlaciona com perfil.** Seções que ainda têm fila às 17h são maiores, mais urbanas e
   mais nordestinas. Por isso o voto em Lula cresce com o minuto de encerramento, **também em 2022**:

| Encerramento (Brasília) | Lula % 2026 | Lula % 2022 |
|---|---:|---:|
| 17:00 | 49,0 | 50,1 |
| 17:02 | 52,2 | 51,1 |
| 17:05 | 55,3 | 52,2 |
| 17:10 | 59,4 | 54,4 |
| 17:15 | 59,1 | 56,1 |

Em 2026 o gradiente é mais inclinado. Isso se explica sobretudo pela composição: a Bahia passou de
9,8% para 13,3% das seções que fecharam entre 17h05 e 17h15, o que é coerente com a crise de ônibus
em Salvador, Feira de Santana e Lauro de Freitas que motivou o pedido de prorrogação. Dentro de cada
estado, a diferença entre seções que fecham cedo e tarde tem tamanho parecido nos dois anos na maioria
dos estados (SP: +7,2 pontos em 2026 e +6,4 em 2022; ver `04`).

## 2. Seções tardias e "após as 19h" — prorrogação real, efeito pequeno, tabela com cherry-pick

A prorrogação até 19h (decisão de Zanin na Rcl 101.673) **aparece nos dados**: 6.352 seções do Brasil
fecharam depois das 19h em 2026, contra 21 em 2022.

A tabela do post por estado confere número a número (BA 936 / 72,31%; PE 657 / 65,70%;
SP 1.571 / 57,46%; MA 83,31%), mas **omite o RJ**, que é o estado com mais seções após as 19h:

| UF | Seções ≥ 19h | Lula % |
|---|---:|---:|
| **RJ** | **2.805** | **45,81 (Flávio venceu)** |
| SP | 1.571 | 57,46 |
| BA | 936 | 72,31 |
| PE | 657 | 65,70 |
| MA | **3** | 83,31 |

O "MA 83,31%" do post se refere a **3 seções** (634 eleitores). O post exibe "—" no lugar da contagem.

**Limite aritmético.** O BU não registra o horário de cada voto, então não dá para verificar com estes
dados os ~34 mil votos depois das 17h informados pelo TSE. Mas isso não é necessário. Somando **todas**
as seções que fecharam a partir das 17h16 (8.845 seções, 2,54 milhões de comparecimento), o saldo de
Lula nelas é de +278.748. Com a margem oficial de 4.430.191:

- anular essas seções inteiras: Lula vence por **4,15 milhões**;
- anular todos os votos de Lula nelas e manter os de Flávio: Lula vence por **3,07 milhões**;
- transferir todos os votos de Lula nelas para Flávio: Lula vence por **1,71 milhão**.

## 3. Biometria — o número confere, a conclusão é falsa

- `QT_ELEI_BIOM_SEM_HABILITACAO` (definição do leiame do TSE): "eleitores com biometria, mas que não
  foram habilitados por meio dela". É a liberação regulamentar feita pelo mesário depois de falhas na
  leitura da digital. O eleitor continua identificado por documento e título.
- 2026: **8.632.488 (6,73%)**, igual ao post. **2022: 10.011.347 (8,06%)**, ou seja, mais do que agora.
- Comparar esse número com a margem não faz sentido. São votos legítimos de eleitores identificados,
  e eles se dividem entre os dois candidatos.
- Correlação ponderada entre a taxa de liberação e o percentual de Lula:

| | Bruta | Dentro do município | Dentro do mesmo local de votação |
|---|---:|---:|---:|
| 2026 | 0,063 | 0,010 | 0,014 |
| 2022 | 0,144 | −0,007 | −0,020 |

A correlação bruta é fraca e vem da geografia: o Nordeste tem mais liberações (uma hipótese plausível
é a de eleitorado mais velho e digitais desgastadas por trabalho manual) e vota mais em Lula. Comparando seções vizinhas, no mesmo
município ou na mesma escola, ela **desaparece**. A "curva" do post (liberação de 20%, 30% e 50% ou
mais) cobre cerca de 4.150 seções (0,8% do total), mais nordestinas que a média; os "picos de mais de
60%" correspondem às 97 seções com 50% ou mais de liberação (61,2% Lula). Em 2022 o mesmo padrão por
faixa foi **mais forte** (68,7% Lula na faixa de 30 a 50%).

## 4. "Unanimidade" — a mesma assimetria, e maior, em 2022

| | 100% Lula | 100% nº 22 | ≥ 90% Lula | ≥ 90% nº 22 | Razão ≥ 90% |
|---|---:|---:|---:|---:|---:|
| 2026 | 106 | 4 | 6.899 | 384 | 18:1 |
| 2022 | 143 | 4 | 9.538 | 220 | 43:1 |

(Percentual sobre votos válidos. Os números de 2026 coincidem exatamente com os do post.)

Os redutos de Lula (interior de MA, BA, PI, CE) são historicamente muito mais homogêneos que os redutos
bolsonaristas (RS, SC, MT), onde o voto raramente passa de 80 a 85%. As seções 100% são pequenas
(mediana de 122 votos válidos). A distribuição por seção **não** deveria ser gaussiana, porque reflete
a geografia social.

## 5. Benford — o próprio post não apresenta resultado

A lei de Benford do 1º dígito é sabidamente inválida para contagens de votos por seção, porque o
tamanho das seções (cerca de 50 a 500 eleitores) restringe os dígitos. A literatura (Deckert, Myagkov &
Ordeshook, 2011) mostra falsos positivos e falsos negativos. O post diz ter feito o teste, mas não mostra
nada. Não reproduzi.

## 6. Outras alegações

- **"Dados sonegados por 72 horas"**: os arquivos BWeb do 2º turno foram **gerados em 26/10/2026
  às 07:42** (segunda-feira de manhã), e a entrada no catálogo do portal foi atualizada em
  **27/10 às 19:22**, cerca de 50 horas após o fechamento das urnas e antes de quarta-feira. Mais
  importante: o campo `DT_BU_RECEBIDO` mostra que **todos** os BUs chegaram à totalização na
  própria noite da eleição (mediana às 20h26, último às 23h21 de 25/10). Além disso, cada BU é
  impresso e afixado na seção ao fim da votação, o que permite conferência independente.
- Passaportes, PF, Banco Master, Trump, China etc. não são alegações sobre dados e ficam fora do
  escopo desta análise.

## 7. Segundo controle: 2018 (Haddad 13 × Bolsonaro 17; vitória de Bolsonaro)

BWeb do 2º turno de 2018 (SHA-512 conferido; totais batem com o oficial: Bolsonaro 57.797.847,
Haddad 47.040.906). Diferença importante: **em 2018 o horário de votação era local** (8h às 17h em
cada fuso). A unificação pelo horário de Brasília só veio em 2022, então em 2018 o corte do post não
tem o artefato de fuso. Script: `06_tres_eleicoes.py`. "13" é Lula em 2022/2026 e Haddad em 2018;
"adv" é o adversário.

| Métrica | 2018 (venceu adv) | 2022 (venceu 13) | 2026 (venceu 13) |
|---|---:|---:|---:|
| % do 13 nacional | 44,87 | 50,90 | 51,79 |
| Corte do post: % do 13 "até 17h" | 44,74 | 48,91 | 47,61 |
| Corte do post: % do 13 "após 17h" | 44,98 | 52,25 | 53,53 |
| Seções fechadas ≥ 17h16 | 1.035 | 1.554 | 8.845 |
| % do 13 nessas seções | **51,07** | 56,50 | 55,70 |
| Seções fechadas ≥ 19h | 34 | 21 | 6.352 |
| Liberados sem biometria | 7.898.943 (6,81%) | 10.011.347 (8,06%) | 8.632.488 (6,73%) |
| Corr. biometria × % do 13, bruta | **0,174** | 0,145 | 0,064 |
| Corr. biometria × % do 13, dentro do município | 0,019 | −0,007 | 0,010 |
| Seções 100% 13 / 100% adv | **328 / 4** | 143 / 4 | 106 / 4 |
| Seções ≥ 90% 13 / ≥ 90% adv | **15.133 / 1.328 (11:1)** | 9.538 / 220 (43:1) | 6.899 / 384 (18:1) |

O que 2018 acrescenta:

- **Biometria e unanimidade:** os dois "indícios" do post aparecem com força numa eleição que o 13
  **perdeu** por 10,7 milhões de votos. A correlação bruta entre liberação sem biometria e voto no 13
  foi a mais alta das três eleições (0,17), e o 13 teve 328 seções com 100% dos votos contra 4 do
  adversário. Se esses padrões fossem marcas de fraude a favor do 13, ela teria fracassado justamente
  quando as marcas eram maiores. Eles refletem a geografia do eleitorado do PT, não o resultado.
- **Seções que fecham tarde:** também em 2018 elas votaram bem mais no 13 do que a média (51,1%
  contra 44,9% nacional).
- **Gradiente por minuto (alegação 1):** em 2018 ele é **bem mais fraco** (44,7% às 17h00, cerca de
  46 a 47% às 17h08–17h12) do que em 2022 e 2026, e o corte do post quase não separa os grupos
  (44,7% contra 45,0%). A explicação provável tem duas partes. Primeiro, não havia o artefato de
  fuso. Segundo, em 2018 Bolsonaro ia bem nas grandes cidades do Sudeste, onde se formam filas, de
  modo que a fila não pendia para um lado. A ressalva honesta é que o tamanho do gradiente depende da
  geografia eleitoral de cada ano, então 2018 não "reproduz" o gradiente de 2026. O controle decisivo
  para a alegação 1 continua sendo 2022: mesmos dois números, mesmo horário unificado, nenhuma
  prorrogação, e o mesmo efeito.
- **A única coisa realmente atípica em 2026** é o número de seções que fecharam depois das 19h
  (6.352, contra 34 em 2018 e 21 em 2022), que é o efeito direto da prorrogação. Como mostra a
  seção 2, ela não tem tamanho para mudar o resultado.

---

# Parte 2 — Outras teses de fraude

Dados adicionais: BWeb do 1º turno de 2026 e de 2022 (só presidente; SHA-512 conferido;
totais batem com o oficial), correspondência esperada urna × seção do 2º turno de 2026
(CESP, com SHA-512) e o arquivo de logs do AC (2º turno de 2026), usado só para calibrar
número de série × modelo de urna. **Os logs do Brasil inteiro (~134 GB) ainda não foram
analisados**; ver "pendências" no fim.

## 8. "É matematicamente impossível Lula ter ganhado tanto do 1º para o 2º turno" — FALSO

| 2026 | 1º turno | 2º turno | Δ |
|---|---:|---:|---:|
| Lula | 53.879.538 | 64.256.232 | **+10,38 mi** |
| Flávio | 56.104.503 | 59.826.041 | +3,72 mi |
| Demais candidatos | 9.321.993 | — | −9,32 mi |
| Brancos + nulos | 5.969.801 | 4.153.801 | −1,82 mi |
| Comparecimento | 125.275.835 | 128.236.074 | +2,96 mi |

- **A conta fecha.** Estoque disponível = terceiros + queda de brancos e nulos + aumento de
  comparecimento = 9,32 + 1,82 + 2,96 = **14,10 milhões**, que é exatamente o crescimento somado dos
  dois (+10,38 + 3,72). Lula ficou com **73,6%** desse estoque.
- **Em 2022 aconteceu o espelho:**

| 2022 (Brasil, seções pareadas) | Δ 1º → 2º turno | Fatia do estoque (10,18 mi) |
|---|---:|---:|
| Lula | +3,07 mi | 30,2% |
| Bolsonaro | +7,11 mi | **69,8%** |

  Ninguém chamou aquilo de impossível.
- **Limite rígido por seção.** Quem se absteve no 1º turno pode votar no 2º, então a abstenção também
  é uma fonte legítima de votos. O ganho de um candidato numa seção só pode superar terceiros +
  brancos/nulos + abstenção do 1º turno se eleitores trocarem diretamente de um candidato para o
  outro. Isso acontece em **10 de 497.897 seções** (20 votos no total) em 2026, e em 6 seções em 2022.
- **Limite apertado** (terceiros + brancos/nulos + aumento *líquido* de comparecimento). Não é um
  limite rígido, porque quem votou no 1º turno pode faltar no 2º e vice-versa. Ele mostra com que
  frequência é preciso troca direta de voto ou rotação de abstenção. O ganho de Lula o excede em
  6.533 seções (1,31%) em 2026; em 2022 o ganho de Bolsonaro o excedeu em 3.127 (0,66%). O padrão é
  espelhado, e em 2026 é cerca de duas vezes mais frequente.
- **De onde veio o ganho de Lula** (regressão ecológica de Goodman por UF; são estimativas, sujeitas à
  falácia ecológica):

| Grupo no 1º turno | Tamanho | → Lula | → Flávio | → branco/nulo | → abstenção |
|---|---:|---:|---:|---:|---:|
| Augusto Cury (70) | 3,44 mi | 0,56 | 0,31 | 0,12 | 0,01 |
| Renan Santos (14) | 2,67 mi | 0,40 | 0,37 | 0,16 | 0,07 |
| Caiado (55) | 2,60 mi | 0,40 | 0,55 | 0,11 | −0,06 |
| Zema (30) | 0,32 mi | 0,00 | 0,86 | 0,14 | 0,00 |
| Brancos e nulos | 5,96 mi | **0,61** | 0,08 | 0,38 | −0,07 |
| Abstenção | 32,9 mi | **0,095** | 0,037 | 0,00 | 0,87 |

  A premissa escondida da tese ("votos de candidatos de direita vão para o Flávio") não se sustenta,
  e o maior saldo de Lula vem de quem votou branco, nulo ou não votou no 1º turno.

  **Ressalva:** o coeficiente de brancos e nulos para Lula (0,61; em 2022 foi 0,23 para Lula e 0,29
  para Bolsonaro) é a estimativa mais exposta à falácia ecológica, porque brancos, nulos e
  abstenção são mais comuns justamente onde Lula é forte. O argumento não depende dele: depende do
  limite rígido (10 seções) e do espelho de 2022.

## 9. "A virada às 20h24" — real, e normal

Reconstruindo a totalização pela ordem de chegada dos BUs (`DT_BU_RECEBIDO`), a última troca de
liderança foi às **20h23min38s, com 47,2% dos BUs**. Em 2022 a virada de Lula foi às **18h43, com
67,6%** (contando o exterior, como em 2026), ou seja, mais tarde na apuração. Nos dois anos, dentro de cada estado, os BUs que chegam por
último votam cerca de 2 pontos a mais no 13 (2026: 53,1% contra 50,9%; 2022: 52,3% contra 50,0%).
O Nordeste **não** chegou por último em 2026: a mediana de chegada foi 20h27 no Nordeste contra 20h25
no resto do país. A apuração de 2026 praticamente só começou depois das 19h, o que é coerente com a
prorrogação. Dos 1.868 BUs recebidos antes disso, 776 são do exterior e 1.092 de seções brasileiras
que fecharam entre 17h00 e 17h06 e transmitiram imediatamente.

## 10. "Comparecimento impossível" — FALSO

| 2º turno | Comparec. > aptos | Abstenção zero | Comparec. ≥ 98% | Comparec. médio |
|---|---:|---:|---:|---:|
| 2018 | 0 | 10 | 35 | 78,8% |
| 2022 | 0 | 4 | 16 | 79,6% |
| 2026 | **0** | 12 | 66 | 81,0% |

As 12 seções com abstenção zero em 2026 são minúsculas (mediana de 57 aptos).

## 11. "Seções com zero votos para Flávio" — padrão antigo

São 106 seções em 2026, contra 143 sem voto em Bolsonaro em 2022 e 328 em 2018. Ficam no Alto
Solimões (AM: Tabatinga, Atalaia do Norte, Santo Antônio do Içá), no MA e no PA. **Flávio já tinha
praticamente zero nelas no 1º turno** (118 votos somando todas as 106).

## 12. "Comparecimento subiu nos redutos de Lula" — FALSO

O comparecimento subiu 2,96 milhões do 1º para o 2º turno, mas **de forma uniforme**: +1,50 ponto
percentual no decil mais pró-Flávio e +1,58 no decil mais pró-Lula (+1,8 a +2,1 nos decis
intermediários). O maior aumento absoluto foi em **SP** (+932 mil), estado que Flávio venceu.

## 13. "Urnas antigas votaram mais no Lula" (tese do PL, 2022) — efeito de geografia

Geração da urna inferida pela faixa do número de série, calibrada com os logs do AC (UE2020 de
2,01 a 2,10 milhões; UE2022 de 2,25 a 2,47 milhões). O AC não tem urnas anteriores a 2020, então
"abaixo de 2,0 milhões = anterior a 2020" é uma **extrapolação** da numeração sequencial, não algo
observado.
Diferença de % do 13 entre urnas antigas e novas:

| | Bruta | Mesmo município | Mesmo local de votação |
|---|---:|---:|---:|
| 2022 | **+3,45 p.p.** | +1,03 | +0,19 |
| 2026 | +0,51 | −0,21 | +0,37 |

A diferença de 2022 existe nos dados brutos e cai para cerca de um terço dentro do mesmo município
(+1,03) e para perto de zero dentro do mesmo local de votação (+0,19, com 1.745 seções). As urnas
antigas estavam mais no Nordeste e no interior. Em 2026 ela não existe nem no agregado. Poucos
locais de votação misturam gerações (cerca de 1.400 seções), então o controle por município é o mais
robusto.

## 14. "Urnas trocadas" — 99,4% das seções usaram exatamente a urna e a carga previstas

Cruzamento entre a urna efetivada (BWeb) e a correspondência esperada publicada em 24/10 (antes da
eleição):

| Situação | Seções | % do 13 |
|---|---:|---:|
| Urna e carga esperadas | 496.138 | 51,78 |
| Urna de contingência da própria zona | 2.267 | 51,49 |
| Urna de contingência de outra zona | 632 | 52,14 |
| Sem explicação pelas listas (outra seção, fora das listas, carga diferente, seção sem correspondência) | 168 | — |

As seções com urna substituída votaram **0,29 ponto a menos** em Lula do que a média do próprio
município. As 168 sem explicação somam 37.639 eleitores e um saldo de +4.835 para Lula, cerca de 0,1%
da margem. Das 39 seções sem correspondência esperada, 27 são do exterior. A explicação mais provável (não verificada) são urnas preparadas
depois da geração da lista, em 24/10. Isso pode ser checado nos logs.

## Pendências

- **Logs das urnas (~134 GB):** permitiriam contar exatamente os votos registrados depois das 17h e
  das 19h (para conferir os ~34 mil do TSE), identificar o modelo de cada urna sem inferência por
  faixa de série e explicar as 168 seções da seção 14.
- **Correspondência efetivada** do 2º turno, quando o TSE publicar.

## Limites desta análise

O BWeb não permite auditar votos individuais. O que a análise mostra é que **nenhum dos padrões
apresentados no post é evidência de fraude**: todos se reproduzem numa eleição de controle ou se
explicam por fuso, geografia e filas, e a prorrogação, mesmo tratada da forma mais hostil possível,
não muda o vencedor. Isso refuta o post nos próprios termos dele. Não é uma prova de que fraude é
impossível em geral; para isso existem outros mecanismos (teste de integridade, logs das urnas,
auditoria dos códigos), que estão fora do escopo.
