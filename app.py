import streamlit as st
from decimal import Decimal, getcontext, InvalidOperation
import db
from services import repository
from services import conversion
import pandas as pd
from datetime import datetime

getcontext().prec = 28


def setup():
    db.init_db()
    db.seed_common_currencies()


setup()

if "pivot" not in st.session_state:
    st.session_state.pivot = "USD"
if "decimals" not in st.session_state:
    st.session_state.decimals = 2

st.sidebar.title("Money Converter")
page = st.sidebar.selectbox("Navigate", ["Convert", "Currencies", "Rates", "History", "Settings"])


def fmt(d: Decimal) -> str:
    q = Decimal(10) ** -st.session_state.decimals
    return str(d.quantize(q))


if page == "Convert":
    st.header("Currency Converter")
    currencies = repository.list_currencies(active_only=True)
    codes = [c.code for c in currencies]

    # ensure session keys exist
    if "from" not in st.session_state:
        st.session_state["from"] = codes[0] if codes else ""
    if "to" not in st.session_state:
        st.session_state["to"] = codes[1] if len(codes) > 1 else (codes[0] if codes else "")

    def _swap():
        a = st.session_state.get("from")
        b = st.session_state.get("to")
        st.session_state["from"] = b
        st.session_state["to"] = a

    col1, col2 = st.columns([2, 1])
    with col1:
        from_currency = st.selectbox("From", codes, index=codes.index(st.session_state["from"]) if st.session_state["from"] in codes else 0, key="from")
        to_currency = st.selectbox("To", codes, index=codes.index(st.session_state["to"]) if st.session_state["to"] in codes else (1 if len(codes) > 1 else 0), key="to")
        amount_str = st.text_input("Amount", "1")
    with col2:
        st.button("Swap", on_click=_swap)

    try:
        amount = Decimal(amount_str)
    except (InvalidOperation, ValueError):
        st.error("Invalid amount")
        amount = None

    if st.button("Convert") and amount is not None:
        if from_currency == to_currency:
            st.success(f"{fmt(amount)} {from_currency} = {fmt(amount)} {to_currency} (same currency)")
        else:
            try:
                result, rate_used, method = conversion.convert(amount, from_currency, to_currency, pivot=st.session_state.pivot)
                repository.log_conversion(from_currency, to_currency, amount, result, rate_used, method)
                st.write("Rate used:", rate_used)
                st.write("Method:", method)
                st.success(f"{fmt(amount)} {from_currency} = {fmt(result)} {to_currency}")
            except Exception as e:
                st.error(str(e))

elif page == "Currencies":
    st.header("Manage Currencies")
    st.subheader("Add / Edit")
    with st.form("currency_form"):
        code = st.text_input("Code (uppercase)")
        name = st.text_input("Name")
        symbol = st.text_input("Symbol (optional)")
        active = st.checkbox("Active", value=True)
        submitted = st.form_submit_button("Save")
        if submitted:
            if not code or not name:
                st.error("Code and name required")
            else:
                repository.upsert_currency(code.upper(), name, symbol or None, active)
                st.success("Saved")

    st.subheader("Existing")
    currencies = repository.list_currencies()
    if currencies:
        rows = [[c.code, c.name, c.symbol or "", "Yes" if c.active else "No"] for c in currencies]
        df = pd.DataFrame(rows, columns=["Code", "Name", "Symbol", "Active"])
        st.dataframe(df)
        del_code = st.text_input("Delete currency code")
        if st.button("Delete") and del_code:
            repository.delete_currency(del_code)
            st.success("Deleted")
    else:
        st.info("No currencies")

elif page == "Rates":
    st.header("Manage Rates")
    st.subheader("Add / Update Rate")
    currencies = [c.code for c in repository.list_currencies(active_only=True)]
    with st.form("rate_form"):
        base = st.selectbox("Base", currencies)
        quote = st.selectbox("Quote", currencies, index=1 if len(currencies) > 1 else 0)
        rate_str = st.text_input("Rate (quote per base)")
        eff = st.date_input("Effective date")
        submitted = st.form_submit_button("Save Rate")
        if submitted:
            if base == quote:
                st.error("Base and quote must differ")
            else:
                try:
                    r = Decimal(rate_str)
                    if r <= 0:
                        raise ValueError()
                    repository.upsert_rate(base, quote, r, eff.isoformat())
                    st.success("Rate saved")
                except Exception:
                    st.error("Invalid rate")

    st.subheader("Existing Rates")
    rates = repository.list_rates()
    if rates:
        rows = [[r.base_currency, r.quote_currency, str(r.rate), r.effective_date] for r in rates]
        df = pd.DataFrame(rows, columns=["Base", "Quote", "Rate", "Effective Date"])
        st.dataframe(df)
        del_base = st.text_input("Delete base currency code")
        del_quote = st.text_input("Delete quote currency code")
        if st.button("Delete Rate") and del_base and del_quote:
            repository.delete_rate(del_base, del_quote)
            st.success("Deleted")
    else:
        st.info("No rates available")

elif page == "History":
    st.header("Conversion History")
    hist = repository.get_history(50)
    if hist:
        rows = [[h.timestamp, h.base_currency, h.quote_currency, str(h.amount), str(h.result), str(h.rate_used), h.method] for h in hist]
        df = pd.DataFrame(rows, columns=["Timestamp", "Base", "Quote", "Amount", "Result", "Rate", "Method"])
        st.dataframe(df)
        if st.button("Clear History"):
            # simple clear by deleting rows
            conn = db.get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM history")
            conn.commit()
            conn.close()
            st.success("History cleared")
    else:
        st.info("No history yet")

elif page == "Settings":
    st.header("Settings")
    currencies = [c.code for c in repository.list_currencies()]
    pivot = st.selectbox("Pivot currency (used for cross conversions)", currencies, index=currencies.index(st.session_state.pivot) if st.session_state.pivot in currencies else 0)
    decimals = st.number_input("Rounding decimals", min_value=0, max_value=8, value=st.session_state.decimals)
    if st.button("Save Settings"):
        st.session_state.pivot = pivot
        st.session_state.decimals = int(decimals)
        st.success("Settings saved")
