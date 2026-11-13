# Radar Embu — coletor de dados (protótipo)

Coleta os dados públicos da Câmara Municipal de Embu das Artes no sistema
**NoPaper** (`nopapercloud.cmembu.sp.gov.br/spl/`) e grava tudo em `dados/embu.json`.
É a base para um site estático no estilo de um "raio-x" dos vereadores.

## Como rodar

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m coletor                    # desde a posse (2025-01-01)
.venv\Scripts\python.exe -m coletor --sem-sessoes      # só vereadores e propostas (≈1 min)
```

A primeira execução completa baixa cerca de 80 PDFs de sessões e extrai o texto em paralelo
(≈ 5 min). PDFs e texto ficam em `dados/cache/` e não são processados de novo.
Os CSVs dos anos anteriores também ficam em cache; o ano corrente é sempre atualizado.

## Site

```bash
.venv\Scripts\python.exe -m coletor.site                     # dados/embu.json -> site/dados.js + site/fotos/
.venv\Scripts\python.exe -m http.server 8765 --directory site  # abrir http://localhost:8765
.venv\Scripts\python.exe marca\gerar_logo.py                  # regenera logo, favicon e og.png
```

### Fotos e nomes

- **Nome exibido diferente da ficha** (ex.: "Vanessa da Saúde"): `coletor/ajustes.json`.
- **Fotos padronizadas** (fundo branco, rosto centralizado, 480×480): coloque a foto em
  `fotos_manuais/` com o nome do vereador no arquivo (opcional; senão usa a da ficha) e rode
  ```bash
  py -3.12 -m venv .venv-fotos
  .venv-fotos\Scripts\python.exe -m pip install "rembg[cpu]" "opencv-python-headless<5" pillow pillow-avif-plugin requests
  .venv-fotos\Scripts\python.exe marca\padronizar_fotos.py          # todas, ou passe ids: ... 87 89
  ```
  Usa Python 3.12 porque o rembg (remoção de fundo) ainda não roda no 3.15.
  Confira o resultado em `dados/cache/prancha_fotos.jpg`.

`site/` é 100% estático (index.html + app.js + dados.js) e pode ir para GitHub Pages,
Netlify ou qualquer hospedagem. O workflow `.github/workflows/atualizar.yml` coleta toda
madrugada, faz commit dos dados e publica no GitHub Pages.

## De onde vem cada dado

| Dado | Fonte no NoPaper | Como |
|---|---|---|
| Vereadores (nome, partido, e-mail, telefone, foto, Mesa) | `parlamentares.aspx` → `parlamentar.aspx?id=N` | HTML |
| Propostas (indicações, requerimentos, moções, PLs...) | `consulta-producao.aspx?tipo=T&ano_proposicao=A` + botão **CSV** | 1 CSV por tipo/ano (o ano inteiro de uma vez estoura o limite da exportação) |
| Votos nominais e presença | `sessoes.aspx` (paginado por postback) → PDF **Resultado da Votação** de cada sessão | texto do PDF (pypdf) |

### Cuidados conhecidos

- **CSV mal formado:** o NoPaper não escapa aspas nem quebras de linha nas ementas.
  `propostas.ler_csv` lê cada registro pelas colunas fixas do início e do fim.
- **Presença:** a "Lista de Presença" do PDF marca `---` até para quem votou.
  Presente = votou em alguma votação da sessão **ou** está como "Presente".
- **Nomes:** autores do CSV, fichas e PDFs usam o nome parlamentar com grafias diferentes;
  o casamento é feito sem acento/maiúsculas e por prefixo ("Abidan Henrique da Silva" → "Abidan Henrique").
  Nomes que não casam vão para `autores_sem_vereador` e `nomes_nao_casados_pdf` no JSON — confira a cada execução.
- **Ruas e bairros:** extraídos da ementa por expressões regulares; há falsos positivos.
  O próximo passo é validar contra uma lista oficial de bairros/logradouros (IBGE/OSM/Prefeitura).
- **Salário:** R$ 12.661,12 (legislatura 2025–2028), segundo reportagem de 2022 sobre a votação
  na Câmara. Trocar a fonte pelo ato oficial assim que localizado (`coletor/__main__.py`).
- **Nomes no painel de votação:** em fev/2025 o painel usava nome civil. `coletor/apelidos.json`
  liga esses nomes às fichas. "Giba do Embu" vota desde ago/2026 e não tem ficha no NoPaper.
- **Mesa Diretora:** o NoPaper só tem a 1ª formação (até 31/01/2026); o site mostra o período.

## Estrutura

```
coletor/
  http.py        cliente HTTP com intervalo, novas tentativas e cache de arquivos
  vereadores.py  lista e fichas dos vereadores
  propostas.py   exportação CSV por tipo/ano e leitor tolerante
  sessoes.py     lista de sessões (postback) e leitura dos PDFs de votação/presença
  analise.py     grupos (pedido/cobrança/homenagem/lei/outros), temas, ruas, bairros,
                 pedidos repetidos e números por vereador
  __main__.py    orquestra e grava dados/embu.json
```
