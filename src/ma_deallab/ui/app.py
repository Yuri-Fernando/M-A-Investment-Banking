"""Streamlit UI; all financial calculations delegate to shared service functions."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ma_deallab.contracts import AS_OF, DISCLAIMER, M, ModelError
from ma_deallab.ingestion import load_case
from ma_deallab.research import evidence_lookup, monte_carlo
from ma_deallab.services import build_run, scenario_assumptions
from ma_deallab.transaction import STAGES, Workflow, vdr_access

st.set_page_config(page_title="M&A DealLab | Project Aurora", page_icon="📊", layout="wide")
st.markdown(
    """<style>.stApp{background:#f4f7fa}h1,h2,h3{color:#142d4e}
[data-testid="stMetric"]{background:white;padding:18px;border:1px solid #dce3ec;border-radius:5px}
[data-testid="stSidebar"]{background:#e8eef5}</style>""",
    unsafe_allow_html=True,
)
st.sidebar.title("M&A DealLab")
st.sidebar.caption("PROJECT AURORA / SYNTHETIC")
scenario = st.sidebar.selectbox("Cenário", ["base", "downside", "upside"])
page = st.sidebar.radio(
    "Área",
    [
        "Visão geral",
        "Histórico e checagens",
        "QoE e NWC",
        "Projeções",
        "Valuation",
        "Comparáveis",
        "Buy-side e Sell-side",
        "Diligência e data room",
        "Estrutura da transação",
        "Relatórios e evidências",
        "Pesquisa opcional",
    ],
)
st.sidebar.caption("Python 3.10 | local | sem credenciais")
try:
    baseline = build_run()
except (ModelError, ValueError, OSError) as exc:
    st.error(str(exc))
    st.stop()
active_defaults = baseline["scenarios"][scenario]["assumptions"]
with st.sidebar.expander("Premissas do cenário"):
    customize = st.checkbox("Editar premissas", value=False)
    growth = st.number_input(
        "Crescimento 2027 (%)",
        min_value=0.0,
        max_value=80.0,
        value=active_defaults["growth"] * 100,
        step=1.0,
        key="growth_" + scenario,
    )
    margin = st.number_input(
        "Margem EBITDA terminal (%)",
        min_value=8.0,
        max_value=50.0,
        value=active_defaults["terminal_margin"] * 100,
        step=1.0,
        key="margin_" + scenario,
    )
    rf = st.number_input(
        "Taxa livre de risco BRL (%)",
        min_value=0.0,
        max_value=40.0,
        value=active_defaults["rf_brl"] * 100,
        step=0.5,
        key="rf_" + scenario,
    )
    g = st.number_input(
        "Crescimento terminal (%)",
        min_value=0.0,
        max_value=30.0,
        value=active_defaults["terminal_g"] * 100,
        step=0.5,
        key="g_" + scenario,
    )
overrides = (
    {
        scenario: {
            "growth": growth / 100,
            "terminal_margin": margin / 100,
            "rf_brl": rf / 100,
            "terminal_g": g / 100,
        }
    }
    if customize
    else None
)
try:
    run = build_run(overrides=overrides) if customize else baseline
except (ModelError, ValueError, OSError) as exc:
    st.error(str(exc))
    st.stop()
s = run["scenarios"][scenario]
st.title("Project Aurora")
st.caption(f"NexaOps Analytics Ltda. | SYNTHETIC | as-of {AS_OF} | R$ mi | run {run['run_id']}")
st.info(
    "Simulação com dados sintéticos. Valores e premissas são ilustrativos. Materiais em rascunho para revisão."
)


def money(v):
    return f"{v / M:,.2f}"


def df(rows):
    return pd.DataFrame(rows)


if page == "Visão geral":
    metrics = [
        ("Receita LTM", run["ltm"]["net_revenue"]),
        ("EBITDA LTM", run["ltm"]["ebitda"]),
        ("Dívida líquida", run["net_debt"]),
        ("DCF standalone", s["valuation"]["ev"]),
    ]
    for offset in range(0, len(metrics), 2):
        for col, (label, value) in zip(st.columns(2), metrics[offset : offset + 2]):
            col.metric(label, money(value))
    st.subheader("Preço e decisão condicional")
    st.warning(s["decision"] + " | " + run["closing_status"])
    st.text(
        "EV proposto: R$ "
        + money(run["bridge"]["ev"])
        + " mi. Equity antes do ajuste de NWC: R$ "
        + money(run["bridge"]["equity"])
        + " mi."
    )
    comp = df(
        [
            {"Cenário": n, "EV (R$ mi)": v["valuation"]["ev"] / M, "Decisão": v["decision"]}
            for n, v in run["scenarios"].items()
        ]
    )
    st.plotly_chart(
        px.bar(comp, x="Cenário", y="EV (R$ mi)", color="Cenário", template="plotly_white"), width="stretch"
    )
    st.dataframe(comp, hide_index=True, width="stretch")
    st.write("Comparáveis públicos:", run["comps"]["status"])
    st.caption(
        "Football field: apenas cenários DCF disponíveis; múltiplos públicos/transacionais sem dados verificados."
    )

elif page == "Histórico e checagens":
    for kind, title in (("income", "DRE"), ("balance", "Balanço"), ("cashflow", "Fluxo de caixa")):
        st.subheader(title + " | R$ mi")
        table = pd.DataFrame(run[kind]) / M
        st.dataframe(table, width="stretch")
    st.subheader("LTM = FY2025 − 9M2025 + 9M2026")
    st.dataframe(pd.Series(run["ltm"], name="R$ mi") / M, width="stretch")
    st.dataframe(df(run["checks"]), hide_index=True, width="stretch")

elif page == "QoE e NWC":
    st.subheader("Ajustes de EBITDA | FY2025")
    st.write(
        "EBITDA reportado / ajustado aceito:",
        money(run["qoe"]["reported"]),
        "/",
        money(run["qoe"]["adjusted"]),
    )
    st.dataframe(df(run["qoe"]["items"]), hide_index=True, width="stretch")
    st.caption(
        "Aceite exige reviewer e evidence_id via --qoe-decisions; nenhum ajuste proposto é aceito automaticamente."
    )
    st.write("NWC operacional (inclui imposto a pagar): R$ " + money(run["operating_nwc"]) + " mi")
    st.write("NWC contratual ilustrativo (exclui imposto): R$ " + money(run["contract_nwc"]) + " mi")
    st.warning(run["policy"]["nwc_peg"])
    st.code('{"Q01":{"reviewer":"demo-reviewer","evidence_id":"DEMO_Q01_INVOICE"}}', language="json")

elif page == "Projeções":
    st.write(
        "Receita FY2026E = 9M observado + Q4 projetado: R$ " + money(s["fy2026e"]["net_revenue"]) + " mi"
    )
    st.caption("Q4/2026 é um trimestre; 2027–2031 são anos completos. Caixa vem da DFC, sem plug.")
    table = df(
        [
            {
                k: r[k] / M
                if k in ("net_revenue", "ebitda", "net_income", "fcff", "cash", "capex", "nwc")
                else r[k]
                for k in (
                    "year",
                    "period",
                    "net_revenue",
                    "ebitda",
                    "net_income",
                    "capex",
                    "nwc",
                    "fcff",
                    "cash",
                    "bs_residual",
                )
            }
            for r in s["forecast"]
        ]
    )
    st.dataframe(table, hide_index=True, width="stretch")
    st.plotly_chart(
        px.line(
            table,
            x="year",
            y=["net_revenue", "ebitda", "fcff"],
            markers=True,
            labels={"value": "R$ mi"},
            template="plotly_white",
        ),
        width="stretch",
    )
    st.caption("Premissas: montantes em BRL e taxas em fração.")
    st.json(s["assumptions"])
    for warning in s["warnings"]:
        st.error(warning)

elif page == "Valuation":
    cols = st.columns(2)
    cols[0].metric("WACC nominal BRL", f"{s['valuation']['wacc']:.2%}")
    cols[1].metric("EV standalone R$ mi", money(s["valuation"]["ev"]))
    st.metric("EV via múltiplo de saída", money(s["valuation"]["exit_ev"]))
    st.caption(s["wacc_build"]["erp_policy"])
    st.write("FCFF = EBIT × (1 − imposto) + D&A − capex − ΔNWC. Juros ficam fora do FCFF.")
    st.caption("Tabela: FCFF e PV em BRL; fatores adimensionais e prazos em anos.")
    st.dataframe(df(s["valuation"]["periods"]), hide_index=True, width="stretch")
    sens = df(s["sensitivity"])
    sens["ev"] = sens["ev"] / M
    matrix = sens.pivot(index="wacc", columns="g", values="ev")
    st.plotly_chart(
        px.imshow(
            matrix,
            text_auto=".1f",
            aspect="auto",
            color_continuous_scale="Teal",
            labels={"x": "g", "y": "WACC", "color": "EV R$ mi"},
        ),
        width="stretch",
    )
    st.subheader("Sensibilidade operacional")
    stress = df(s["stress"])
    stress["ev"] /= M
    st.plotly_chart(
        px.bar(stress, x="ev", y="driver", orientation="h", template="plotly_white"), width="stretch"
    )
    st.write("Synergy PV separado (não somado ao standalone): R$ " + money(s["synergies"]["pv"]) + " mi")

elif page == "Comparáveis":
    st.warning(run["comps"]["status"])
    st.write("Dados públicos e transações: nenhuma cotação ou múltiplo foi inventado.")
    st.json(run["comps"])
    st.caption(
        "CLI fetch-cvm baixa snapshots oficiais sob demanda; inspect-cvm exige companhia, escopo, versão e data de publicação."
    )

elif page == "Buy-side e Sell-side":
    st.subheader("Compradores fictícios | score com intervalo para dados ausentes")
    st.dataframe(df(run["buyer_screening"]), hide_index=True, width="stretch")
    st.subheader("Ofertas ilustrativas, não recebidas")
    st.dataframe(
        df(
            [
                {
                    "Comprador": b["buyer"],
                    "EV R$ mi": b["bridge"]["ev"] / M,
                    "Equity R$ mi": b["bridge"]["equity"] / M,
                    "Condições": b["conditions"],
                }
                for b in run["bids"]
            ]
        ),
        hide_index=True,
        width="stretch",
    )
    st.subheader("Cronograma planejado")
    st.dataframe(df(run["planned_events"]), hide_index=True, width="stretch")
    if "workflow" not in st.session_state:
        st.session_state.workflow = Workflow()
    flow = st.session_state.workflow
    st.write("Estado da simulação:", flow.stage)
    role = st.selectbox("Papel simulado", ["viewer", "analyst", "reviewer"])
    actor = st.text_input("Identificação do revisor")
    evidence = st.text_input("Evidence ID da aprovação")
    rationale = st.text_input("Justificativa")
    shortlist = st.checkbox("Shortlist revisada (simulação)")
    if st.button("Avançar uma etapa"):
        try:
            index = STAGES.index(flow.stage)
            if index == len(STAGES) - 1:
                raise ModelError("Fluxo já encerrado")
            flow.advance(
                STAGES[index + 1],
                role,
                actor,
                evidence,
                rationale,
                {"shortlist": shortlist},
                unresolved_high=sum(
                    r["severity"] == "HIGH" and r["status"] == "UNRESOLVED" for r in run["risks"]
                ),
            )
            st.success("Etapa registrada em memória nesta sessão.")
        except ModelError as exc:
            st.error(str(exc))
    st.json(flow.events)
    st.download_button(
        "Baixar log da simulação", json.dumps(flow.events, indent=2), file_name="simulated_events.json"
    )
    st.caption("Papéis são uma demonstração de política; não representam autenticação.")

elif page == "Diligência e data room":
    st.dataframe(df(run["risks"]), hide_index=True, width="stretch")
    role = st.selectbox("Papel para consulta", ["viewer", "counterparty", "analyst", "reviewer"])
    st.write(
        "Acesso a documentos não aprovados:",
        "PERMITIDO NA SIMULAÇÃO" if vdr_access(role, False) else "BLOQUEADO",
    )
    if vdr_access(role, False):
        st.dataframe(
            df(run["qoe"]["items"])[["issue_id", "description", "evidence_id", "status"]],
            hide_index=True,
            width="stretch",
        )
    st.caption("VDR contém apenas evidências sintéticas em rascunho, geradas no pacote de exportação.")

elif page == "Estrutura da transação":
    b = run["bridge"]
    fig = go.Figure(
        go.Waterfall(
            x=["EV", "Caixa", "Dívida", "Debt-like", "NWC", "Fees", "Equity"],
            measure=["absolute", "relative", "relative", "relative", "relative", "relative", "total"],
            y=[
                b["ev"] / M,
                b["cash"] / M,
                -b["financial_debt"] / M,
                -b["debt_like"] / M,
                b["nwc_adjustment"] / M,
                -b["seller_fees"] / M,
                0,
            ],
        )
    )
    fig.update_layout(template="plotly_white", title="EV → Equity | R$ mi")
    st.plotly_chart(fig, width="stretch")
    st.caption("JSON de termos: valores monetários em BRL; stake em fração.")
    st.json(run["consideration"])
    st.warning("Peg de NWC não acordado; caixa e dívida são do as-of, não saldos de fechamento verificados.")
    st.caption("Completion accounts e locked-box são alternativas; o motor rejeita a aplicação simultânea.")

elif page == "Relatórios e evidências":
    st.write(
        "Excel de cada cenário, IC, DD, valuation, teaser anônimo, closing packet, CIM e management deck."
    )
    if st.button("Gerar pacote congelado local"):
        try:
            from ma_deallab.export import export_run

            destination = export_run(run, Path("outputs"))
            st.session_state.export_path = str(destination)
            st.success("Pacote verificado: " + str(destination))
        except (ModelError, OSError) as exc:
            st.error(str(exc))
    if "export_path" in st.session_state:
        st.code(st.session_state.export_path)
    st.download_button(
        "Baixar run.json", json.dumps(run, indent=2, sort_keys=True), file_name=f"{run['run_id']}.json"
    )
    query = st.text_input("Buscar evidência (ex.: ltm ebitda, valuation wacc)")
    if query:
        evidence = evidence_lookup(run, query)
        st.json(evidence if evidence else {"status": "INSUFFICIENT_EVIDENCE"})
    st.dataframe(
        df([{"source": k, **v} for k, v in run["sources"].items()]), hide_index=True, width="stretch"
    )

else:
    st.caption("Pesquisa opcional offline, sem LLM. Distribuições ilustrativas não calibradas.")
    if st.button("Rodar Monte Carlo ilustrativo"):
        case = load_case()
        a = type(scenario_assumptions(case, scenario))(**s["assumptions"])
        st.json(monte_carlo(case, a))
    st.write("Coortes e retenção por cliente indisponíveis: dados granulares não foram fornecidos.")
st.caption(DISCLAIMER)
