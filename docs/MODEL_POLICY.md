# Política implementada do modelo

- Dados e valuation em 2026-09-30; publicação sintética explícita nesse cutoff. Eventos de processo futuros são planejamento, não informação financeira observada.
- Fonte de dinheiro: R$ mi nos CSVs, convertido por Decimal para BRL no motor/SQLite. Cálculo subsequente em float64, tolerância contábil 0,001 BRL, mais estrita que 1 BRL exigido.
- NWC operacional = AR + inventory + other operating CA - AP - accruals - tax payable. Contrato ilustrativo exclui tax payable. Nenhum peg mensal é inventado.
- Q4 receita 26 mi, margem 22%, capex e D&A proporcionais à receita. Receita FY2026E é 101 mi. As premissas-base adicionais são ANALYST_ASSUMPTION.
- COGS 54%; opex é a diferença entre receita, COGS e EBITDA-alvo. Margem converge linearmente ao terminal em cinco anos.
- Forecast NWC por razão, sem simultaneamente aplicar dias. Inventory 3%, operating CA 3,5%, AP 12%, accruals 4,5% de receita anual; AR deriva desses drivers e do NWC-alvo. Essa é uma política operacional explícita, sem plug de caixa ou patrimônio.
- Tax payable e outros saldos não operacionais permanecem constantes. D&A alocada a PPE; intangíveis mantidos constantes. Capitalização de software demanda revisão futura.
- Dívida financeira mantida em 18 mi. Juros sobre saldo de abertura; Q4 usa 0,25. Dividendos: 30% do NI positivo. NI negativo não gera crédito tributário ou dividendo.
- Caixa = saldo inicial + CFO - capex - dividendos. Não há financiamento automático. Caixa negativo é exibido no modelo e bloqueia exportação.
- FCFF = EBIT(1-tax) + D&A - capex - ΔNWC, excluindo juros. A hipótese de dedutibilidade tributária do WACC é ilustrativa, sem cálculo de limites legais.
- Ke = rf nominal BRL + beta * ERP local total. Rf 10%, beta 1, ERP 7%, Kd 13%, Wd 20%, imposto 34% -> WACC 15,316%. ERP já inclui risco-país; nenhum CRP adicional.
- Desconto no fim do período: Q4 0,25 anos; 2027 1,25; 2031 5,25. Não se desconta FY2026 inteiro como um ano.
- Terminal normalizado = (NOPAT final + D&A final - capex final)*(1+g) - g*NWC final. Isso evita carregar o crescimento de NWC do último ano explícito perpetuamente quando g é diferente.
- Synergy: FCFF incremental líquido de impostos em horizonte finito, receita incremental proporcional, probabilidade 60%, desconto 18%, integração 3 mi paga em t=0 independentemente da realização. Não entra no EV standalone.
- EV negativo em stress não é truncado; equity pode ser negativo analiticamente. Consideração de aquisição não pode ser alocada se o preço total for negativo.
- Earnout: PV esperado dentro do equity all-in, cap nominal separado; escrow retido do upfront, rollover reduz desembolso. Partial stake é compra secundária, sem confundir com capital primário.
- Relatórios congelam todos os cenários. Cada Excel representa um único cenário; mudança exige nova geração ou edição consciente de suas fórmulas.
- Run ID depende dos inputs, decisões, premissas, resultados e hashes do código do pacote. Timestamps/bytes dos arquivos de Office/PDF não são prometidos idênticos entre plataformas.
