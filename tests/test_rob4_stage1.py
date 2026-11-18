from decimal import Decimal
import pandas as pd
from app import compute_month_step, generate_synthetic_experiment

def test_three_month_fixture():
    fixture = pd.read_csv("sample_data/monthly_fixture.csv")
    cash = Decimal("5000.00")
    stock = 100
    expected = [
        ("2027-01", 30, 3600.0, 2550.0, 1050.0, 6950.0, 70),
        ("2027-02", 30, 3600.0, 2650.0, 950.0, 8800.0, 40),
        ("2027-03", 22, 2640.0, 2030.0, 610.0, 10070.0, 18),
    ]
    for i, row in fixture.iterrows():
        res = compute_month_step(
            month_str=str(row["month"]),
            requested=int(row["requested"]),
            base_price=Decimal("120.00"),
            staff_hours=90.0,
            hours_per_unit=3.0,
            opening_stock_units=stock,
            component_unit_cost=Decimal("30.00"),
            restock_units=0,
            defect_rate=0.0,
            non_component_var_per_unit=Decimal("35.00"),
            fixed_expense=Decimal("600.00"),
            ad_cost=Decimal(str(row["ad_cost"])),
            opening_cash=cash,
            capacity_override=int(row["capacity_override"]),
        )
        exp_m, exp_sold, exp_rev, exp_tot_exp, exp_prof, exp_cash, exp_stock = expected[i]
        assert res["month"] == exp_m
        assert res["sold"] == exp_sold
        assert res["revenue"] == exp_rev
        assert res["total_expense"] == exp_tot_exp
        assert res["operating_profit"] == exp_prof
        assert res["ending_cash"] == exp_cash
        assert res["ending_stock_units"] == exp_stock
        cash = Decimal(str(res["ending_cash"]))
        stock = res["ending_stock_units"]

def test_rob_business_specific_low_stock():
    res = compute_month_step(
        month_str="2027-01",
        requested=40,
        base_price=Decimal("120.00"),
        staff_hours=90.0,
        hours_per_unit=3.0,
        opening_stock_units=10,
        component_unit_cost=Decimal("30.00"),
        restock_units=0,
        defect_rate=0.0,
        non_component_var_per_unit=Decimal("35.00"),
        fixed_expense=Decimal("600.00"),
        ad_cost=Decimal("0.00"),
        opening_cash=Decimal("5000.00"),
    )
    assert res["sold"] == 10
    assert res["revenue"] == 1200.0
    assert res["total_expense"] == 1250.0
    assert res["operating_profit"] == -50.0
    assert res["ending_stock_units"] == 0
    assert res["ending_cash"] == 5000.0 + 1200.0 - 350.0 - 600.0

def test_zero_sales():
    res = compute_month_step(
        month_str="2027-01",
        requested=0,
        base_price=Decimal("120.00"),
        staff_hours=90.0,
        hours_per_unit=3.0,
        opening_stock_units=100,
        component_unit_cost=Decimal("30.00"),
        restock_units=0,
        defect_rate=0.0,
        non_component_var_per_unit=Decimal("35.00"),
        fixed_expense=Decimal("600.00"),
        ad_cost=Decimal("0.00"),
        opening_cash=Decimal("5000.00"),
    )
    assert res["revenue"] == 0.0
    assert res["variable_expense"] == 0.0
    assert res["operating_profit"] == -600.0

def test_ap_stats_synthetic_experiment():
    df = generate_synthetic_experiment(2027)
    assert len(df) == 80
    assert df["prospect_id"].nunique() == 80
    assert (df["message"] == "A").sum() == 40
    assert (df["message"] == "B").sum() == 40
    p_a = df[df["message"] == "A"]["converted"].mean()
    p_b = df[df["message"] == "B"]["converted"].mean()
    assert abs(p_a - 0.30) < 1e-6
    assert abs(p_b - 0.50) < 1e-6
    assert abs((p_b - p_a) - 0.20) < 1e-6
