# Guia operacional

## Ambiente

Use Python 3.10. A demo não exige segredos, serviço de nuvem ou Office instalado.

```powershell
py -3.10 --version
py -3.10 -m pip install -r requirements-lock.txt
py -3.10 -m pip install --no-deps -e .
```

Instale apenas as dependências que faltarem no ambiente escolhido. Não é necessário recriar um Python 3.10 já configurado.

## Fluxo offline

```powershell
py -3.10 -m ma_deallab.cli validate
py -3.10 -m ma_deallab.cli model
py -3.10 -m ma_deallab.cli demo
```

Sem instalação editável, defina `$env:PYTHONPATH='src'`.

O comando demo gera as três planilhas e todos os relatórios após validar o modelo. A saída informa run ID, EV por cenário, estado de closing e diretório.

## Dashboard

```powershell
py -3.10 -m streamlit run src/ma_deallab/ui/app.py
```

Acesse o endereço local exibido. Para outra porta, acrescente `--server.port 8511`. A configuração do repositório usa loopback. O processo pode ser interrompido com Ctrl+C no terminal.

O cenário escolhido determina os valores iniciais dos controles. Marque edição de premissas para recalcular um novo run. Uma entrada inválida deve bloquear o resultado.

## Encontrar e verificar o pacote

O diretório é `outputs/<run_id>/`. Não dependa de um nome de run fixo entre alterações de código ou ambientes.

```powershell
py -3.10 -m ma_deallab.cli verify outputs/<run_id>
```

Arquivos modificados ou removidos geram erro. Não atualize o manifest manualmente para esconder corrupção: gere outro pacote a partir dos inputs desejados.

## Customização

Use JSON local com `--assumptions`, `--qoe-decisions` ou `--peers`. Valores monetários usam BRL, e taxas usam frações.

```json
{"base": {"growth": 0.10, "terminal_margin": 0.20, "q4_revenue": 26000000}}
```

```powershell
py -3.10 -m ma_deallab.cli export --assumptions my_assumptions.json
```

Mudança de cenário gera outro run. O arquivo base de Excel não possui um seletor que atualize os outros arquivos congelados; abra o cenário desejado ou regenere os materiais.

QoE exige issue conhecido, reviewer, evidence_id correto e período compatível. As propostas permanecem fora do ajustado até o aceite.

## Verificação nativa de Office

Opcional: Windows, Excel, PowerPoint, pywin32 e PyMuPDF.

```powershell
py -3.10 scripts/verify_office.py outputs/<run_id>
py -3.10 scripts/render_pdf_previews.py outputs/<run_id>
```

O verificador usa cópias curtas temporárias, desabilita macros no Excel, não salva de volta a planilha original e fecha somente as apresentações que abriu. Evidências ficam em `outputs/validation/<run_id>/`.

## SQLite

Exemplo de leitura:

```sql
SELECT period_end, account, amount_brl
FROM financial_facts
WHERE kind = 'income' AND account IN ('net_revenue', 'ebitda')
ORDER BY period_end, account;

SELECT scenario, year, account, amount_brl
FROM forecasts
WHERE account IN ('net_revenue', 'fcff', 'cash')
ORDER BY scenario, year, account;
```

Montantes do banco estão em BRL. Fatos anuais e cumulativos devem continuar identificados por período; não some FY e 9M como observações independentes.

## Falhas e ação recomendada

| Sintoma | Ação |
|---|---|
| Módulo ma_deallab não encontrado | Instale o pacote editável ou defina PYTHONPATH=src na raiz |
| Python fora de 3.10 | Selecione explicitamente o runtime suportado |
| Campo/conta ausente | Corrija o conjunto de entrada; não impute zero |
| Conciliação não fecha | Confira sinal, escala, período e identidade contábil indicada |
| WACC menor ou igual a g | Revise premissas; não suprima a proteção |
| Caixa negativo | Modele financiamento/driver coerente; o export permanece bloqueado |
| QoE recusado | Confira período, evidência e revisor |
| Peers insuficientes | Forneça dados completos e compatíveis; ausência não é múltiplo zero |
| Closing bloqueado | Resolva riscos e aprovações explicitamente na simulação |
| Integridade de artefato falha | Preserve a evidência do erro e gere novo run íntegro |
| Pasta sincronizada lenta | Aguarde hidratação, use testes focados e inspecione processos antes de classificar timeout como erro financeiro |
| Office indisponível | Use verificação Python; não declare recálculo nativo executado |
| Porta ocupada | Escolha outra porta local com --server.port |

## Rede e publicação

A demo é offline. Somente `fetch-cvm` inicia download público explícito. Não existe envio de email, contato com compradores, ordem financeira ou implantação em nuvem.

As saídas e dados brutos são ignorados pelo Git. Mantenha credenciais em configuração local não versionada, mesmo ao ampliar o projeto.
