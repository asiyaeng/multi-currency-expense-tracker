# app.py
import streamlit as st
from datetime import datetime
import pandas as pd
import plotly.express as px
from models import init_db
import db as dbm
import currency
import utils
import auth

st.set_page_config(page_title='Multi-Currency Expense Tracker', layout='wide')
init_db()

# session defaults
if 'user' not in st.session_state:
    st.session_state.user = None
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# --- Auth UI in sidebar ---
st.sidebar.header('Account')
if st.session_state.user:
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.user['username']}")
    if st.sidebar.button('Logout'):
        st.session_state.user = None
        st.experimental_rerun()
else:
    auth_mode = st.sidebar.radio('Choose', ['Login', 'Register'])
    if auth_mode == 'Login':
        uname = st.sidebar.text_input('Username', key='login_user')
        pwd = st.sidebar.text_input('Password', type='password', key='login_pwd')
        if st.sidebar.button('Login'):
            ok, res = auth.authenticate_user(uname, pwd)
            if ok:
                st.session_state.user = res
                st.success('Logged in')
                st.experimental_rerun()
            else:
                st.error(res)
    else:
        uname = st.sidebar.text_input('Choose username', key='reg_user')
        pwd = st.sidebar.text_input('Choose password', type='password', key='reg_pwd')
        if st.sidebar.button('Register'):
            ok, err = auth.register_user(uname, pwd)
            if ok:
                st.success('Registered — please log in')
            else:
                st.error(f'Registration error: {err}')

if not st.session_state.user:
    st.title('Please log in or register to use the Expense Tracker')
    st.stop()

USER_ID = st.session_state.user['id']

# settings
st.sidebar.header('Settings')
base_currency = st.sidebar.selectbox('Base currency', options=currency.available_currencies(base='USD'))
st.sidebar.markdown('---')

st.title('💸 Multi-Currency Expense Tracker')

# --- Tabs for navigation ---
tab1, tab2, tab3 = st.tabs(["Expenses", "Reports", "Profile Settings"])

# ======================
# Tab 1: Expenses
# ======================
with tab1:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header('Add / Edit Expense')
        edit_id = st.session_state.get('edit_id', None)
        if edit_id:
            rec = dbm.get_expense(edit_id, USER_ID)
            if rec:
                default_amount = rec['amount']
                default_currency = rec['currency']
                default_category = rec['category'] or 'General'
                default_date = pd.to_datetime(rec['date']).date()
                default_notes = rec['notes'] or ''
            else:
                st.session_state.edit_id = None
                default_amount = 0.0
                default_currency = base_currency
                default_category = 'General'
                default_date = datetime.today().date()
                default_notes = ''
        else:
            default_amount = 0.0
            default_currency = base_currency
            default_category = 'General'
            default_date = datetime.today().date()
            default_notes = ''

        with st.form('expense_form', clear_on_submit=False):
            amount = st.number_input('Amount', min_value=0.0, format='%f', value=float(default_amount))
            currency_input = st.selectbox('Currency', options=currency.available_currencies(base=base_currency))
            category = st.text_input('Category', value=default_category)
            date = st.date_input('Date', value=default_date)
            notes = st.text_area('Notes', height=80, value=default_notes)
            submitted = st.form_submit_button('Save')

            if submitted:
                try:
                    converted = currency.convert_amount(amount, currency_input, base_currency)
                except Exception as e:
                    st.error(f'Error converting currency: {e}')
                else:
                    if edit_id:
                        dbm.update_expense(edit_id, USER_ID, amount, currency_input, converted,
                                           base_currency, category, date.isoformat(), notes)
                        st.success('Expense updated')
                        st.session_state.edit_id = None
                        st.experimental_rerun()
                    else:
                        dbm.add_expense(USER_ID, amount, currency_input, converted,
                                        base_currency, category, date.isoformat(), notes)
                        st.success('Expense added')
                        st.experimental_rerun()

    with col2:
        st.header('Expenses')
        expenses = dbm.list_expenses(USER_ID)
        df = utils.expenses_to_df(expenses)

        st.subheader('Filters')
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            cat_options = ['All'] + sorted(df['category'].dropna().unique().tolist()) if not df.empty else ['All']
            cat_filter = st.selectbox('Category', options=cat_options)
        with c2:
            if df.empty:
                start_date = datetime.today().date().replace(day=1)
                end_date = datetime.today().date()
            else:
                start_date = df['date'].min().date()
                end_date = df['date'].max().date()
            date_range = st.date_input('Date range', value=(start_date, end_date))
        with c3:
            search = st.text_input('Search notes')

        filtered = df.copy()
        if not df.empty:
            if cat_filter and cat_filter != 'All':
                filtered = filtered[filtered['category'] == cat_filter]
            try:
                start, end = date_range
            except Exception:
                start = date_range
                end = date_range
            filtered = filtered[(filtered['date'] >= pd.to_datetime(start)) & (filtered['date'] <= pd.to_datetime(end))]
            if search:
                filtered = filtered[filtered['notes'].str.contains(search, case=False, na=False)]

        st.write(f"Showing {len(filtered)} expenses")

        if not filtered.empty:
            display_df = filtered.copy()
            display_df['date'] = display_df['date'].dt.date
            display_df = display_df.sort_values('date', ascending=False)
            st.dataframe(display_df[['id', 'date', 'category', 'amount', 'currency',
                                     'converted_amount', 'base_currency', 'notes']])

            st.write('Actions')
            for _, row in display_df.iterrows():
                cols = st.columns([1, 1, 4, 1, 1])
                cols[0].write(f"ID: {int(row['id'])}")
                cols[1].write(f"{row['date']}")
                cols[2].write(f"{row['category']} — {str(row['notes'])[:60]}")
                if cols[3].button('Edit', key=f"edit_{int(row['id'])}"):
                    st.session_state.edit_id = int(row['id'])
                    st.experimental_rerun()
                if cols[4].button('Delete', key=f"del_{int(row['id'])}"):
                    dbm.delete_expense(int(row['id']), USER_ID)
                    st.success('Deleted')
                    st.experimental_rerun()
        else:
            st.info('No expenses found for selected filters')

# ======================
# Tab 2: Reports
# ======================
with tab2:
    st.header('Reports')
    expenses = dbm.list_expenses(USER_ID)
    df = utils.expenses_to_df(expenses)

    s_by_month = utils.summarize_by_month(df)
    s_by_cat = utils.summarize_by_category(df)

    st.subheader('Spending by month')
    if not s_by_month.empty:
        fig = px.line(s_by_month, x='month', y='converted_amount',
                      title='Monthly spending',
                      labels={'converted_amount': f'Amount ({base_currency})'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write('No monthly data')

    st.subheader('Spending by category')
    if not s_by_cat.empty:
        fig2 = px.pie(s_by_cat, values='converted_amount', names='category',
                      title='Category breakdown')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write('No category data')

    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button('Export CSV', csv,
                           file_name=f'expenses_{datetime.today().date()}.csv',
                           mime='text/csv')

# ======================
# Tab 3: Profile Settings
# ======================
with tab3:
    st.header("Profile Settings")

    # --- Change Password ---
    with st.expander("🔑 Change Password", expanded=True):
        with st.form("change_pw_form"):
            old_pw = st.text_input("Old Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Change Password")

            if submitted:
                if new_pw != confirm_pw:
                    st.error("New passwords do not match.")
                else:
                    ok, err = auth.change_password(USER_ID, old_pw, new_pw)
                    if ok:
                        st.success("Password updated successfully. Please log in again.")
                        st.session_state.user = None
                        st.experimental_rerun()
                    else:
                        st.error(err)

    # --- Delete Account ---
    with st.expander("⚠️ Delete Account"):
        st.warning("This action will **permanently delete your account and all expenses**. This cannot be undone.")

        # Export data first
        expenses = dbm.list_expenses(USER_ID)
        df_export = utils.expenses_to_df(expenses)
        if not df_export.empty:
            csv = df_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download My Expenses (CSV)",
                data=csv,
                file_name=f"expenses_backup_user{USER_ID}.csv",
                mime="text/csv"
            )
        else:
            st.info("No expenses found to export.")

        st.markdown("---")
        confirm = st.checkbox("I understand the consequences", key="confirm_delete")
        if st.button("Delete My Account", type="primary", disabled=not confirm):
            dbm.delete_all_expenses(USER_ID)  # remove all user expenses
            auth.delete_user(USER_ID)         # remove user account
            st.success("Your account and all expenses have been deleted.")
            st.session_state.user = None
            st.experimental_rerun()
