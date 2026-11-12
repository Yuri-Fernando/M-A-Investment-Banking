from zipfile import ZipFile

import pytest

from ma_deallab.contracts import ModelError
from ma_deallab.public_data import parse_cvm


def test_cvm_explicit_scope_unit_version_and_publication(tmp_path):
    p = tmp_path / "test.zip"
    member = "dfp_cia_aberta_DRE_con_2025.csv"
    text = (
        "CNPJ_CIA;ORDEM_EXERC;VERSAO;DT_FIM_EXERC;DT_INI_EXERC;CD_CONTA;ESCALA_MOEDA;MOEDA;VL_CONTA\n"
        "TEST;ÚLTIMO;1;2025-12-31;2025-01-01;3.01;MIL;REAL;1234.56\n"
    )
    with ZipFile(p, "w") as z:
        z.writestr(member, text.encode("latin-1"))
    facts = parse_cvm(p, member, "TEST", "CON", "2026-09-30", "2026-03-01", "1")
    assert facts[0]["amount_brl"] == 1234560
    assert facts[0]["scope"] == "CON"
    with pytest.raises(ModelError, match="FUTURE"):
        parse_cvm(p, member, "TEST", "CON", "2026-09-30", "2026-10-01", "1")
    with pytest.raises(ModelError, match="SCOPE"):
        parse_cvm(p, member, "NEXAOPS_SYNTH", "CON", "2026-09-30", "2026-03-01", "1")
    with pytest.raises(ModelError, match="SCOPE"):
        parse_cvm(p, member, "TEST", "IND", "2026-09-30", "2026-03-01", "1")
