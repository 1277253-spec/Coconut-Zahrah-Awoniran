import json
import math
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Coconut | ROB-4 Robotics Studio (Stage 1)",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- EXACT MONEY HELPERS ---
def to_dec(val) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def fmt_usd(val) -> str:
    d = to_dec(val)
    return f"-${abs(d):,.2f}" if d < 0 else f"${d:,.2f}"

# --- DETERMINISTIC ROB ENGINE ---
def compute_month_step(
    *,
    month_str: str,
    requested: int,
    base_price: Decimal,
    staff_hours: float,
    hours_per_unit: float,
    opening_stock_units: int,
    component_unit_cost: Decimal,
    restock_units: int,
    defect_rate: float,
    non_component_var_per_unit: Decimal,
    fixed_expense: Decimal,
    ad_cost: Decimal,
    opening_cash: Decimal,
    capacity_override: int | None = None,
    refund_amount: Decimal = Decimal("0.00"),
    loan_cash: Decimal = Decimal("0.00"),
    loan_principal_repaid: Decimal = Decimal("0.00"),
    interest_expense: Decimal = Decimal("0.00"),
    additional_capex: Decimal = Decimal("0.00"),
    new_owner_cash: Decimal = Decimal("0.00"),
) -> dict:
    if requested < 0 or staff_hours < 0 or hours_per_unit <= 0 or opening_stock_units < 0 or restock_units < 0:
        raise ValueError("Inputs must satisfy non-negative / positive domain constraints.")
    if not (0.0 <= defect_rate <= 1.0):
        raise ValueError("defect_rate must be in [0, 1].")

    derived_capacity = math.floor(staff_hours / hours_per_unit)
    effective_capacity = int(capacity_override) if capacity_override is not None else derived_capacity

    available_stock = opening_stock_units + restock_units
    attempted = min(int(requested), effective_capacity, available_stock)
    failed = math.floor(attempted * defect_rate)
    sold = attempted - failed
    unserved_demand = max(0, int(requested) - attempted)

    revenue = to_dec(base_price * sold) - to_dec(refund_amount)
    consumed_component_cost = to_dec(component_unit_cost * attempted)
    non_component_var_cost = to_dec(non_component_var_per_unit * attempted)
    total_variable_expense = to_dec(consumed_component_cost + non_component_var_cost)
    total_operating_expense = to_dec(total_variable_expense + fixed_expense + ad_cost)
    operating_profit = to_dec(revenue - total_operating_expense)
    net_profit = to_dec(operating_profit - interest_expense)

    # Cash rules: components expensed on consumption, cash outflow on restock
    restock_cash_outflow = to_dec(component_unit_cost * restock_units)
    ending_cash = to_dec(
        opening_cash
        + revenue
        - non_component_var_cost
        - fixed_expense
        - ad_cost
        - restock_cash_outflow
        - interest_expense
        - loan_principal_repaid
        - additional_capex
        + new_owner_cash
        + loan_cash
    )

    ending_stock_units = available_stock - attempted
    ending_inventory_value = to_dec(component_unit_cost * ending_stock_units)

    return {
        "month": month_str,
        "date": f"{month_str}-28",
        "requested": int(requested),
        "derived_capacity": derived_capacity,
        "effective_capacity": effective_capacity,
        "capacity_mode": "Fixture Override" if capacity_override is not None else "Normal Resource-Derived",
        "attempted": attempted,
        "failed": failed,
        "sold": sold,
        "unserved_demand": unserved_demand,
        "revenue": float(revenue),
        "consumed_component_cost": float(consumed_component_cost),
        "non_component_var_cost": float(non_component_var_cost),
        "variable_expense": float(total_variable_expense),
        "fixed_expense": float(fixed_expense),
        "ad_cost": float(ad_cost),
        "total_expense": float(total_operating_expense),
        "operating_profit": float(operating_profit),
        "net_profit": float(net_profit),
        "restock_units": int(restock_units),
        "restock_cash_outflow": float(restock_cash_outflow),
        "opening_cash": float(opening_cash),
        "ending_cash": float(ending_cash),
        "opening_stock_units": int(opening_stock_units),
        "ending_stock_units": int(ending_stock_units),
        "ending_inventory_value": float(ending_inventory_value),
    }

def generate_synthetic_experiment(seed: int = 2027) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    group = np.array(["A"] * 40 + ["B"] * 40)
    success = np.r_[rng.permutation([1] * 12 + [0] * 28), rng.permutation([1] * 20 + [0] * 20)]
    df = pd.DataFrame({
        "prospect_id": [f"P{i:03}" for i in range(1, 81)],
        "message": group,
        "converted": success,
    })
    return df.iloc[rng.permutation(80)].reset_index(drop=True)

def get_default_state() -> dict:
    return {
        "team_id": "Coconut",
        "course": "AP Statistics",
        "pathway_id": "ROB-4",
        "selected_level": "Foundation",
        "approved_skills": ["Synthetic Randomized Experiment & Exploratory Data Analysis"],
        "snapshot_id": "SNAP-ROB4-V1",
        "state_version": 1,
        "simulation_date": "2027-01-01",
        "base_period": "monthly",
        "working_days": 22,
        "currency": "USD",
        "random_seed": 2027,
        "funding": {
            "owner_contribution": 12000.00,
            "equipment_assets": 4000.00,
            "pre_opening_expense": 0.00,
            "opening_inventory_value": 3000.00,
            "opening_cash": 5000.00,
            "retained_earnings": 0.00,
            "loan_debt": 0.00,
        },
        "params": {
            "base_price": 120.00,
            "D0": 40,
            "staff_hours": 90.0,
            "hours_per_unit": 3.0,
            "opening_stock_units": 100,
            "component_unit_cost": 30.00,
            "defect_rate": 0.0,
            "var_lines": {
                "components_COGS": 30.00,
                "assembly_labor": 20.00,
                "packaging": 10.00,
                "warranty_consumables": 5.00,
            },
            "fixed_lines": {
                "workspace": 250.00,
                "software": 100.00,
                "equipment_maintenance": 150.00,
                "admin": 100.00,
            },
        },
        "current_cash": 5000.00,
        "current_stock_units": 100,
        "processed_run_ids": [],
        "ledger": [],
        "decisions": [],
    }

if "sim_state" not in st.session_state:
    st.session_state.sim_state = get_default_state()

state = st.session_state.sim_state

# --- SIDEBAR: SNAPSHOT & SAVE/LOAD ---
with st.sidebar:
    st.header("Team Coconut | ROB-4")
    st.caption("Course: AP Statistics | Level: Foundation")
    st.info(f"**Snapshot:** `{state['snapshot_id']}`\n\n**State Version:** `v{state['state_version']}`")

    if st.button("Reset to Opening State (v1)", use_container_width=True):
        st.session_state.sim_state = get_default_state()
        st.rerun()

    st.divider()
    st.subheader("Durable Save / Load JSON")
    snapshot_json = json.dumps(state, indent=2)
    st.download_button(
        label="Export Snapshot JSON",
        data=snapshot_json,
        file_name=f"{state['team_id']}_{state['pathway_id']}_v{state['state_version']}.json",
        mime="application/json",
        use_container_width=True,
    )

    uploaded_file = st.file_uploader("Restore / Import Snapshot JSON", type=["json"])
    if uploaded_file is not None:
        try:
            imported = json.load(uploaded_file)
            required_keys = {"team_id", "course", "pathway_id", "state_version", "params", "funding", "ledger"}
            if not required_keys.issubset(imported.keys()):
                st.error("Import Rejected: Missing required schema fields.")
            elif imported.get("team_id") != "Coconut":
                st.error(f"Import Rejected: Wrong team_id (`{imported.get('team_id')}`). Expected `Coconut`.")
            elif imported.get("pathway_id") != "ROB-4":
                st.error(f"Import Rejected: Wrong pathway_id (`{imported.get('pathway_id')}`). Expected `ROB-4`.")
            elif int(imported.get("state_version", 0)) < int(state["state_version"]):
                st.error(
                    f"Import Rejected (Stale Version): Imported v{imported.get('state_version')} "
                    f"is older than current v{state['state_version']}."
                )
            else:
                st.session_state.sim_state = imported
                st.success(f"Restored snapshot `{imported.get('snapshot_id')}` (v{imported.get('state_version')}).")
                st.rerun()
        except Exception as exc:
            st.error(f"Import Rejected: Invalid JSON ({exc}).")

# --- TOP KPI BAR ---
st.title("Robotics Kit & Repair Studio — Operating Dashboard (Stage 1)")
st.warning(
    "**Stage 1 Build Status:** Core deterministic ledger, inventory/cash accounting, AP Statistics Foundation experiment, "
    "and fixture verification are active. Full Report Center, Costed Marketing Studio, and Assessment Generator unlock in Stages 2-3."
)

col1, col2, col3, col4, col5 = st.columns(5)
p = state["params"]
derived_cap = math.floor(p["staff_hours"] / p["hours_per_unit"])
col1.metric("Current Cash", fmt_usd(state["current_cash"]), delta="Cash Floor: $1,000")
col2.metric("Component Stock", f"{state['current_stock_units']} sets", delta=fmt_usd(state["current_stock_units"] * p["component_unit_cost"]))
col3.metric("Monthly Capacity", f"{derived_cap} kits", delta=f"{p['staff_hours']} hrs @ {p['hours_per_unit']} hr/kit")
col4.metric("Unit Variable Cost", fmt_usd(sum(p["var_lines"].values())))
col5.metric("Monthly Fixed Cost", fmt_usd(sum(p["fixed_lines"].values())))

if state["current_cash"] < 1000:
    st.error("FINANCE ALERT: Cash balance is below the $1,000 ROB safety threshold!")

# --- MAIN TABS ---
tab_overview, tab_inputs, tab_math, tab_ops, tab_fixtures = st.tabs([
    "1. Overview & Ledger",
    "2. Inputs & Funding",
    "3. Math Skills (AP Stats Foundation)",
    "4. Operations & Simulation Run",
    "5. Fixture Acceptance Tests",
])

with tab_overview:
    st.subheader("System Map & Ledger Summary")
    st.markdown(
        "**Operating Flow (Student-Approved):** `Campaign / Demand (D0)` -> `Operations Capacity & Stock Check` -> "
        "`Completed Sales` -> `Income & Cash Ledger` -> `Snapshot Export & Review`"
    )
    if not state["ledger"]:
        st.info("No simulation months recorded yet. Run a month in Tab 4 or replay the official ROB fixture in Tab 5.")
    else:
        df_ledger = pd.DataFrame(state["ledger"])
        st.dataframe(df_ledger, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_ledger["month"], y=df_ledger["revenue"], name="Revenue ($)", marker_color="#2b5c8f"))
        fig.add_trace(go.Bar(x=df_ledger["month"], y=df_ledger["total_expense"], name="Total Expense ($)", marker_color="#d95f02"))
        fig.add_trace(go.Scatter(x=df_ledger["month"], y=df_ledger["operating_profit"], name="Operating Profit ($)", mode="lines+markers", line=dict(color="#1b9e77", width=3)))
        fig.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="Break-Even ($0)")
        fig.update_layout(
            title=f"Actual Simulated Revenue, Expense & Profit ({state['snapshot_id']} | v{state['state_version']})",
            xaxis_title="Simulation Month",
            yaxis_title="USD ($)",
            barmode="group",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab_inputs:
    st.subheader("Startup Financing & Editable ROB Cost Parameters")
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("#### Opening Balance Sheet (Owner Contribution = $12,000)")
        f_data = state["funding"]
        st.table(pd.DataFrame([
            {"Item": "Post-Startup Spendable Cash", "Amount (USD)": fmt_usd(f_data["opening_cash"]), "Classification": "Asset (Cash)"},
            {"Item": "Initial Component Inventory (100 sets @ $30)", "Amount (USD)": fmt_usd(f_data["opening_inventory_value"]), "Classification": "Asset (Inventory)"},
            {"Item": "Tools & Test Equipment", "Amount (USD)": fmt_usd(f_data["equipment_assets"]), "Classification": "Asset (Equipment)"},
            {"Item": "Owner Contribution (Paid-In Equity)", "Amount (USD)": fmt_usd(f_data["owner_contribution"]), "Classification": "Equity (Not Revenue)"},
        ]))
        st.caption("Accounting Rule: Equipment and opening inventory are assets, not expensed again at startup. Components are expensed when consumed.")

    with c_right:
        st.markdown("#### Baseline Operating Inputs (Editable Scenario Parameters)")
        new_price = st.number_input("Base Price ($/kit)", min_value=1.0, value=float(p["base_price"]), step=5.0)
        new_d0 = st.number_input("Baseline Monthly Demand D0 (kits)", min_value=0, value=int(p["D0"]), step=1)
        new_hours = st.number_input("Staff Hours / Month", min_value=0.0, value=float(p["staff_hours"]), step=3.0)
        new_hpu = st.number_input("Hours per Kit", min_value=0.5, value=float(p["hours_per_unit"]), step=0.5)
        new_defect = st.slider("Defect Rate (0.00 to 1.00)", min_value=0.0, max_value=1.0, value=float(p["defect_rate"]), step=0.01)
        if st.button("Apply Parameter Updates (Advances Version)"):
            state["params"]["base_price"] = new_price
            state["params"]["D0"] = new_d0
            state["params"]["staff_hours"] = new_hours
            state["params"]["hours_per_unit"] = new_hpu
            state["params"]["defect_rate"] = new_defect
            state["state_version"] += 1
            state["snapshot_id"] = f"SNAP-ROB4-V{state['state_version']}"
            st.success("Parameters updated and snapshot version incremented.")
            st.rerun()

with tab_math:
    st.subheader("Persistent Math Panel — AP Statistics (Foundation Level)")
    st.markdown(
        """
        - **Course & Level:** AP Statistics | **Foundation** (Teacher-Approved)
        - **Named Skill:** Synthetic Randomized Invitation Experiment & Exploratory Distribution Analysis
        - **Business Question:** Does Message B yield a higher conversion proportion than Message A among 80 fictional robotics kit prospects, and how do center, spread, and outliers behave?
        - **Variables & Domain:** Explanatory = `message` (`A` or `B`, $n_A=40, n_B=40$); Response = `converted` ($1 = \text{purchase conversion}$, $0 = \text{no conversion}$).
        - **Crucial Limitation:** These 80 rows are **synthetic simulation data**, NOT actual market evidence. Do NOT auto-change $D_0$ based on this experiment.
        """
    )

    exp_df = generate_synthetic_experiment(state["random_seed"])
    summary_rows = []
    for grp in ["A", "B"]:
        sub = exp_df[exp_df["message"] == grp]["converted"]
        summary_rows.append({
            "Message Group": f"Message {grp}",
            "Count (n)": len(sub),
            "Successes (1)": int(sub.sum()),
            "Failures (0)": int((1 - sub).sum()),
            "Sample Proportion (p_hat / Mean)": round(float(sub.mean()), 4),
            "Median": round(float(sub.median()), 2),
            "IQR": round(float(sub.quantile(0.75) - sub.quantile(0.25)), 2),
            "Sample Std Dev (s)": round(float(sub.std(ddof=1)), 4),
        })
    summary_df = pd.DataFrame(summary_rows)
    p_a = summary_df.loc[0, "Sample Proportion (p_hat / Mean)"]
    p_b = summary_df.loc[1, "Sample Proportion (p_hat / Mean)"]

    st.table(summary_df)
    st.metric("Observed Difference in Conversion Proportions (p_B - p_A)", f"{p_b - p_a:+.4f} (+20.0 percentage points)")

    fig_exp = px.bar(
        summary_df,
        x="Message Group",
        y=["Successes (1)", "Failures (0)"],
        barmode="group",
        title="AP Statistics Foundation: Synthetic Randomized Experiment Outcomes (n = 80)",
        labels={"value": "Number of Fictional Prospects", "variable": "Outcome"},
        color_discrete_sequence=["#1b9e77", "#7570b3"],
    )
    fig_exp.update_yaxes(range=[0, 35])
    st.plotly_chart(fig_exp, use_container_width=True)

    with st.expander("Transfer Check & Student Interpretation Prompts"):
        st.markdown(
            "1. **Why does Message A have a median of 0 while Message B has a median of 0.5?** (Hint: Check the 20th and 21st ordered values in each group of 40.)\n"
            "2. **Are there any unusual observations (outliers)?** Why or why not for a binary variable on {0, 1}?\n"
            "3. **Why can we draw a causal conclusion within the simulation, yet NOT generalize to real-world robotics buyers?**"
        )

with tab_ops:
    st.subheader("Execute Single Simulation Month (Duplicate-Run Protected)")
    st.markdown(
        "**Exact ROB Fulfillment Algorithm:**  \n"
        "`capacity = floor(staff_hours / hours_per_unit)`  \n"
        "`attempted = min(requested, capacity, opening_stock_units + restock_units)`  \n"
        "`failed = floor(attempted * defect_rate)`  \n"
        "`sold = attempted - failed`"
    )
    with st.form("run_month_form"):
        c1, c2, c3 = st.columns(3)
        run_id = c1.text_input("Unique Run ID", value=f"RUN-2027-{len(state['ledger']) + 1:02d}")
        sim_month = c2.text_input("Simulation Month (YYYY-MM)", value=f"2027-{len(state['ledger']) + 1:02d}")
        req_units = c3.number_input("Requested Demand (kits)", min_value=0, value=int(p["D0"]), step=1)

        c4, c5, c6 = st.columns(3)
        restock_qty = c4.number_input("Restock Component Sets Purchased", min_value=0, value=0, step=10)
        ad_spend = c5.number_input("Approved Own-Business Marketing ($)", min_value=0.0, value=0.0, step=25.0)
        override_cap = c6.checkbox("Enable Fixture Capacity Override?", value=False)
        cap_val = st.number_input("Capacity Override (only if checked)", min_value=0, value=30, step=1)

        submitted = st.form_submit_button("Approve & Advance Simulation One Month")
        if submitted:
            if run_id in state["processed_run_ids"]:
                st.error(f"Duplicate Run Rejected: `run_id` `{run_id}` has already been executed.")
            else:
                var_non_comp = to_dec(sum(p["var_lines"].values()) - p["var_lines"]["components_COGS"])
                step_res = compute_month_step(
                    month_str=sim_month,
                    requested=int(req_units),
                    base_price=to_dec(p["base_price"]),
                    staff_hours=float(p["staff_hours"]),
                    hours_per_unit=float(p["hours_per_unit"]),
                    opening_stock_units=int(state["current_stock_units"]),
                    component_unit_cost=to_dec(p["component_unit_cost"]),
                    restock_units=int(restock_qty),
                    defect_rate=float(p["defect_rate"]),
                    non_component_var_per_unit=var_non_comp,
                    fixed_expense=to_dec(sum(p["fixed_lines"].values())),
                    ad_cost=to_dec(ad_spend),
                    opening_cash=to_dec(state["current_cash"]),
                    capacity_override=int(cap_val) if override_cap else None,
                )
                step_res["run_id"] = run_id
                state["ledger"].append(step_res)
                state["processed_run_ids"].append(run_id)
                state["current_cash"] = step_res["ending_cash"]
                state["current_stock_units"] = step_res["ending_stock_units"]
                state["state_version"] += 1
                state["snapshot_id"] = f"SNAP-ROB4-V{state['state_version']}"
                st.success(f"Month {sim_month} committed (`{run_id}`). Sold {step_res['sold']} kits; Unserved demand: {step_res['unserved_demand']}.")
                st.rerun()

with tab_fixtures:
    st.subheader("Official ROB Package Fixture & Acceptance Verification (Page 80)")
    st.warning("Fixture Mode uses explicit `capacity_override` values from `sample_data/monthly_fixture.csv` to verify ledger math.")

    expected_df = pd.DataFrame([
        {"Month": "2027-01", "Sold": 30, "Revenue": 3600.0, "Total expense": 2550.0, "Profit": 1050.0, "Closing cash": 6950.0, "Closing stock": 70},
        {"Month": "2027-02", "Sold": 30, "Revenue": 3600.0, "Total expense": 2650.0, "Profit": 950.0, "Closing cash": 8800.0, "Closing stock": 40},
        {"Month": "2027-03", "Sold": 22, "Revenue": 2640.0, "Total expense": 2030.0, "Profit": 610.0, "Closing cash": 10070.0, "Closing stock": 18},
    ])

    if st.button("Reset & Replay Official 3-Month ROB Fixture"):
        fresh = get_default_state()
        fixture_rows = pd.read_csv("sample_data/monthly_fixture.csv")
        cash = to_dec(fresh["funding"]["opening_cash"])
        stock = int(fresh["params"]["opening_stock_units"])
        var_non_comp = Decimal("35.00")
        fixed_exp = Decimal("600.00")

        actual_rows = []
        for idx, row in fixture_rows.iterrows():
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
                non_component_var_per_unit=var_non_comp,
                fixed_expense=fixed_exp,
                ad_cost=to_dec(row["ad_cost"]),
                opening_cash=cash,
                capacity_override=int(row["capacity_override"]),
            )
            res["run_id"] = f"FIXTURE-{row['month']}"
            fresh["ledger"].append(res)
            fresh["processed_run_ids"].append(res["run_id"])
            cash = to_dec(res["ending_cash"])
            stock = res["ending_stock_units"]
            actual_rows.append({
                "Month": res["month"],
                "Sold": res["sold"],
                "Revenue": res["revenue"],
                "Total expense": res["total_expense"],
                "Profit": res["operating_profit"],
                "Closing cash": res["ending_cash"],
                "Closing stock": res["ending_stock_units"],
            })

        fresh["current_cash"] = float(cash)
        fresh["current_stock_units"] = stock
        fresh["state_version"] = 4
        fresh["snapshot_id"] = "SNAP-ROB4-FIXTURE-V4"
        st.session_state.sim_state = fresh

        actual_df = pd.DataFrame(actual_rows)
        st.markdown("#### Actual Replay Output vs. Handbook Expected Table")
        st.dataframe(actual_df, use_container_width=True)
        if actual_df.equals(expected_df):
            st.success("PASS: All 3 months match the exact handbook fixture values ($0.00 variance)!")
        else:
            st.error("FAIL: Output diverged from expected table.")
