# Arquitetura e decisões técnicas

## Limite do sistema

O DealLab é uma aplicação local de modelagem e execução simulada de M&A. O alvo e as contrapartes são fictícios. CLI e Streamlit utilizam serviços Python diretamente; não existe uma API HTTP produtiva ou uma integração de escrita com investidores.

## Direção das dependências

`contracts -> ingestion -> finance / transaction -> services -> reporting / export -> UI`

- `contracts`: premissas imutáveis, classificações, moeda e erros.
- `ingestion`: fontes, validação, conciliação, LTM, NWC e QoE.
- `finance`: roll-forwards, forecast, FCFF e DCF.
- `transaction`: termos econômicos e máquinas de estados.
- `services.build_run`: composição dos três cenários e do registro de métricas.
- `export.export_run`: verificação e publicação local dos arquivos.
- `ui/app.py`: apresentação; não implementa uma segunda fórmula de valuation.

As contas públicas seguem um caminho separado em `public_data`. O identificador sintético não recebe fatos CVM por associação acidental.

## Contrato de entrada

O conjunto canônico são sete CSVs em `examples/`. As cópias em `src/ma_deallab/data/` permitem distribuição em wheel. Não são versões diferentes do caso.

Cada fonte recebe hash SHA256, origem, classificação, data de disponibilidade sintética, escopo e unidade. A leitura exige entidade, conta, período e linhas mandatórias esperadas. Valores das fixtures são convertidos de BRL milhões para BRL.

Ausência, duplicata, escala incompatível, sinal inválido, escopo incorreto e publicação futura não são corrigidos por imputação silenciosa. As identidades financeiras precisam fechar antes do forecast.

## Forecast

Há seis períodos de projeção: Q4/2026 e cinco exercícios completos. O modelo calcula DRE, caixa e balanço em conjunto.

NWC utiliza uma razão de receita e uma política operacional de alocação. Caixa é resultado de CFO/CFI/CFF e patrimônio evolui por lucro menos dividendos; nenhum deles é usado para esconder diferença de balanço. A dívida do alvo é fixa no exemplo. Caixa negativo exige financiamento e bloqueia exportação.

Políticas, taxas e fórmulas detalhadas: [MODEL_POLICY.md](MODEL_POLICY.md).

## Run e reprodutibilidade

O run contém:

- fontes e hashes;
- versão e hashes dos arquivos Python do pacote;
- fatos históricos e LTM;
- premissas e resultados por cenário;
- QoE, riscos e termos econômicos;
- checks, estados de disponibilidade e registro de métricas.

O identificador é derivado do conteúdo canônico, com chaves ordenadas e proibição de NaN. O registro de métricas associa caminhos, valores, unidades, classificação, fórmulas de referência e hashes.

A repetibilidade de ID considera o mesmo conjunto de código, fontes, premissas e ambiente numérico. Plataformas e versões de runtime podem variar no último bit de ponto flutuante; as verificações financeiras usam tolerâncias explícitas. Não se promete igualdade binária de PDFs/PPTX entre sistemas.

O Git preserva LF nos arquivos de código e os bytes originais dos CSVs, reduzindo diferenças de snapshot por conversão de fim de linha.

## Publicação local

`export_run`:

1. verifica checks e necessidade de financiamento;
2. confere identidade do run, código atual e registro de métricas;
3. cria uma área temporária no mesmo volume;
4. copia os inputs somente se os hashes ainda coincidirem;
5. gera os três Excel e avalia suas fórmulas;
6. gera relatórios, materiais, apresentações, SQLite e HTML;
7. calcula checksums dos artefatos;
8. renomeia a pasta completa para `outputs/<run_id>/`.

Uma pasta existente só é reutilizada se seus arquivos passarem pela conferência. Caminhos externos ao run não são aceitos no manifest. Checksums são controles de integridade, não assinaturas profissionais ou aprovações de investimento.

## Persistência

Cada run contém um SQLite independente:

| Tabela | Campos centrais |
|---|---|
| financial_facts | kind, period_end, account, amount_brl, source_hash, data_class |
| forecasts | run_id, scenario, year, account, amount_brl |
| metadata | key, value_json |

O JSON preserva a estrutura completa, incluindo campos que não são materializados nas tabelas analíticas.

## Workflow e revisão

`Workflow` exige avanço consecutivo, papel de revisor, ator, evidência e justificativa. LOI requer shortlist e closing depende de gates explícitos e ausência de risco alto pendente.

`ArtifactReview` demonstra revisão de rascunho até distribuição simulada. Exportar um rascunho é diferente de distribuí-lo.

O processo editado no dashboard permanece na sessão e pode ser baixado separadamente. Não altera um valuation congelado. A política do VDR não inclui autenticação produtiva nem auditoria persistente de cada leitura.

## Decisões de escopo

- Python 3.10 como runtime suportado.
- Biblioteca padrão no núcleo financeiro; pandas na apresentação.
- SQLite e arquivos locais em vez de serviços externos obrigatórios.
- Sem LLM, conta de nuvem ou API paga para a demo.
- Comparáveis incompletos explicitamente indisponíveis.
- Sensibilidades e algumas tabelas Excel são snapshots do motor; mudança de premissas requer regeneração para consistência de todo o pacote.
- Docker é uma opção de distribuição ainda sem runtime validado.

## Evolução

Dados públicos point-in-time, NWC mensal, clientes/coortes, revisão persistente e segurança real são extensões com contratos e dados próprios. A arquitetura não trata uma demonstração como implantação pronta.
