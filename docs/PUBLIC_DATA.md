# Dados públicos opcionais

A demo não depende de rede e não contém cotações reais.

## Fontes verificadas no trabalho

- CVM DFP: https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp
- CVM ITR: https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr
- Metodologia FCFF/FCFE: https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation

As páginas oficiais da CVM descrevem demonstrações, reapresentações e licença ODbL. Uma captura atual de ZIP não comprova disponibilidade histórica de cada registro.

## Download e parse explícitos

```powershell
$env:PYTHONPATH = 'src'
py -3.10 -m ma_deallab.cli fetch-cvm dfp 2025
py -3.10 -m ma_deallab.cli inspect-cvm data/raw/cvm/<hash>/source.zip --member dfp_cia_aberta_DRE_con_2025.csv --cnpj <CNPJ> --scope CON --as-of 2026-09-30 --available-at <publication-date> --version 1
```

O download só ocorre nesse comando. Mantém ZIP, SHA256, URL e data de captura, com timeout e limite de tamanho. O parser não extrai caminhos do ZIP para o disco, exige membro/escopo/versão e rejeita duplicatas, moeda/escala desconhecida e publicação futura. `available_at` deve vir da evidência de publicação do protocolo; não é inferida de DT_REFER.

Nenhum valor CVM é unido ao identificador sintético NEXAOPS_SYNTH. O parser retorna contas originais; a definição de EBITDA ajustado, leases e dívida exige mapeamento revisado por companhia.

## Comparáveis via --peers

Importe um array JSON de peers completos. Cada item precisa dos valores BRL: `market_cap, debt, cash, leases, minority, preferred, nonoperating, ltm_ebitda, ltm_revenue`; datas `quote_date, capital_structure_date, ltm_end, available_at`; `name, source_url, snapshot_hash, inclusion_reason, data_class` e `lease_policy: "ALIGNED"`.

Zeros só podem ser informados se verificados. Ausência permanece null e exclui o peer. Market cap precisa ser reconciliado a preços e ações por classe, incluindo eventos societários. O importador não prova a veracidade econômica dos dados fornecidos pelo analista; registra e valida o contrato.

O serviço calcula EV e múltiplos, exclui denominador negativo ou incompleto, e só publica mediana com três nomes distintos e utilizáveis. Inputs devem ser compatíveis com a mesma data-base e política de leases. Nenhum peer real está pré-carregado porque o conjunto completo não foi verificado neste trabalho.

Integrações B3/BCB/IBGE/Damodaran e comparáveis transacionais permanecem etapas dependentes de pesquisa e snapshots próprios, sem preenchimentos fictícios.
