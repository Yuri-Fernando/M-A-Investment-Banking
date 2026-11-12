# Referência da API Python

Todos os exemplos pressupõem Python 3.10 e instalação editável, ou `PYTHONPATH=src`. Valores monetários da API são BRL originais; apresentação em milhões exige divisão explícita por 1.000.000.

## Ingestão e histórico

| Função | Entrada | Retorno / comportamento |
|---|---|---|
| `load_case(data_dir=None, as_of=AS_OF)` | Diretório com as sete fixtures | Caso validado; falha em dados incompletos ou incompatíveis |
| `amount_brl(text, unit, locale)` | Texto numérico e escala explícita | Float BRL após parsing Decimal |
| `ltm(case, account=None)` | Conta de fluxo ou conjunto completo | FY2025 − 9M2025 + 9M2026; saldos são rejeitados |
| `nwc(bs, contract=False)` | Balanço canônico | Operacional com imposto, ou contratual sem imposto |
| `debt(bs)` | Balanço canônico | Dívida financeira de curto + longo prazo |
| `qoe(case, accepted=None, period=...)` | Decisões por issue/reviewer/evidence | Reportado, aceito ajustado e trilha dos itens |

```python
from ma_deallab.ingestion import load_case, ltm, amount_brl

case = load_case()
assert ltm(case, "net_revenue") == 99_000_000
assert amount_brl("1.234,56", "BRL", "pt_BR") == 1234.56
```

Contas mandatórias não recebem `fillna(0)`. O parser de fixtures usa magnitudes positivas para DRE/BP e os sinais definidos no arquivo de fluxo de caixa.

## Premissas e cálculo

`Assumptions` é uma dataclass congelada. Campos monetários incluem `q4_revenue`, `bid_ev` e `integration_cost`; taxas e razões são frações.

| Função | Finalidade |
|---|---|
| `scenario_assumptions(case, name)` | Construir premissas do CSV para base/downside/upside |
| `forecast(case, assumptions)` | Seis períodos integrados de DRE/BP/DFC |
| `model(case, assumptions)` | Forecast, FY2026E, valuation e warnings |
| `dcf(rows, wacc, g, exit_multiple)` | PV explícito, terminal e cross-check de saída |
| `sensitivity(rows, assumptions)` | Matriz WACC/g |
| `operating_stress(case, assumptions)` | Alteração isolada de drivers |
| `synergies(rows, assumptions)` | Valor esperado finito separado do standalone |

```python
from ma_deallab.services import build_run

run = build_run(overrides={"base": {"growth": 0.10}})
base = run["scenarios"]["base"]
print(base["valuation"]["ev"])   # BRL
print(base["valuation"]["wacc"]) # fração
```

Os overrides são agrupados por cenário. O caso aceita data-base 2026-09-30. WACC deve exceder g, valores devem ser finitos e os drivers precisam respeitar seus limites.

## Termos econômicos

`equity_bridge` recebe EV, caixa, dívida, debt-like, despesas do vendedor e, opcionalmente, NWC de closing/peg juntos.

```python
from ma_deallab.transaction import equity_bridge, consideration

bridge = equity_bridge(160_000_000, 11_000_000, 18_000_000)
assert bridge["equity"] == 153_000_000

terms = consideration(bridge["equity"], earnout_cap=15_000_000)
assert abs(terms["allocation_residual"]) < 0.001
```

- `mechanism`: completion_accounts ou locked_box.
- NWC/peg não podem ser aplicados ao locked-box.
- `consideration`: equity all-in, cap nominal, probabilidade, desconto, prazo, escrow, rollover e stake.
- `earnout_payout`: payout linear limitado entre zero e cap.
- `score_buyer`: notas 0–5 e pesos; dados ausentes geram intervalo e cobertura.

EV/equity negativos podem existir analiticamente em stress. Uma contraprestação negativa não é alocada como compra normal.

## Serviço e exportação

`build_run(data_dir=None, overrides=None, accepted_qoe=None, peers=None)` é o ponto comum de CLI e dashboard.

`export_run(run, output, data_dir=None)` retorna o diretório congelado. Não modifica um pacote anterior. Checks críticos, caixa negativo, run alterado, código diferente e registro adulterado bloqueiam a operação.

`verify_artifacts(directory)` confere cada arquivo listado no manifest.

```python
from pathlib import Path
from ma_deallab.export import export_run, verify_artifacts
from ma_deallab.services import build_run

path = export_run(build_run(), Path("outputs"))
assert verify_artifacts(path)["status"] == "PASS"
```

## Evidências e pesquisa

- `evidence_lookup(run, query, limit=10)`: retorna somente caminhos/entradas existentes no registro.
- `monte_carlo(case, assumptions, samples=500, seed=20261111)`: sensibilidade triangular independente de crescimento/margem, não calibrada com dados de mercado.
- `verify_workbook(path, formula_manifest)`: avalia todas as fórmulas do subconjunto gerado e compara os caches com o motor.

Consulta sem evidência retorna lista vazia; a UI a apresenta como informação insuficiente.

## Dados públicos

`download_cvm(kind, year, destination)` é uma operação de rede explícita. Retorna ZIP congelado por hash.

`parse_cvm(path, member, entity_cnpj, scope, as_of, available_at, version)` exige seleção explícita e preserva contas originais, período, hash e versão.

`trading_comps(peers, as_of)` calcula EV/múltiplos somente com entradas completas e compatíveis. Publica mediana com ao menos três nomes distintos. Ver [PUBLIC_DATA.md](PUBLIC_DATA.md).

## Erros operacionais

`ModelError` é a exceção de domínio. Entre os códigos/motivos estão:

`RECONCILIATION_ERROR`, `MISSING_REQUIRED_LINE`, `DATA_FUTURE_LEAK`, `SCOPE_MISMATCH`, `STOCK_LTM_DISALLOWED`, `FINANCING_REQUIRED`, `WORKBOOK_PARITY`, `RUN_INTEGRITY`, `ARTIFACT_INTEGRITY` e `CLOSING_BLOCKED`.

A mensagem informa o controle que falhou. Não se deve capturá-la para substituir o resultado por zero e continuar um relatório financeiro.
