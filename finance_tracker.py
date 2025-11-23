import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os
import re
import numpy as np
import easyocr

DB_FILE = "expenses_data.json"
MAX_WIDTH = 1000


def resize_for_ocr(image):
    w, h = image.size
    if w > MAX_WIDTH:
        image = image.resize((MAX_WIDTH, int(h * MAX_WIDTH / w)))
    return image


def load_expenses():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_expenses():
    with open(DB_FILE, "w") as f:
        json.dump(st.session_state.expenses, f, indent=2)


def add_expense(description, amount, category, date, source="manual"):
    expense = {
        "id": datetime.now().timestamp(),
        "description": description,
        "amount": float(amount),
        "category": category,
        "date": date.strftime("%Y-%m-%d"),
        "source": source,
    }
    st.session_state.expenses.append(expense)
    save_expenses()


def delete_expense(expense_id):
    st.session_state.expenses = [e for e in st.session_state.expenses if e["id"] != expense_id]
    save_expenses()


def get_expenses_df():
    if not st.session_state.expenses:
        return pd.DataFrame()
    df = pd.DataFrame(st.session_state.expenses)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date", ascending=False)


def calculate_statistics():
    if not st.session_state.expenses:
        return {"total": 0, "month": 0, "avg_daily": 0, "count": 0}
    df = get_expenses_df()
    total = df["amount"].sum()
    now = datetime.now()
    month_total = df[
        (df["date"].dt.year == now.year) & (df["date"].dt.month == now.month)
        ]["amount"].sum()
    days = df["date"].dt.date.nunique()
    avg_daily = total / days if days else 0
    return {
        "total": round(total, 2),
        "month": round(month_total, 2),
        "avg_daily": round(avg_daily, 2),
        "count": len(df),
    }


def parse_receipt_text(text: str):
    lines = [x.strip() for x in text.strip().split('\n') if x.strip()]
    items = []
    i = 0
    while i < len(lines) - 1:
        desc, price_line = lines[i], lines[i + 1]
        try:
            price = float(price_line.replace("$", "").replace("S", "").replace(",", ""))
            if any(desc.lower().startswith(x) for x in ["total", "amount", "change", "cash"]):
                i += 1
                continue
            items.append({"description": desc, "amount": round(price, 2)})
            i += 2
            continue
        except ValueError:
            pass
        i += 1
    if not items:
        price_patterns = [r"(\d+\.\d{2})", r"(\d+,\d{2})", r"\b(\d+)\b"]
        for line in lines:
            for pattern in price_patterns:
                matches = re.findall(pattern, line)
                if matches:
                    price_str = matches[-1]
                    try:
                        price = float(price_str.replace(",", ""))
                        desc = re.sub(pattern, "", line).strip()
                        if desc and len(desc) > 1:
                            items.append({"description": desc[:50], "amount": round(price, 2)})
                        break
                    except ValueError:
                        continue
    total = 0.0
    for line in lines:
        if 'total' in line.lower():
            parts = re.findall(r"\d+[\.,]?\d*", line)
            if parts:
                total = float(parts[-1].replace(",", "").replace("S", ""))
                break
    return {"items": items, "total": round(total, 2)}


@st.cache_resource
def get_easyocr_reader():
    return easyocr.Reader(["en"], gpu=False)


def perform_ocr_easyocr(image: Image.Image):
    try:
        reader = get_easyocr_reader()
        image = resize_for_ocr(image)
        arr = np.array(image)
        res = reader.readtext(arr)
        text = "\n".join(r[1] for r in res)
        if not text.strip():
            return None, "EasyOCR: No text detected"
        return text, None
    except Exception as e:
        return None, f"EasyOCR Error: {e}"


# Initialize session state
if "expenses" not in st.session_state:
    st.session_state.expenses = load_expenses()

if "parsed_items" not in st.session_state:
    st.session_state.parsed_items = []

st.set_page_config(page_title="Finance Tracker", page_icon="💰", layout="wide")
st.title("💰 Finance Tracker")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📸 Scan Bill", "✍️ Manual Entry", "📊 Expenses", "📈 Statistics"]
)

# TAB 1: Scan Bill
with tab1:
    st.header("Scan Receipt/Bill")
    st.info("💡 Option 1: Paste receipt text (no OCR needed)")
    manual_text = st.text_area("Paste receipt text here:", height=120)
    if manual_text and st.button("📝 Parse Text"):
        parsed = parse_receipt_text(manual_text)
        if parsed["items"]:
            st.session_state.parsed_items = parsed["items"]
            st.success(f"Found {len(parsed['items'])} items - Review and edit below")
            st.rerun()
        else:
            st.warning("No items found in text")

    st.divider()
    st.info("💡 Option 2: Upload receipt image (EasyOCR)")

    uploaded = st.file_uploader("Upload receipt image", type=["png", "jpg", "jpeg"])
    if uploaded is not None:
        img = Image.open(uploaded)
        c1, c2 = st.columns(2)
        with c1:
            st.image(img, caption="Uploaded Receipt", use_container_width=True)
        with c2:
            if st.button("🔍 Extract with EasyOCR"):
                with st.spinner("Processing with EasyOCR..."):
                    text, err = perform_ocr_easyocr(img)
                    if err:
                        st.error(err)
                    elif text:
                        with st.expander("Raw Extracted Text"):
                            st.text(text)
                        parsed = parse_receipt_text(text)
                        if parsed["items"]:
                            st.session_state.parsed_items = parsed["items"]
                            st.success(f"Found {len(parsed['items'])} items - Review and edit below")
                            st.rerun()
                        else:
                            st.warning("No items parsed from OCR text")

    # Show editable items if any parsed
    if st.session_state.parsed_items:
        st.divider()
        st.subheader("📋 Review & Edit Parsed Items")
        st.info("Edit description, amount, and category for each item, then save selected ones")

        with st.form("parsed_items_form"):
            items_to_save = []
            for idx, item in enumerate(st.session_state.parsed_items):
                st.markdown(f"**Item {idx + 1}**")
                cols = st.columns([3, 2, 2, 1])

                with cols[0]:
                    desc = st.text_input(
                        "Description",
                        value=item["description"],
                        key=f"desc_{idx}",
                        label_visibility="collapsed"
                    )

                with cols[1]:
                    amt = st.number_input(
                        "Amount",
                        value=float(item["amount"]),
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                        key=f"amt_{idx}",
                        label_visibility="collapsed"
                    )

                with cols[2]:
                    cat = st.selectbox(
                        "Category",
                        ["food", "transport", "utilities", "entertainment", "other"],
                        key=f"cat_{idx}",
                        label_visibility="collapsed"
                    )

                with cols[3]:
                    include = st.checkbox("✓", value=True, key=f"inc_{idx}")

                if include:
                    items_to_save.append({
                        "description": desc,
                        "amount": amt,
                        "category": cat
                    })

                st.divider()

            col1, col2 = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button("💾 Save Selected Items", type="primary")
            with col2:
                if st.form_submit_button("🗑️ Clear All"):
                    st.session_state.parsed_items = []
                    st.rerun()

            if submitted and items_to_save:
                today = datetime.now()
                for item in items_to_save:
                    add_expense(
                        item["description"],
                        item["amount"],
                        item["category"],
                        today,
                        source="ocr"
                    )
                st.session_state.parsed_items = []
                st.success(f"✅ Saved {len(items_to_save)} expenses!")
                st.rerun()

# TAB 2: Manual Entry
with tab2:
    st.header("Add Expense Manually")
    with st.form("manual_form"):
        c1, c2 = st.columns(2)
        with c1:
            desc = st.text_input("Description*")
            amt = st.number_input("Amount (₹)*", min_value=0.0, step=0.01, format="%.2f")
        with c2:
            cat = st.selectbox(
                "Category*",
                ["", "food", "transport", "utilities", "entertainment", "other"],
            )
            date = st.date_input("Date", value=datetime.now())
        submitted = st.form_submit_button("➕ Add Expense")
        if submitted:
            if not desc:
                st.error("Enter description")
            elif amt <= 0:
                st.error("Enter valid amount")
            elif not cat:
                st.error("Select category")
            else:
                add_expense(desc, amt, cat, date, source="manual")
                st.success("Expense added")
                st.rerun()

# TAB 3: Expenses
with tab3:
    st.header("Recent Expenses")
    df = get_expenses_df()
    if df.empty:
        st.info("No expenses yet")
    else:
        c1, c2 = st.columns(2)
        with c1:
            cat_filter = st.multiselect(
                "Filter by Category",
                ["food", "transport", "utilities", "entertainment", "other"],
            )
        with c2:
            src_filter = st.multiselect("Filter by Source", ["manual", "ocr"])
        fdf = df.copy()
        if cat_filter:
            fdf = fdf[fdf["category"].isin(cat_filter)]
        if src_filter:
            fdf = fdf[fdf["source"].isin(src_filter)]
        st.write(f"Showing {len(fdf)} of {len(df)} expenses")
        for _, row in fdf.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 2, 1])
            with c1:
                st.write(f"**{row['description']}**")
            with c2:
                cat_emoji = {
                    "food": "🍔", "transport": "🚗",
                    "utilities": "💡", "entertainment": "🎬", "other": "📦"
                }
                st.write(f"{cat_emoji.get(row['category'], '📦')} {row['category']}")
            with c3:
                st.write(f"₹{row['amount']:.2f}")
            with c4:
                icon = "📷" if row["source"] == "ocr" else "✍️"
                st.write(f"{row['date'].strftime('%Y-%m-%d')} {icon}")
            with c5:
                 if st.button("🗑️", key=f"del_{row['id']}_{_}"):
                    delete_expense(row["id"])
                    st.rerun()

# TAB 4: Statistics
with tab4:
    st.header("Expense Statistics")
    stats = calculate_statistics()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total", f"₹{stats['total']:.2f}")
    with c2:
        st.metric("This Month", f"₹{stats['month']:.2f}")
    with c3:
        st.metric("Avg / Day", f"₹{stats['avg_daily']:.2f}")
    with c4:
        st.metric("Transactions", stats["count"])
    if not st.session_state.expenses:
        st.info("Add expenses to see charts")
    else:
        df = get_expenses_df()
        c1, c2 = st.columns(2)
        with c1:
            cat_data = df.groupby("category")["amount"].sum().reset_index()
            cat_data["category"] = cat_data["category"].map(
                {
                    "food": "🍔 Food",
                    "transport": "🚗 Transport",
                    "utilities": "💡 Utilities",
                    "entertainment": "🎬 Entertainment",
                    "other": "📦 Other",
                }
            )
            fig = px.pie(cat_data, values="amount", names="category", hole=0.4, title="Expenses by Category")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            src_data = df.groupby("source")["amount"].sum().reset_index()
            src_data["source"] = src_data["source"].map(
                {"manual": "✍️ Manual", "ocr": "📷 OCR Scanned"}
            )
            fig2 = px.bar(src_data, x="source", y="amount", title="Expenses by Source")
            st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.caption("💰 Finance Tracker | Each item categorized individually | Data: expenses_data.json")
