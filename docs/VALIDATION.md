# Validação e evidências

## Comandos

Na raiz, com Python 3.10:

```powershell
$env:PYTHONPATH = 'src'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
py -3.10 -m pytest -q
py -3.10 -m ruff check src tests scripts
py -3.10 -m ma_deallab.cli demo
py -3.10 -m ma_deallab.cli verify outputs/<run_id>
```

A evidência selecionada fica em [evidence/validation.json](evidence/validation.json), [evidence/native_office_audit.json](evidence/native_office_audit.json) e [evidence/model_reference.json](evidence/model_reference.json).

## Escopo dos testes

- Valores de referência independentes: receita/EBITDA/NI, caixa 6→8→9→11, LTM e dívida líquida.
- Identidades históricas e forecast de DRE/BP/DFC, PPE, dívida e patrimônio.
- DCF de duas etapas calculável à mão e invariantes de sensibilidade.
- Ponte EV/equity, true-up, locked-box, earn-out, escrow, stake e rollover.
- Entradas ausentes, duplicadas, futuras, negativas, não finitas e em unidade ambígua.
- QoE proposto, aceito, sem evidência e fora do período.
- Workflow, revisão, shortlist, permissões simuladas e gates de closing.
- Parser CVM com ZIP local controlado e contrato de peers.
- Determinismo dentro do ambiente e integridade dos runs/artefatos.
- Planilhas, PDFs, PPTX e navegação das onze áreas do dashboard.
- Pesquisa local, Monte Carlo com seed fixa e controles de premissas da interface.

## Fórmulas e Excel

Cada workbook contém 33 abas e 518 fórmulas geradas. Um avaliador AST independente percorre referências e aritmética do subconjunto utilizado, detecta dependências cíclicas e compara resultado, referência Python e cache salvo.

A verificação nativa é separada:

```powershell
py -3.10 scripts/verify_office.py outputs/<run_id>
```

O Excel recalcula uma cópia temporária e compara todas as fórmulas. A auditoria registra versão da aplicação e maior diferença observada. Salvar uma fórmula no XLSX, por si só, não seria evidência de recálculo.

## Documentos e apresentação

O pacote gera:

| Material | Cobertura estrutural |
|---|---|
| IC | 4 páginas |
| DD | 6 páginas |
| Valuation | 4 páginas |
| Closing | 3 páginas |
| Teaser anônimo | 1 página; sem nome do alvo/compradores |
| CIM | 16 slides |
| Management deck | 10 slides |

Os testes conferem quantidade, texto sintético, geometria e anonimato. O PowerPoint abre e renderiza os slides; sua checagem de altura de texto complementa a inspeção visual, sem prometer que toda escolha editorial possa ser automatizada.

## Reprodutibilidade e tolerâncias

O motor calcula em float64 após conversão explícita da escala. A tolerância contábil é 0,001 BRL. A paridade de fórmulas usa tolerâncias relativas/absolutas mais restritas que o arredondamento da apresentação.

Run ID congela conteúdo e código. Arquivos binários podem variar por fontes, timestamps e plataforma. Compare resultados numéricos com tolerância; não use igualdade binária de PDFs como teste do modelo.

## CI remoto

O workflow executa instalação, Ruff, pytest e demo em Linux e Windows com Python 3.10. A execução corrente é consultável em Actions; evidências nativas de Office são locais e não são presumidas pelo runner.

## Não inferido pelos testes

Os testes não demonstram: auditoria de uma empresa real; qualidade de dados não fornecidos; cotação real; transação executada; financiamento comprometido; autenticação/VDR produtivo; build Docker; implantação em nuvem; calibração empírica das distribuições de stress.
