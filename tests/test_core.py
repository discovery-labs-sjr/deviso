from deviso_core import clean_rates, convert_amount


def test_clean_rates_keeps_xof_reference():
    rates = clean_rates({"USD": 1.1, "XOF": 700.0})
    assert rates["EUR"] == 1.0
    assert rates["XOF"] == 655.957
    assert rates["USD"] == 1.1


def test_convert_amount_without_fee():
    result = convert_amount(
        amount=100,
        src="EUR",
        tgt="XOF",
        rates={"EUR": 1.0, "XOF": 655.957},
        fee_pct=0,
    )
    assert round(result["net"], 2) == 65595.70
    assert round(result["fee"], 2) == 0.0
    assert round(result["rate"], 3) == 655.957


def test_convert_amount_with_fee():
    result = convert_amount(
        amount=100,
        src="EUR",
        tgt="USD",
        rates={"EUR": 1.0, "USD": 1.085},
        fee_pct=2,
    )
    assert round(result["gross"], 2) == 108.50
    assert round(result["fee"], 2) == 2.17
    assert round(result["net"], 2) == 106.33
