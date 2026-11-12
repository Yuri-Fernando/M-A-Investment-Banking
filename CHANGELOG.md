# Changelog

## 1.0.0 — 2026-11-11

Primeira versão funcional do M&A DealLab Brazil.

### Implementado

- Ingestão, classificação, hashes e validação das sete fixtures.
- Conciliação histórica, LTM, QoE e forecast integrado de três demonstrações.
- FCFF DCF, WACC nominal BRL, terminal normalizado e cenários.
- Ponte EV/equity, NWC contratual, earn-out, escrow, stake e rollover.
- Workflow e revisão de materiais simulados.
- Excel de 33 abas por cenário, PDF/Markdown, CIM, management deck, HTML e SQLite.
- Busca determinística de evidências e Monte Carlo ilustrativo.
- Download CVM opt-in, parser explícito e contrato de trading comps.
- Empacotamento e execução pelo CLI/Streamlit.
- Documentação pública, imagens reais, referências e CI Linux/Windows.

### Validação registrada

69 testes; Ruff; 518 fórmulas por cenário verificadas pelo avaliador e pelo Excel; 16+10 slides renderizados no PowerPoint; PDFs e dashboard inspecionados. Evidência portável em docs/evidence.

### Limites

Caso sintético; sem comparáveis reais pré-carregados; NWC mensal e coortes não fornecidos; VDR demonstrativo; Docker e operação produtiva sem validação de runtime.
