from __future__ import annotations







import logging
import re



import html as _html



from datetime import date, datetime, timezone, timedelta



from time import monotonic



import os



import hashlib



import json



from typing import Any







import pandas as pd



import requests



import streamlit as st



from requests.adapters import HTTPAdapter



from urllib3.util.retry import Retry







# ============================================================



# CONFIG



# ============================================================







GOOGLE_SCRIPT_URL = os.getenv("TIFFIN_SCRIPT_URL", "https://script.google.com/macros/s/AKfycbyaei39szCybKrAf7khvOOgKvRI0AyN83WJK0gh0bNiK6jY6NAc5QYgIPb3iEUCht1y/exec")



APP_VERSION = "V20-DATE-TIMEZONE-FIX"



REQUEST_TIMEOUT = 12







st.set_page_config(



    page_title="MegaServe Tiffin",



    page_icon="🍱",



    layout="wide",



    initial_sidebar_state="collapsed",



)







logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")



log = logging.getLogger("tiffin_v15")











INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def india_today() -> date:
    """India calendar date, independent of Streamlit server timezone."""
    return datetime.now(INDIA_TIMEZONE).date()


class AppError(Exception):



    """Expected application/backend error."""











# ============================================================



# MODERN, THEME-SAFE, MOBILE-ADAPTIVE UI



# ============================================================







st.markdown("""



<style>



@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');







:root{



  --ms-primary:#6C5CE7;



  --ms-blue:#0984E3;



  --ms-green:#00B894;



  --ms-red:#E17055;



  --ms-grad:linear-gradient(135deg,#6C5CE7 0%,#0984E3 55%,#00B894 100%);



  --ms-border:rgba(128,128,128,.20);



  --ms-surface:rgba(128,128,128,.06);



  --ms-surface-2:rgba(128,128,128,.10);



  --ms-shadow:0 10px 30px rgba(17,24,39,.08);



  --ms-radius:18px;



}







/* ---------- Base ---------- */



html, body, .stApp, .stMarkdown, button, input, textarea, label, select{



  font-family:'Plus Jakarta Sans', system-ui, -apple-system, 'Segoe UI', sans-serif !important;



}



.stApp{



  background-image:



    radial-gradient(900px 420px at 0% -10%, rgba(108,92,231,.10), transparent 60%),



    radial-gradient(700px 380px at 100% 0%, rgba(0,184,148,.08), transparent 60%);



  background-attachment:fixed;



}



.block-container, [data-testid="stMainBlockContainer"]{



  max-width:1280px;



  padding-top:1.4rem !important;



  padding-bottom:3rem !important;



}



#MainMenu, footer{visibility:hidden;}



header[data-testid="stHeader"]{background:transparent;}







@keyframes fadeUp{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:none;}}







/* ---------- Hero ---------- */



.hero{



  position:relative;overflow:hidden;



  padding:30px 34px;border-radius:24px;margin-bottom:22px;



  background:var(--ms-grad);



  box-shadow:0 18px 40px rgba(108,92,231,.28);



  animation:fadeUp .45s ease both;



}



.hero::before,.hero::after{



  content:"";position:absolute;border-radius:50%;



  background:rgba(255,255,255,.12);pointer-events:none;



}



.hero::before{width:260px;height:260px;right:-70px;top:-110px;}



.hero::after{width:160px;height:160px;right:120px;bottom:-90px;background:rgba(255,255,255,.08);}



.hero h1,.hero p,.hero span{color:#fff !important;margin:0;position:relative;z-index:1;}



.hero h1{font-size:2.05rem;font-weight:800;letter-spacing:-.02em;line-height:1.2;}



.hero p{margin-top:6px;font-size:1.02rem;opacity:.92;}



.hero-chip{



  display:inline-block;margin-bottom:10px;padding:4px 12px;border-radius:999px;



  background:rgba(255,255,255,.18);backdrop-filter:blur(6px);



  font-size:.75rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;



}







/* ---------- Section titles ---------- */



.sec{margin:20px 0 12px;}



.sec h3{margin:0;font-size:1.15rem;font-weight:800;letter-spacing:-.01em;



  display:flex;align-items:center;gap:10px;}



.sec h3::before{content:"";width:5px;height:20px;border-radius:4px;background:var(--ms-grad);}



.sec p{margin:4px 0 0 15px;opacity:.65;font-size:.9rem;}







/* ---------- Metrics ---------- */



div[data-testid="stMetric"]{



  position:relative;overflow:hidden;



  background:var(--ms-surface);



  border:1px solid var(--ms-border);



  border-radius:var(--ms-radius);



  padding:18px 20px 16px;



  transition:transform .18s ease, box-shadow .18s ease;



  animation:fadeUp .45s ease both;



}



div[data-testid="stMetric"]::before{



  content:"";position:absolute;left:0;right:0;top:0;height:4px;background:var(--ms-grad);



}



div[data-testid="stMetric"]:hover{transform:translateY(-3px);box-shadow:var(--ms-shadow);}



[data-testid="stMetricLabel"] p{



  font-size:.78rem !important;font-weight:700 !important;opacity:.65;



  text-transform:uppercase;letter-spacing:.06em;



}



[data-testid="stMetricValue"]{font-size:1.75rem !important;font-weight:800 !important;letter-spacing:-.02em;}







/* ---------- Pill navigation (horizontal radios) ---------- */



div[role="radiogroup"]{



  display:flex;flex-wrap:wrap;gap:6px;



  padding:6px;border-radius:16px;



  background:var(--ms-surface);border:1px solid var(--ms-border);



  scrollbar-width:none;



}



div[role="radiogroup"]::-webkit-scrollbar{display:none;}



div[role="radiogroup"] > label{



  margin:0 !important;padding:9px 16px;border-radius:12px;



  cursor:pointer;white-space:nowrap;



  transition:background .18s ease, transform .12s ease;



}



div[role="radiogroup"] > label:hover{background:var(--ms-surface-2);}



div[role="radiogroup"] > label > div:first-child{display:none;}



div[role="radiogroup"] > label p{font-weight:600;font-size:.92rem;}



div[role="radiogroup"] > label:has(input:checked){



  background:var(--ms-grad);box-shadow:0 6px 16px rgba(108,92,231,.30);



}



div[role="radiogroup"] > label:has(input:checked) p{color:#fff !important;}







/* ---------- Buttons ---------- */



.stButton button, [data-testid="stFormSubmitButton"] button, .stDownloadButton button{



  border-radius:12px !important;font-weight:700 !important;



  min-height:42px;padding:0 18px;



  transition:transform .12s ease, box-shadow .18s ease, filter .18s ease;



}



.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover, .stDownloadButton button:hover{



  transform:translateY(-1px);



}



.stButton button[kind="primary"], [data-testid="stBaseButton-primary"],



[data-testid="stFormSubmitButton"] button{



  background:var(--ms-grad) !important;color:#fff !important;border:none !important;



  box-shadow:0 8px 20px rgba(108,92,231,.28);



}



.stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover,



[data-testid="stFormSubmitButton"] button:hover{filter:brightness(1.07);}



.stButton button:disabled, [data-testid="stFormSubmitButton"] button:disabled{



  filter:grayscale(.6);opacity:.55;box-shadow:none;transform:none;



}







/* ---------- Forms, inputs, containers ---------- */



[data-testid="stForm"]{



  background:var(--ms-surface);border:1px solid var(--ms-border) !important;



  border-radius:var(--ms-radius);padding:20px 20px 8px;



  animation:fadeUp .4s ease both;



}



[data-testid="stVerticalBlockBorderWrapper"]{border-radius:var(--ms-radius) !important;}



div[data-baseweb="input"], div[data-baseweb="select"] > div,



div[data-baseweb="textarea"], div[data-baseweb="base-input"]{border-radius:12px !important;}



label[data-testid="stWidgetLabel"] p{font-weight:600;}



[data-testid="stDataFrame"]{



  border:1px solid var(--ms-border);border-radius:14px;overflow:hidden;



}



[data-testid="stAlert"]{border-radius:14px;}







/* ---------- Vendor cards ---------- */



.vcard{animation:fadeUp .45s ease both;}



.vhead{display:flex;align-items:center;gap:12px;margin-bottom:12px;}



.vavatar{



  flex:0 0 46px;width:46px;height:46px;border-radius:14px;



  display:flex;align-items:center;justify-content:center;



  background:var(--ms-grad);color:#fff;font-weight:800;font-size:1.15rem;



  box-shadow:0 6px 14px rgba(108,92,231,.3);



}



.vname{font-weight:800;font-size:1.05rem;line-height:1.25;}



.vrate{font-size:.88rem;opacity:.7;margin-top:2px;}



.vrate b{opacity:1;color:var(--ms-green);}



.vlabel{font-size:.72rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;opacity:.55;margin-bottom:4px;}



.vmenu{



  background:var(--ms-surface);border:1px dashed var(--ms-border);



  border-radius:12px;padding:10px 12px;font-size:.92rem;line-height:1.5;



  min-height:64px;margin-bottom:12px;word-break:break-word;



}



.vmenu.empty{opacity:.55;font-style:italic;}







/* ---------- Pills / banners ---------- */



.pill{



  display:inline-flex;align-items:center;gap:6px;



  padding:4px 11px;border-radius:999px;font-size:.78rem;font-weight:700;



}



.pill.ok{background:rgba(0,184,148,.14);color:#00a383;}



.pill.no{background:rgba(225,112,85,.15);color:#d35d40;}



.pill.info{background:rgba(9,132,227,.13);color:#0984e3;}



.pill .dot{width:8px;height:8px;border-radius:50%;background:currentColor;}



.pill.ok .dot{animation:pulse 1.6s infinite;}



@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(0,184,148,.55);}100%{box-shadow:0 0 0 8px rgba(0,184,148,0);}}



.banner{



  display:flex;flex-wrap:wrap;align-items:center;gap:10px;



  padding:12px 16px;margin:16px 0 4px;border-radius:14px;



  background:var(--ms-surface);border:1px solid var(--ms-border);



  font-size:.92rem;



}







/* ---------- Login ---------- */



.login-foot{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-top:14px;}



.login-foot span{



  padding:6px 12px;border-radius:999px;font-size:.8rem;font-weight:600;



  background:var(--ms-surface);border:1px solid var(--ms-border);



}







/* ---------- Sidebar ---------- */



.side-card{



  display:flex;align-items:center;gap:12px;padding:14px;border-radius:16px;



  background:var(--ms-surface);border:1px solid var(--ms-border);margin-bottom:14px;



}



.side-avatar{



  width:44px;height:44px;border-radius:50%;flex:0 0 44px;



  display:flex;align-items:center;justify-content:center;



  background:var(--ms-grad);color:#fff;font-weight:800;



}



.side-name{font-weight:800;line-height:1.2;word-break:break-word;}



.side-brand{font-size:1.25rem;font-weight:800;margin-bottom:12px;}



.muted{opacity:.65;}







/* ---------- Mobile ---------- */



@media (max-width:640px){



  .block-container, [data-testid="stMainBlockContainer"]{



    padding:.6rem .8rem 3rem !important;



  }



  .hero{padding:22px 20px;border-radius:20px;margin-bottom:16px;}



  .hero h1{font-size:1.45rem;}



  .hero p{font-size:.9rem;}



  .hero::before{width:180px;height:180px;right:-60px;top:-80px;}



  div[role="radiogroup"]{flex-wrap:nowrap !important;overflow-x:auto;-webkit-overflow-scrolling:touch;}



  div[role="radiogroup"] > label{padding:8px 14px;}



  div[data-testid="stMetric"]{padding:14px 16px 12px;}



  [data-testid="stMetricValue"]{font-size:1.4rem !important;}



  [data-testid="stForm"]{padding:16px 14px 6px;}



  .stButton button, [data-testid="stFormSubmitButton"] button, .stDownloadButton button{



    width:100%;min-height:48px;



  }



  .sec h3{font-size:1.05rem;}



}



</style>



""", unsafe_allow_html=True)











# ============================================================



# HTTP



# ============================================================







@st.cache_resource



def http_session() -> requests.Session:



    session = requests.Session()



    retry = Retry(



        total=2,



        connect=2,



        read=2,



        status=2,



        backoff_factor=0.25,



        status_forcelist=(429, 500, 502, 503, 504),



        allowed_methods=frozenset(),  # Never retry order/payment writes automatically.



        raise_on_status=False,



    )



    session.mount("https://", HTTPAdapter(max_retries=retry))



    session.headers.update({



        "Accept": "application/json",



        "Content-Type": "application/json",



        "User-Agent": "MegaServe-Tiffin-V15/1.1",



    })



    return session











def _api_post_uncached(action: str, **payload: Any) -> dict[str, Any]:



    body = {



        "action": action,



        "username": st.session_state.get("username", ""),



        "pin": st.session_state.get("pin", ""),



        **payload,



    }



    try:



        response = http_session().post(



            GOOGLE_SCRIPT_URL,



            json=body,



            timeout=REQUEST_TIMEOUT,



            allow_redirects=True,



        )



    except requests.RequestException as exc:



        raise AppError(f"Could not connect to backend: {exc}") from exc







    raw = (response.text or "").lstrip("\ufeff").strip()



    if not raw:



        raise AppError(



            "Backend returned an empty response. Deploy the V15 Apps Script "



            "as a Web App with 'Execute as me' and 'Who has access: Anyone'."



        )



    try:



        data = response.json()



    except ValueError as exc:



        log.error("Non-JSON response: HTTP %s | %s", response.status_code, raw[:1000])



        raise AppError(



            "Backend did not return JSON. Make sure the V15 Apps Script is deployed "



            "to this /exec URL."



        ) from exc



    if not isinstance(data, dict):



        raise AppError("Backend returned an invalid response.")



    if not data.get("ok"):



        raise AppError(str(data.get("message", "Backend request failed.")))



    return data











# ============================================================



# LAZY API CACHE (PER STREAMLIT USER SESSION)



# ============================================================



# Only read-only actions are cached. Never cache login or writes.



READ_ACTIONS = frozenset({



    "public_home", "user_home", "user_month_report",



    "vendor_dashboard", "vendor_month_report", "admin_dashboard",



    "admin_users", "admin_all_vendors", "admin_month_report",



    "admin_payments", "admin_list_settings", "admin_vendor_today",

    "admin_day_report",



})



LIVE_ACTIONS = frozenset({"user_home", "vendor_dashboard", "admin_dashboard", "admin_vendor_today"})











def invalidate_data() -> None:



    """Clear only the current browser session's API data cache."""



    st.session_state.pop("_api_cache", None)











def api_post(action: str, **payload: Any) -> dict[str, Any]:



    """Send an API request; cache allowed reads for a bounded time.







    A write is always sent to the server and invalidates cached reads.



    """



    is_read = action in READ_ACTIONS



    cache_key = ""



    now = monotonic()



    if is_read:



        # Include the authenticated account, so login changes cannot reuse data.



        cache_key = json.dumps(



            [action, st.session_state.get("username", ""), payload],



            sort_keys=True, default=str, ensure_ascii=False,



        )



        entry = st.session_state.get("_api_cache", {}).get(cache_key)



        if entry is not None and now < entry[0]:



            return entry[1]







    result = _api_post_uncached(action, **payload)



    if is_read:



        ttl = 15 if action in LIVE_ACTIONS else 120



        cache = st.session_state.setdefault("_api_cache", {})



        cache[cache_key] = (monotonic() + ttl, result)



        # Bound memory even if a user browses many historical months.



        if len(cache) > 100:



            expired = [key for key, (expires, _) in cache.items()



                       if expires <= monotonic()]



            for key in expired:



                cache.pop(key, None)



            while len(cache) > 100:



                cache.pop(next(iter(cache)))



    else:



        invalidate_data()



    return result











# ============================================================



# UI HELPERS (presentation only)



# ============================================================







def format_display_date(value: Any) -> str:
    """Format known ISO dates for display; preserve invalid/unknown values."""
    if value is None or value == "":
        return ""
    if isinstance(value, (date,)):
        return value.strftime("%d-%b-%Y")
    raw = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        try:
            return date.fromisoformat(raw).strftime("%d-%b-%Y")
        except ValueError:
            return raw
    return raw


def date_columns_for_display(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in result.columns:
        if str(column).lower() in {"date", "order_date", "menu_date", "paid_on"}:
            result[column] = result[column].map(format_display_date)
    return result


def esc(value: Any) -> str:



    return _html.escape(str(value if value is not None else ""))











def hero(title: str, subtitle: str = "", chip: str = "") -> None:



    chip_html = f'<span class="hero-chip">{esc(chip)}</span>' if chip else ""



    st.markdown(



        f'<div class="hero">{chip_html}<h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>',



        unsafe_allow_html=True,



    )











def section_title(title: str, caption: str = "") -> None:



    cap = f"<p>{esc(caption)}</p>" if caption else ""



    st.markdown(f'<div class="sec"><h3>{esc(title)}</h3>{cap}</div>', unsafe_allow_html=True)











def initials(name: str) -> str:



    parts = [p for p in str(name or "").split() if p]



    return "".join(p[0] for p in parts[:2]).upper() or "🍱"











def render_vendor_card(v: dict[str, Any], voted: bool) -> None:

    """Render a vendor card using native Streamlit controls (no multiline HTML)."""

    vendor_name = str(v.get("vendor_name") or "Unnamed vendor").strip()

    menu = str(v.get("menu") or "").strip()



    left, right = st.columns([1, 5], vertical_alignment="center")

    with left:

        st.markdown(f"**{esc(initials(vendor_name))}**", unsafe_allow_html=True)

    with right:

        st.markdown(f"**{esc(vendor_name)}**", unsafe_allow_html=True)


    if voted:

        st.success("✓ Selected vendor")

    st.markdown("**Today's menu**")

    if menu:

        st.write(menu)

    else:

        st.caption("Not published yet")







def logout() -> None:



    for key in ("logged_in", "username", "role", "user", "pin", "_api_cache"):



        st.session_state.pop(key, None)



    st.rerun()











def df_or_info(rows: list[dict[str, Any]], message: str = "No records.") -> None:



    if rows:



        st.dataframe(date_columns_for_display(pd.DataFrame(rows)), use_container_width=True, hide_index=True)



    else:



        st.info(message)











# ============================================================



# LOGIN



# ============================================================







def login() -> bool:



    if st.session_state.get("logged_in"):



        return True







    hero("🍱 MegaServe Tiffin", "Simple multi-vendor tiffin management", chip="Welcome back")







    left, center, right = st.columns([1, 1.3, 1])



    with center:



        section_title("Sign in", "Use the username and PIN given by your admin")



        with st.form("login"):



            username = st.text_input("Username", placeholder="e.g. rahul")



            pin = st.text_input("PIN", type="password", placeholder="••••")



            submit = st.form_submit_button("Login  →", use_container_width=True)







        if submit:



            username = username.strip()



            pin = pin.strip()



            if not username or not pin:



                st.error("Enter username and PIN.")



            else:



                try:



                    result = api_post("login", username=username, pin=pin)



                    st.session_state.logged_in = True



                    st.session_state.username = username



                    st.session_state.role = result["user"]["role"]



                    st.session_state.user = result["user"]



                    st.session_state.pin = pin



                    st.rerun()



                except AppError as exc:



                    st.error(str(exc))







        st.markdown(



            '<div class="login-foot"><span>🗳️ Daily voting</span>'



            '<span>🍽️ Live menus</span><span>📊 Monthly reports</span></div>',



            unsafe_allow_html=True,



        )



    return False











# ============================================================



# SHARED PORTAL PIECES



# ============================================================







def month_picker(key: str, *, completed_only: bool = False) -> str:

    """Month-only selector: no day picker and no invalid month strings."""

    today = india_today()

    latest = today.year * 12 + today.month - (1 if completed_only else 0)

    options = []

    for step in range(0, 120):

        index = latest - step - 1

        options.append(f"{index // 12:04d}-{index % 12 + 1:02d}")

    return st.selectbox('Select month', options, key=key,

                        format_func=lambda m: date(int(m[:4]), int(m[5:]), 1).strftime('%B %Y'))





def name_selector(label: str, records: list[dict[str, Any]], id_field: str, name_field: str,

                  key: str, *, all_option: bool = False) -> str:

    mapping = {str(r[id_field]): str(r.get(name_field) or r[id_field]) for r in records}

    opts = ([''] if all_option else []) + list(mapping)

    return st.selectbox(label, opts, key=key,

                        format_func=lambda value: 'All' if not value else mapping.get(value, value))





def payment_month_completed(month: str) -> bool:

    return bool(month and month < india_today().strftime('%Y-%m'))





def payment_checkbox_changed(widget_key: str) -> None:

    """Persist changed rows only; avoid re-sending the entire payment table."""

    changes = st.session_state.get(widget_key, {}).get('edited_rows', {})

    rows = st.session_state.get('payment_grid_rows', [])

    month = st.session_state.get('payments_selected_month')

    if not month or not payment_month_completed(month):

        st.session_state['payment_notice'] = 'Payments can only be changed for completed months.'

        return

    for index, columns in changes.items():

        idx = int(index)

        if idx >= len(rows) or 'paid' not in columns:

            continue

        record = rows[idx]

        wanted = bool(columns['paid'])

        if wanted == bool(record.get('paid')):

            continue

        try:

            api_post('admin_mark_paid' if wanted else 'admin_clear_paid',

                     member_id=record['member_id'], vendor_id=record['vendor_id'], month=month)

        except AppError as exc:

            st.session_state['payment_notice'] = str(exc)

            break

    st.session_state.pop('payment_grid_rows', None)

    st.session_state.pop('payments_loaded_month', None)

    st.session_state['payment_reload_pending'] = True

    st.session_state['payment_editor_version'] = st.session_state.get('payment_editor_version', 0) + 1





def daily_report_display(data: dict[str, Any], *, show_people: bool = True) -> None:

    a, b = st.columns(2)

    a.metric('Total Tiffins', int(data.get('total_tiffins', 0)))

    b.metric('Active Vendors', len(data.get('vendor_totals', [])))

    section_title('Vendor-wise daily orders')

    display_rows(data.get('vendor_totals', []), hide_ids=True)

    if show_people:

        section_title('Orders by person')

        display_rows(data.get('orders', []), hide_ids=True)





def display_rows(rows: list[dict[str, Any]], hide_ids: bool = False) -> None:



    """Keep IDs in API payload but show readable display names in portals."""



    if not rows:



        st.info('No records.')



        return



    df = pd.DataFrame(rows)



    if hide_ids:



        df = df.drop(columns=['member_id', 'vendor_id'], errors='ignore')



    st.dataframe(date_columns_for_display(df), use_container_width=True, hide_index=True)











def profile_panel() -> None:



    """Account holder can change only username and PIN. System IDs are immutable."""



    actor = st.session_state['user']



    section_title('My Profile', 'Your account ID is allocated automatically and cannot be changed.')



    with st.container(border=True):



        c1, c2 = st.columns(2)



        c1.text_input('Account ID (read-only)',



                      value=actor.get('vendor_id') or actor.get('member_id', ''), disabled=True)



        c2.text_input('Name (contact admin to change)',



                      value=actor.get('person_name', ''), disabled=True)







    section_title('Login details', 'Update your username or PIN')



    with st.form('self_profile'):



        new_username = st.text_input('Login username', value=actor.get('username', ''), max_chars=80)



        current_pin = st.text_input('Current PIN (required)', type='password')



        p1, p2 = st.columns(2)



        new_pin = p1.text_input('New PIN (optional; 4–12 digits)', type='password')



        confirm_pin = p2.text_input('Confirm new PIN', type='password')



        submitted = st.form_submit_button('Update Login Details')



    if submitted:



        if new_pin != confirm_pin:



            st.error('New PIN and confirmation do not match.')



            return



        if not current_pin:



            st.error('Enter your current PIN.')



            return



        updated = api_post('profile_update', new_username=new_username.strip(),



                           current_pin=current_pin, new_pin=new_pin)



        st.session_state['user'] = updated['user']



        st.session_state['username'] = updated['user']['username']



        st.session_state['pin'] = new_pin or current_pin



        for key in ('user_report_key', 'vendor_report_key', 'show_vendor_menus'):



            st.session_state.pop(key, None)



        st.success('Login details updated.')



        st.rerun()











def show_month_report(data: dict[str, Any], show_users: bool = False) -> None:



    a, b = st.columns(2)



    a.metric('Total Tiffins', int(data.get('total_tiffins', 0)))



    b.metric('Total Amount', f"₹{float(data.get('total_amount', 0)):,.2f}")



    section_title('Vendor breakdown')



    display_rows(data.get('vendor_totals', []), hide_ids=True)



    if show_users:



        section_title('User × Vendor breakdown')



        display_rows(data.get('rows', []), hide_ids=True)



    daily = data.get('daily', [])



    if daily:



        frame = pd.DataFrame(daily)



        chart = frame.assign(vendor_name=frame['vendor_id'].map({v['vendor_id']: v['vendor_name'] for v in data.get('vendor_totals', [])}).fillna(frame['vendor_id'])).pivot_table(index='date', columns='vendor_name', values='count', aggfunc='sum', fill_value=0)



        section_title('Daily trend')



        with st.container(border=True):



            st.bar_chart(chart)



        st.download_button('⬇️ Download daily CSV', date_columns_for_display(frame.assign(vendor_name=frame['vendor_id'].map({v['vendor_id']: v['vendor_name'] for v in data.get('vendor_totals', [])})).drop(columns=['vendor_id'])).to_csv(index=False).encode('utf-8-sig'), f"tiffin_daily_{data['month']}.csv", 'text/csv')











# ============================================================



# USER PORTAL



# ============================================================







USER_ICONS = {'Vote & Today’s Menu': '🗳️', 'Monthly History': '📅', 'My Profile': '👤'}











def user_portal() -> None:



    user = st.session_state['user']



    mid = user['member_id']



    hero('🍱 My Tiffin Dashboard', f"Welcome, {user['person_name']}", chip=india_today().strftime('%A, %d %b %Y'))



    page = st.radio('User section', ['Vote & Today’s Menu', 'Monthly History', 'My Profile'],



                    horizontal=True, label_visibility='collapsed',



                    format_func=lambda p: f"{USER_ICONS.get(p, '')} {p}")



    if page == 'Vote & Today’s Menu':



        home = api_post('user_home', member_id=mid)



        a, b, c = st.columns(3)



        a.metric('Current Month Tiffins', home['month_tiffins'])



        b.metric('Month Amount', f"₹{home['month_amount']:,.2f}")



        c.metric('Today’s Vendor', next((v['vendor_name'] for v in home.get('vendors', []) if v['vendor_id'] == home.get('today_vote')), 'Not voted'))







        status = ('<span class="pill ok"><span class="dot"></span>Voting open</span>'



                  if home['voting_open'] else



                  '<span class="pill no"><span class="dot"></span>Voting closed</span>')



        st.markdown(f'<div class="banner">{status}<span class="muted">🕒 {esc(home["window_label"])}</span></div>',



                    unsafe_allow_html=True)







        section_title('Choose today’s vendor', 'One vote = one tiffin')



        vendors = home.get('vendors', [])



        if not vendors:



            st.info('No vendors available right now.')



        else:



            cols = st.columns(min(3, len(vendors)))



            for i, v in enumerate(vendors):



                with cols[i % len(cols)]:



                    with st.container(border=True):



                        render_vendor_card(v, home.get('today_vote') == v['vendor_id'])



                        if home.get('today_vote') == v['vendor_id']:



                            st.success('Your vote is confirmed')



                        elif st.button('Vote for ' + v['vendor_name'], key='vote_' + v['vendor_id'],



                                       disabled=not home['voting_open'] or bool(home.get('today_vote')),



                                       type='primary', use_container_width=True):



                            api_post('cast_vote', member_id=mid, vendor_id=v['vendor_id'])



                            st.rerun()



        st.caption('One vote = one tiffin. A submitted vote cannot be changed by the user.')



    if page == 'My Profile':



        profile_panel()



    if page == 'Monthly History':



        section_title('Monthly History', 'Pick a month and load your report')



        c1, c2 = st.columns([2, 1], vertical_alignment='bottom')



        with c1:



            month = month_picker('user_month')



        with c2:



            if st.button('Load user monthly report', type='primary', use_container_width=True):



                st.session_state['user_report_key'] = month



        if st.session_state.get('user_report_key') == month:



            data = api_post('user_month_report', member_id=mid, month=month)



            show_month_report(data, show_users=True)











# ============================================================



# VENDOR PORTAL



# ============================================================







VENDOR_ICONS = {'Today’s Confirmed Orders': '📦', 'Manage Today/Future Menus': '🍽️',



                'Monthly Statistics': '📊', 'My Profile': '👤'}











def vendor_portal() -> None:



    vid = st.session_state['user']['vendor_id']



    hero('🏪 Vendor Dashboard', 'Today’s orders and menu', chip=india_today().strftime('%A, %d %b %Y'))



    page = st.radio('Vendor section', ['Today’s Confirmed Orders', 'Manage Today/Future Menus', 'Monthly Statistics', 'My Profile'],



                    horizontal=True, label_visibility='collapsed',



                    format_func=lambda p: f"{VENDOR_ICONS.get(p, '')} {p}")



    if page == 'Today’s Confirmed Orders':



        data = api_post('vendor_dashboard', vendor_id=vid)



        a, b, c = st.columns(3)



        a.metric('Today Orders', data['today_count'])



        b.metric('Current Month Orders', data['month_count'])



        c.metric('Price / Tiffin', f"₹{float(data['rate']):,.2f}")



        st.caption('Only aggregate order counts are available to vendors.')



    if page == 'Manage Today/Future Menus':



        section_title('Publish a menu', 'Today or any future date')



        with st.form('menu_save'):



            d = st.date_input('Menu date', value=india_today(), min_value=india_today(), format="DD/MM/YYYY")



            menu = st.text_area('Food menu (today or future only)', max_chars=2000,



                                placeholder='e.g. Dal tadka, jeera rice, 4 rotis, salad')



            if st.form_submit_button('Save Menu'):



                api_post('set_menu', vendor_id=vid, date=d.isoformat(), menu=menu.strip())



                st.success('Menu saved')



                st.rerun()



        section_title('Scheduled menus')



        if st.button('Load scheduled menus'):



            st.session_state['show_vendor_menus'] = True



        if st.session_state.get('show_vendor_menus'):



            df_or_info(api_post('vendor_dashboard', vendor_id=vid).get('menus', []))



    if page == 'My Profile':



        profile_panel()



    if page == 'Monthly Statistics':



        section_title('Monthly Statistics', 'Pick a month and load your report')



        c1, c2 = st.columns([2, 1], vertical_alignment='bottom')



        with c1:



            month = month_picker('vendor_month')



        with c2:



            if st.button('Load vendor monthly report', type='primary', use_container_width=True):



                st.session_state['vendor_report_key'] = month



        if st.session_state.get('vendor_report_key') == month:



            report = api_post('vendor_month_report', vendor_id=vid, month=month)
            a, b = st.columns(2)
            a.metric('Total Tiffins', int(report.get('total_tiffins', 0)))
            b.metric('Total Amount', f"₹{float(report.get('total_amount', 0)):,.2f}")

            section_title('Daily Tiffin & Amount Breakdown')
            daily_rows = report.get('daily', [])
            if daily_rows:
                frame = pd.DataFrame(daily_rows)
                frame['date'] = pd.to_datetime(frame['date'], format='%Y-%m-%d', errors='coerce')
                frame = frame.dropna(subset=['date'])
                if not frame.empty:
                    frame = frame.sort_values('date')
                    frame['date'] = frame['date'].dt.strftime('%d-%b-%Y')
                    frame = frame.rename(columns={'date': 'Date', 'count': 'Tiffins',
                                                  'rate': 'Rate (₹)', 'amount': 'Amount (₹)'})
                    st.dataframe(frame[['Date', 'Tiffins', 'Rate (₹)', 'Amount (₹)']],
                                 use_container_width=True, hide_index=True)
                else:
                    st.info('No valid dated records for this month.')
            else:
                st.info('No orders recorded for this month.')











# ============================================================



# ADMIN PORTAL



# ============================================================







ADMIN_ICONS = {'Overview': '📊', 'Users': '👥', 'Vendors & Pricing': '🏪', 'Menus': '🍽️',



               'Monthly Reports': '📅', 'Day-wise Analysis': '📆', 'Payments': '💳', 'Settings': '⚙️', 'Correct Orders': '🛠️'}











def admin_portal() -> None:

    hero('⚙️ Admin Control Center', 'Users, vendors, menus, payments and reporting', chip='Administrator')

    pages = ['Overview', 'Users', 'Vendors & Pricing', 'Menus', 'Monthly Reports',

             'Day-wise Analysis', 'Payments', 'Settings', 'Correct Orders']

    page = st.radio('Admin section', pages, horizontal=True, label_visibility='collapsed',

                    format_func=lambda choice: f"{ADMIN_ICONS.get(choice, '')} {choice}")

    if page == 'Overview':

        data = api_post('admin_dashboard')

        vendors = data.get('vendors', [])

        todays = sum(int(v.get('today_count', 0)) for v in vendors)

        monthly = sum(int(v.get('month_count', 0)) for v in vendors)

        a, b, c, d = st.columns(4)

        a.metric('Active Vendors', len(vendors))

        b.metric('Today Orders', todays)

        c.metric('This Month Orders', monthly)

        d.metric('Daily Revenue (estimated)', f"₹{sum(int(v.get('today_count', 0))*float(v.get('rate', 0)) for v in vendors):,.0f}")

        section_title('Today and month by vendor', 'Live order counts per vendor')

        if vendors:

            view = pd.DataFrame([{'Vendor': v['vendor_name'], 'Today': v['today_count'],

                                  'This Month': v['month_count'], 'Rate': v['rate'],

                                  'Month Value': int(v['month_count'])*float(v['rate'])} for v in vendors])

            st.dataframe(view, hide_index=True, use_container_width=True)

            st.bar_chart(view.set_index('Vendor')[['Today', 'This Month']])

        else:

            st.info('No active vendors')



    elif page == 'Users':

        users = api_post('admin_users').get('users', [])

        section_title('User master', 'Activate/deactivate and edit a person from the same selector')

        st.dataframe(pd.DataFrame(users).drop(columns=['member_id', 'vendor_id'], errors='ignore'),

                     use_container_width=True, hide_index=True)

        regular = [u for u in users if u.get('role') == 'USER']

        with st.expander('➕ Add new user', expanded=False):

            with st.form('add_user_v18'):

                uname = st.text_input('Login username', key='add_uname')

                pname = st.text_input('Person name', key='add_pname')

                pin = st.text_input('PIN (4–12 digits)', type='password', key='add_upin')

                if st.form_submit_button('Create User'):

                    api_post('admin_save_user', member_id='', new_username=uname.strip(), person_name=pname.strip(),

                             new_pin=pin, new_role='USER', active=True)

                    st.success('New user created with automatic unique member ID.'); st.rerun()

        if regular:

            section_title('Edit / activate user')

            selected_id = name_selector('Select person', regular, 'member_id', 'person_name', 'edit_user_id')

            u = next(x for x in regular if x['member_id'] == selected_id)

            with st.form(f'edit_user_{selected_id}'):

                c1, c2 = st.columns(2)

                name = c1.text_input('Person Name', value=u.get('person_name',''))

                uname = c2.text_input('Username', value=u.get('username',''))

                pin = st.text_input('New PIN (leave blank to retain)', type='password')

                active = st.checkbox('Active user', value=bool(u.get('active',True)))

                if st.form_submit_button('Save user changes'):

                    api_post('admin_save_user', member_id=selected_id, new_username=uname.strip(),

                             person_name=name.strip(), new_pin=pin, new_role='USER', active=active)

                    st.success('User updated'); st.rerun()



    elif page == 'Vendors & Pricing':

        vendors = api_post('admin_all_vendors').get('vendors', [])

        section_title('Vendor master', 'Activate/deactivate vendors in one place')

        st.dataframe(pd.DataFrame(vendors).drop(columns=['vendor_id'], errors='ignore'),

                     use_container_width=True, hide_index=True)

        with st.expander('➕ Add new vendor', expanded=False):

            with st.form('add_vendor_v18'):

                name = st.text_input('Vendor name')

                uname = st.text_input('Vendor login username')

                pin = st.text_input('PIN (4–12 digits)', type='password')

                rate = st.number_input('Default price', min_value=0.0, value=90.0)

                if st.form_submit_button('Create Vendor'):

                    api_post('admin_save_vendor', vendor_id='', vendor_name=name.strip(), new_username=uname.strip(),

                             new_pin=pin, default_rate=rate, active=True)

                    st.success('Vendor created with automatic unique vendor ID.'); st.rerun()

        if vendors:

            section_title('Edit / activate vendor')

            vid = name_selector('Select vendor', vendors, 'vendor_id', 'vendor_name', 'edit_vendor_id')

            v = next(x for x in vendors if x['vendor_id'] == vid)

            with st.form(f'edit_vendor_{vid}'):

                c1, c2 = st.columns(2)

                name = c1.text_input('Vendor name', value=v.get('vendor_name',''))

                uname = c2.text_input('Vendor login username', value=v.get('username',''))

                pin = st.text_input('New PIN (leave blank to retain)', type='password')

                rate = st.number_input('Default price', min_value=0.0, value=float(v.get('default_rate',90)))

                active = st.checkbox('Active vendor', value=bool(v.get('active',True)))

                if st.form_submit_button('Save Vendor Changes'):

                    api_post('admin_save_vendor', vendor_id=vid, vendor_name=name.strip(), new_username=uname.strip(),

                             new_pin=pin, default_rate=rate, active=active)

                    st.success('Vendor updated'); st.rerun()

            section_title('Monthly price override')

            with st.form('month_price_v18'):

                price_vendor = name_selector('Vendor', vendors, 'vendor_id','vendor_name','monthly_rate_vendor')

                price_month = month_picker('monthly_rate_month')

                price = st.number_input('Monthly price', min_value=0.0, value=float(v.get('default_rate',90)))

                if st.form_submit_button('Update Monthly Price'):

                    api_post('admin_set_rate', vendor_id=price_vendor, month=price_month, rate=price)

                    st.success('Rate updated'); st.rerun()



    elif page == 'Menus':

        vendors = api_post('admin_all_vendors').get('vendors', [])

        section_title('Manage menus')

        if vendors:

            with st.form('admin_menu'):

                vid = name_selector('Vendor', vendors, 'vendor_id', 'vendor_name', 'admin_menu_vendor')

                day = st.date_input('Menu date', min_value=india_today(), format="DD/MM/YYYY")

                menu = st.text_area('Menu', max_chars=2000)

                if st.form_submit_button('Save Menu'):

                    api_post('admin_save_menu', vendor_id=vid, date=day.isoformat(), menu=menu.strip())

                    st.success('Menu saved'); st.rerun()



    elif page == 'Monthly Reports':

        section_title('Monthly Reports', 'Select a month, person and vendor, then load')

        users = [u for u in api_post('admin_users').get('users',[]) if u['role']=='USER']

        vendors = api_post('admin_all_vendors').get('vendors',[])

        with st.container(border=True):

            a,b,c = st.columns(3)

            with a: month = month_picker('admin_month')

            with b: uid = name_selector('Filter person', users, 'member_id', 'person_name', 'month_user',all_option=True)

            with c: vid = name_selector('Filter vendor', vendors, 'vendor_id','vendor_name','month_vendor',all_option=True)

            selected = (month,uid,vid)

            if st.button('Load monthly report', type='primary'):

                st.session_state['admin_report_key']=selected

        if st.session_state.get('admin_report_key') == selected:

            report = api_post('admin_month_report',month=month,member_id=uid,vendor_id=vid)

            show_month_report(report,show_users=True)



    elif page == 'Day-wise Analysis':

        section_title('Daily Analysis', 'Individual day, all people and vendors')

        users = [u for u in api_post('admin_users').get('users',[]) if u['role']=='USER']

        vendors = api_post('admin_all_vendors').get('vendors',[])

        with st.container(border=True):

            a,b,c=st.columns(3)

            with a: day = st.date_input('Select day',key='admin_day_date',value=india_today(),format="DD/MM/YYYY")

            with b: uid = name_selector('Person',users,'member_id','person_name','daily_user',all_option=True)

            with c: vid = name_selector('Vendor',vendors,'vendor_id','vendor_name','daily_vendor',all_option=True)

            selected = (day.isoformat(),uid,vid)

            if st.button('Load daily analysis',type='primary'):

                st.session_state['admin_day_key']=selected

        if st.session_state.get('admin_day_key') == selected:

            daily_report_display(api_post('admin_day_report',date=day.isoformat(),member_id=uid,vendor_id=vid))



    elif page == 'Payments':

        section_title('Monthly Payments', 'Click the Paid checkbox to update each person directly')

        month = month_picker('payment_month', completed_only=False)

        closed = payment_month_completed(month)

        st.info('Payments can only be settled for a completed month.' if not closed else

                f'{month} is a completed month. Check or uncheck Paid to update the ledger.')

        if st.button('Load Payment Report',type='primary'):

            st.session_state['payments_loaded_month']=month

        if st.session_state.get('payment_reload_pending'):

            st.session_state['payment_reload_pending']=False

            st.session_state['payments_loaded_month']=month

        if st.session_state.get('payments_loaded_month') == month:

            response=api_post('admin_payments',month=month)

            records=response.get('payments',[])

            st.session_state['payment_grid_rows']=records

            st.session_state['payments_selected_month']=month

            if st.session_state.pop('payment_notice', None):

                st.warning('Could not save one or more payment updates. Refresh the report.')

            if records:

                frame=pd.DataFrame(records)

                frame=frame[['person_name','vendor_name','tiffins','rate','amount','paid','paid_on']]

                frame.columns=['Person','Vendor','Tiffins','Rate','Amount','paid','Paid On']

                editor_key = f"payment_grid_{st.session_state.get('payment_editor_version', 0)}"

                st.data_editor(frame, hide_index=True, use_container_width=True, key=editor_key,

                               disabled=['Person','Vendor','Tiffins','Rate','Amount','Paid On'] if closed else list(frame.columns),

                               column_config={'paid':st.column_config.CheckboxColumn('Paid',help='Click to settle this person and vendor')},

                               on_change=payment_checkbox_changed, args=(editor_key,))

                st.download_button('⬇️ Download Payments CSV',pd.DataFrame(records).to_csv(index=False).encode('utf-8-sig'),

                                   f'payments_{month}.csv','text/csv')

            else: st.info('No payments for this month.')

            if closed and records:

                section_title('Mark every outstanding due paid', 'Only use after confirming all money was received')

                confirmation=st.checkbox('I confirm that all dues for this completed month were received', key=f'all_paid_{month}')

                if st.button('Mark ALL dues paid',disabled=not confirmation):

                    api_post('admin_mark_all_paid',month=month)

                    st.session_state.pop('payments_loaded_month',None)

                    st.session_state['payment_editor_version'] = st.session_state.get('payment_editor_version', 0) + 1

                    st.success('All dues marked paid'); st.rerun()



    elif page == 'Settings':

        values = api_post('admin_list_settings').get('settings', {})
        section_title('Voting window')

        import re

        def _voting_hhmm(raw: Any, default: str) -> str:
            value = str(raw if raw is not None else '').strip()
            match = re.fullmatch(r'([01]?\d|2[0-3]):([0-5]\d)(?::\d{2})?', value)
            if match:
                return f'{int(match.group(1)):02d}:{match.group(2)}'
            # Legacy backend sent an 1899 Date.toString() instead of HH:mm.
            legacy = re.search(r'\b([01]?\d|2[0-3]):([0-5]\d):\d{2}\s+GMT', value)
            if legacy:
                return f'{int(legacy.group(1)):02d}:{legacy.group(2)}'
            return default

        with st.form('voting_settings'):
            a, b = st.columns(2)
            begin = a.text_input('Voting start (HH:MM)', value=_voting_hhmm(values.get('VOTING_START'), '09:00'))
            end = b.text_input('Voting end (HH:MM)', value=_voting_hhmm(values.get('VOTING_END'), '12:00'))
            if st.form_submit_button('Save Settings'):
                if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', begin) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', end):
                    st.error('Enter times in HH:MM format, such as 09:00 and 12:00.')
                elif begin >= end:
                    st.error('Voting end must be later than voting start.')
                else:
                    api_post('admin_update_settings', voting_start=begin, voting_end=end)
                    st.success('Saved'); st.rerun()


    elif page == 'Correct Orders':

        st.warning('Correcting an order changes historical totals. Confirm details first.')

        all_users = [u for u in api_post('admin_users').get('users', [])
                     if u.get('role') == 'USER']
        users = [u for u in all_users if u.get('active') is True]
        inactive_count = len(all_users) - len(users)
        if inactive_count:
            st.info(f'{inactive_count} inactive user(s) are excluded from order corrections. '
                    'Reactivate an account in Users before editing its orders.')

        vendors=api_post('admin_all_vendors').get('vendors',[])

        if users:

            with st.form('admin_correct_vote'):

                a,b,c=st.columns(3)

                with a: uid=name_selector('Person',users,'member_id','person_name','correct_user')

                with b: chosen_date=st.date_input('Order date',value=india_today(),format="DD/MM/YYYY")

                with c: vid=name_selector('Vendor / remove',vendors,'vendor_id','vendor_name','correct_vendor',all_option=True)

                st.caption('All = remove tiffin for this day')

                confirm=st.checkbox('I confirm this correction')

                if st.form_submit_button('Apply Correction'):

                    if not confirm: st.error('Confirm first')

                    elif not any(u['member_id'] == uid and u.get('active') is True for u in users):
                        st.error('This user is inactive. Reactivate the user before editing any orders.')
                    else:
                        try:
                            api_post('admin_override_order', member_id=uid,
                                     date=chosen_date.isoformat(), vendor_id=vid)
                        except AppError as exc:
                            st.error(str(exc))
                        else:
                            st.success('Order corrected')
                            st.rerun()
        else:
            st.info('No active users available for order correction.')

def main() -> None:



    if not login():



        return







    user = st.session_state["user"]



    role = str(user.get("role", "USER")).upper()



    display_name = user.get("person_name", st.session_state.get("username", ""))







    with st.sidebar:



        st.markdown('<div class="side-brand">🍱 MegaServe</div>', unsafe_allow_html=True)



        st.markdown(



            f'<div class="side-card"><div class="side-avatar">{esc(initials(display_name))}</div>'



            f'<div><div class="side-name">{esc(display_name)}</div>'



            f'<span class="pill info" style="margin-top:4px">{esc(role)}</span></div></div>',



            unsafe_allow_html=True,



        )



        if st.button("Logout", use_container_width=True):



            logout()







    if st.sidebar.button('🔄 Refresh current data', use_container_width=True):



        invalidate_data()



        st.rerun()



    st.sidebar.caption(f"Version {APP_VERSION}")







    try:



        if role == "ADMIN":



            admin_portal()



        elif role == "VENDOR":



            vendor_portal()



        else:



            user_portal()



    except AppError as exc:



        st.error(str(exc))











if __name__ == "__main__":



    main()
