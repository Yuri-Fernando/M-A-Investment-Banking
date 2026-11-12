# Modelo financeiro implementado

A política detalhada e as hipóteses estão em [MODEL_POLICY.md](MODEL_POLICY.md). Esta página resume os contratos de apresentação.

## Horizonte

- Histórico: FY2023/FY2024/FY2025 e fluxos 9M2025/9M2026.
- Saldo de entrada do forecast: 2026-09-30.
- Stub: Q4/2026.
- Anos completos: 2027–2031.
- LTM somente de fluxos: FY2025 − 9M2025 + 9M2026.

## Cadeia de cálculo

Histórico conciliado → QoE revisável → drivers → DRE/BP/DFC → FCFF → DCF → EV/equity → termos econômicos.

A dívida permanece fixa no exemplo. Caixa vem da DFC; patrimônio, do lucro e dividendos. NWC de fluxo e NWC contratual têm definições distintas.

## Excel

Três arquivos de 33 abas, um por cenário. Azul indica números gravados; preto, fórmulas locais; verde, referências entre abas. As fórmulas são salvas com resultados calculados pelo motor e verificadas independentemente.

O recálculo nativo está registrado na auditoria de Office. Sensibilidades e algumas tabelas auxiliares são snapshots. Alterar premissas exige regeneração para manter o conjunto Excel/PDF/PPTX/HTML coerente.

## Não disponível por ausência de dados

Peg mensal de NWC, coortes reais, comps públicos completos e transações comparáveis. Suas abas/estados informam indisponibilidade, sem fabricar inputs.
