from __future__ import annotations

import csv
import html
import io
import logging
import time
from datetime import date
from typing import Any, Callable

import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =====================================================================
# CONFIG
# =====================================================================

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzmHDwAts60AHnPmNefcVATPE5bYBGspwvAGjGCioaADK5joW5SqB_zdpNRAiCTBAJR/exec"

EXPECTED_CODE_VERSION = "2026-09-17-HISTORY-REPORT-FIX-V8-1"
REQUEST_TIMEOUT_SECONDS = 18
MAX_DAILY_COUNT = 10
APP_UI_VERSION = "V8.1-HISTORY-FIX"

st.set_page_config(
    page_title="MegaServe Tiffin",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("tiffin_tracker")


class AppError(Exception):
    pass


# =====================================================================
# STYLE — THEME SAFE + LIGHTWEIGHT ANIMATION
# =====================================================================

st.markdown(
    """
    <style>
    :root {
        --mega-radius-xl: 24px;
        --mega-radius-lg: 18px;
        --mega-radius-md: 14px;
        --mega-shadow: 0 12px 34px rgba(0, 0, 0, .08);
        --mega-border: rgba(128, 128, 128, .22);
        --mega-green: #14b86e;
        --mega-red: #e25555;
        --mega-blue: #4c8bf5;
        --mega-amber: #e7a93b;
    }

    @keyframes megaFadeUp {
        from {
            opacity: 0;
            transform: translateY(8px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes megaPulseSoft {
        0%, 100% {
            box-shadow: 0 0 0 0 rgba(20, 184, 110, 0);
        }
        50% {
            box-shadow: 0 0 0 6px rgba(20, 184, 110, .06);
        }
    }

    .stApp {
        color: var(--text-color);
        background:
            radial-gradient(circle at 8% 0%, rgba(76, 139, 245, .07), transparent 26%),
            radial-gradient(circle at 92% 0%, rgba(20, 184, 110, .06), transparent 24%),
            var(--background-color);
    }

    .block-container {
        max-width: 1280px;
        padding-top: 1rem;
        padding-bottom: 4rem;
    }

    .mega-hero {
        position: relative;
        overflow: hidden;
        border-radius: var(--mega-radius-xl);
        padding: 25px 30px;
        margin-bottom: 18px;
        background:
            radial-gradient(circle at 85% 15%, rgba(255,255,255,.16), transparent 24%),
            linear-gradient(135deg, #132238 0%, #1f4e78 52%, #227093 100%);
        color: #ffffff !important;
        box-shadow: 0 18px 42px rgba(10, 34, 61, .22);
        animation: megaFadeUp .34s ease-out both;
    }

    .mega-hero::after {
        content: "";
        position: absolute;
        width: 170px;
        height: 170px;
        right: -45px;
        bottom: -80px;
        border-radius: 50%;
        background: rgba(255,255,255,.08);
    }

    .mega-hero h1,
    .mega-hero p {
        color: #ffffff !important;
        position: relative;
        z-index: 1;
    }

    .mega-hero h1 {
        margin: 0;
        font-size: 2rem;
        line-height: 1.15;
        letter-spacing: -.02em;
    }

    .mega-hero p {
        margin: 8px 0 0 0;
        opacity: .9;
    }

    .menu-card,
    .subtle-box,
    .analytics-card {
        color: var(--text-color) !important;
        background: var(--secondary-background-color);
        border: 1px solid var(--mega-border);
        box-shadow: var(--mega-shadow);
        animation: megaFadeUp .30s ease-out both;
    }

    .menu-card {
        border-radius: 20px;
        padding: 20px 22px;
        margin: 8px 0 18px 0;
    }

    .menu-title {
        color: var(--text-color) !important;
        font-size: 0.78rem;
        font-weight: 750;
        letter-spacing: .08em;
        text-transform: uppercase;
        opacity: .7;
        margin-bottom: 8px;
    }

    .menu-body {
        color: var(--text-color) !important;
        font-size: 1.12rem;
        line-height: 1.62;
        white-space: pre-wrap;
    }

    .analytics-card {
        border-radius: 18px;
        padding: 16px 18px;
        margin: 8px 0 12px 0;
    }

    .analytics-kicker {
        color: var(--text-color) !important;
        opacity: .62;
        font-size: .76rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: .07em;
    }

    .analytics-value {
        color: var(--text-color) !important;
        margin-top: 6px;
        font-size: 1.4rem;
        font-weight: 800;
        line-height: 1.2;
    }

    .analytics-note {
        color: var(--text-color) !important;
        opacity: .68;
        margin-top: 5px;
        font-size: .82rem;
    }

    .status-open,
    .status-closed {
        display: inline-block;
        border-radius: 999px;
        padding: 7px 12px;
        color: var(--text-color) !important;
        font-weight: 760;
        font-size: .84rem;
        border: 1px solid transparent;
    }

    .status-open {
        background: rgba(20, 184, 110, .13);
        border-color: rgba(20, 184, 110, .32);
        animation: megaPulseSoft 2.8s ease-in-out infinite;
    }

    .status-closed {
        background: rgba(226, 85, 85, .13);
        border-color: rgba(226, 85, 85, .30);
    }

    .subtle-box {
        border-radius: 16px;
        padding: 14px 16px;
    }

    /* Metrics: explicitly inherit Streamlit theme text colors */
    div[data-testid="stMetric"] {
        color: var(--text-color) !important;
        background: var(--secondary-background-color) !important;
        border: 1px solid var(--mega-border);
        border-radius: var(--mega-radius-lg);
        padding: 15px 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,.06);
        transition:
            transform .18s ease,
            box-shadow .18s ease,
            border-color .18s ease;
        animation: megaFadeUp .28s ease-out both;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 30px rgba(0,0,0,.09);
        border-color: rgba(76, 139, 245, .32);
    }

    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] * {
        color: var(--text-color) !important;
    }

    div[data-testid="stMetricLabel"] {
        font-weight: 680;
        opacity: .72;
    }

    div[data-testid="stMetricValue"] {
        font-weight: 800;
    }

    /* Native Streamlit charts remain theme-aware */
    div[data-testid="stVegaLiteChart"] {
        background: var(--secondary-background-color);
        border: 1px solid var(--mega-border);
        border-radius: var(--mega-radius-lg);
        padding: 10px;
        box-shadow: 0 8px 24px rgba(0,0,0,.05);
        animation: megaFadeUp .32s ease-out both;
    }

    /* Navigation */
    div[data-baseweb="radio"] > div {
        gap: .45rem;
        flex-wrap: wrap;
    }

    div[data-baseweb="radio"] label {
        border-radius: 12px;
    }

    .stButton > button,
    .stFormSubmitButton > button,
    .stDownloadButton > button {
        border-radius: 12px;
        min-height: 2.7rem;
        transition:
            transform .16s ease,
            box-shadow .16s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 18px rgba(0,0,0,.08);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--mega-border);
        box-shadow: 0 8px 22px rgba(0,0,0,.04);
        animation: megaFadeUp .28s ease-out both;
    }

    /* Keep captions, labels, inputs readable in both themes */
    .stMarkdown,
    .stCaption,
    label,
    p,
    span {
        color: inherit;
    }

    /* Avoid large motion for users who disable animations */
    @media (prefers-reduced-motion: reduce) {
        *,
        *::before,
        *::after {
            animation-duration: .001ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: .001ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================================
# HTTP
# =====================================================================

@st.cache_resource
def http_session() -> requests.Session:
    session = requests.Session()

    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.35,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"POST"}),
        raise_on_status=False,
    )

    session.mount(
        "https://",
        HTTPAdapter(max_retries=retry),
    )

    session.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "MegaServeTiffin/7.0",
        }
    )

    return session


def api_post(
    action: str,
    **payload: Any,
) -> dict[str, Any]:
    request_body = {
        "action": action,
        "username": st.session_state.get("username", ""),
        "pin": st.session_state.get("pin", ""),
        **payload,
    }

    try:
        response = http_session().post(
            GOOGLE_SCRIPT_URL,
            json=request_body,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        raise AppError(
            f"Could not reach the tiffin service: {exc}"
        ) from exc

    if not response.ok:
        raise AppError(
            f"Tiffin service returned HTTP {response.status_code}."
        )

    try:
        data = response.json()
    except ValueError as exc:
        logger.error(
            "Non JSON response: %s",
            response.text[:1000],
        )
        raise AppError(
            "The tiffin service returned an invalid response."
        ) from exc

    if not isinstance(data, dict):
        raise AppError(
            "Unexpected response from the tiffin service."
        )

    if not data.get("ok", False):
        raise AppError(
            str(
                data.get(
                    "message",
                    "Request failed.",
                )
            )
        )

    return data


# =====================================================================
# SESSION + SMALL PAGE CACHE
# =====================================================================

DEFAULT_SESSION = {
    "logged_in": False,
    "role": "",
    "member_id": "",
    "username": "",
    "pin": "",
    "person_name": "",
}

for key, value in DEFAULT_SESSION.items():
    st.session_state.setdefault(key, value)


def logout() -> None:
    for key, value in DEFAULT_SESSION.items():
        st.session_state[key] = value

    for key in list(st.session_state.keys()):
        if str(key).startswith("_cache_"):
            del st.session_state[key]

    st.rerun()


def clear_page_cache(*keys: str) -> None:
    for key in keys:
        st.session_state.pop(f"_cache_{key}", None)


def lazy_load(
    key: str,
    loader: Callable[[], dict[str, Any]],
    ttl_seconds: int = 8,
    force: bool = False,
) -> dict[str, Any]:
    cache_key = f"_cache_{key}"
    now = time.time()

    cached = st.session_state.get(cache_key)

    if (
        not force
        and isinstance(cached, dict)
        and now - float(cached.get("ts", 0)) < ttl_seconds
    ):
        return cached["data"]

    data = loader()

    st.session_state[cache_key] = {
        "ts": now,
        "data": data,
    }

    return data


# =====================================================================
# UI HELPERS
# =====================================================================

def hero(
    title: str,
    subtitle: str,
) -> None:
    st.markdown(
        f"""
        <div class="mega-hero">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def menu_card(
    menu_text: str,
    updated_at: str = "",
) -> None:
    if menu_text.strip():
        safe_menu = html.escape(
            menu_text.strip()
        )

        footer = (
            f"<div style='opacity:.55;font-size:.78rem;margin-top:10px;'>"
            f"Updated {html.escape(updated_at)}</div>"
            if updated_at
            else ""
        )

        st.markdown(
            f"""
            <div class="menu-card">
                <div class="menu-title">🍽️ Today's Menu</div>
                <div class="menu-body">{safe_menu}</div>
                {footer}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="menu-card">
                <div class="menu-title">🍽️ Today's Menu</div>
                <div class="menu-body">
                    Menu has not been updated yet.
                </div>
                <div style="opacity:.55;font-size:.78rem;margin-top:10px;">
                    Tiffin count entry still works normally during 09:00–11:00 AM.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def window_badge(
    is_open: bool,
    window: str,
    server_time: str,
) -> None:
    css_class = (
        "status-open"
        if is_open
        else "status-closed"
    )

    label = (
        "● COUNT WINDOW OPEN"
        if is_open
        else "● COUNT WINDOW CLOSED"
    )

    st.markdown(
        f"""
        <span class="{css_class}">{label}</span>
        <span style="margin-left:10px;opacity:.65;">
            {html.escape(window)} · {html.escape(server_time)}
        </span>
        """,
        unsafe_allow_html=True,
    )


def refresh_button(
    cache_key: str,
    button_key: str,
) -> bool:
    clicked = st.button(
        "↻ Refresh",
        key=button_key,
    )

    if clicked:
        clear_page_cache(cache_key)

    return clicked


def format_money(value: Any) -> str:
    return f"₹{float(value or 0):,.0f}"


def analytics_card(
    title: str,
    value: str,
    note: str = "",
) -> None:
    safe_title = html.escape(str(title))
    safe_value = html.escape(str(value))
    safe_note = html.escape(str(note))

    st.markdown(
        f"""
        <div class="analytics-card">
            <div class="analytics-kicker">{safe_title}</div>
            <div class="analytics-value">{safe_value}</div>
            <div class="analytics-note">{safe_note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# LOGIN — NO CONNECTION TEST
# =====================================================================

if not st.session_state["logged_in"]:
    hero(
        "MegaServe Tiffin",
        "Simple daily ordering, live menu and admin reporting.",
    )

    left, center, right = st.columns([1, 1.15, 1])

    with center:
        st.markdown("### Welcome")

        with st.form("login_form"):
            username_input = st.text_input(
                "User ID",
                placeholder="Enter your user ID",
            )

            pin_input = st.text_input(
                "Password / PIN",
                type="password",
                placeholder="Enter your password",
            )

            login_clicked = st.form_submit_button(
                "Login",
                type="primary",
                use_container_width=True,
            )

        if login_clicked:
            if (
                not username_input.strip()
                or not pin_input.strip()
            ):
                st.error(
                    "Please enter both User ID and Password/PIN."
                )
            else:
                # Login uses a direct request because no session auth exists yet.
                try:
                    response = http_session().post(
                        GOOGLE_SCRIPT_URL,
                        json={
                            "action": "login",
                            "username": username_input.strip(),
                            "pin": pin_input.strip(),
                        },
                        timeout=REQUEST_TIMEOUT_SECONDS,
                        allow_redirects=True,
                    )

                    data = response.json()

                    if not data.get("ok", False):
                        raise AppError(
                            str(
                                data.get(
                                    "message",
                                    "Login failed.",
                                )
                            )
                        )

                    st.session_state["logged_in"] = True
                    st.session_state["role"] = str(
                        data.get("role", "")
                    )
                    st.session_state["member_id"] = str(
                        data.get("member_id", "")
                    )
                    st.session_state["username"] = str(
                        data.get(
                            "username",
                            username_input.strip().lower(),
                        )
                    )
                    st.session_state["pin"] = pin_input.strip()
                    st.session_state["person_name"] = str(
                        data.get("person_name", "")
                    )

                    st.rerun()

                except (requests.RequestException, ValueError, AppError) as exc:
                    st.error(str(exc))

    st.stop()


username = st.session_state["username"]
pin = st.session_state["pin"]
role = st.session_state["role"]
person_name = st.session_state["person_name"]


# =====================================================================
# TOP BAR
# =====================================================================

top_left, top_right = st.columns([8, 1])

with top_left:
    st.caption(
        f"Signed in as **{person_name}** · {role.title()} · UI {APP_UI_VERSION}"
    )

with top_right:
    if st.button(
        "Logout",
        use_container_width=True,
    ):
        logout()


# =====================================================================
# USER APP
# =====================================================================

if role == "user":
    hero(
        f"Hi {person_name} 👋",
        "Your tiffin, menu and account — without unnecessary loading.",
    )

    page = st.radio(
        "Navigation",
        [
            "🍱 Today",
            "🗓️ Monthly Report",
            "📊 My Stats",
            "⚙️ My Account",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="user_nav",
    )

    # -----------------------------------------------------------------
    # USER TODAY
    # -----------------------------------------------------------------

    if page == "🍱 Today":
        refresh = refresh_button(
            "user_home",
            "refresh_user_home",
        )

        try:
            data = lazy_load(
                "user_home",
                lambda: api_post("user_home"),
                ttl_seconds=6,
                force=refresh,
            )
        except AppError as exc:
            st.error(str(exc))
            st.stop()

        menu_card(
            str(data.get("today_menu", "") or ""),
            str(data.get("menu_updated_at", "") or ""),
        )

        open_now = bool(
            data.get(
                "can_user_update_today",
                False,
            )
        )

        window_badge(
            open_now,
            str(
                data.get(
                    "count_window",
                    "09:00 AM - 11:00 AM",
                )
            ),
            str(data.get("server_time", "")),
        )

        st.write("")

        m1, m2, m3 = st.columns(3)

        m1.metric(
            "This Month",
            f"{int(data.get('month_total', 0) or 0)} tiffins",
        )

        m2.metric(
            "Monthly Amount",
            format_money(
                data.get(
                    "monthly_amount",
                    0,
                )
            ),
        )

        m3.metric(
            "Tiffin Days",
            int(
                data.get(
                    "month_active_days",
                    0,
                )
                or 0
            ),
        )

        st.write("")

        saved = int(
            data.get(
                "today_count",
                0,
            )
            or 0
        )

        has_entry = bool(
            data.get(
                "today_has_entry",
                False,
            )
        )

        st.markdown(
            f"### Today's Count · {data.get('today_label', '')}"
        )

        if open_now:
            if has_entry:
                st.info(
                    f"Currently saved: **{saved}**. "
                    "You can change it again until 11:00 AM."
                )
            else:
                st.info(
                    "No count saved yet. Default count is 1."
                )

            with st.form("user_today_form"):
                count = st.number_input(
                    "Tiffin count",
                    min_value=0,
                    max_value=MAX_DAILY_COUNT,
                    value=(
                        saved
                        if has_entry
                        else 1
                    ),
                    step=1,
                )

                save_clicked = st.form_submit_button(
                    "Save / Update Count",
                    type="primary",
                    use_container_width=True,
                )

            if save_clicked:
                try:
                    result = api_post(
                        "update_today",
                        count=int(count),
                    )

                    clear_page_cache(
                        "user_home",
                        "admin_summary",
                        "admin_today_report",
                        "user_month_auto",
                        f"user_month_{date.today().strftime('%Y-%m')}",
                        "admin_month_auto",
                        f"admin_month_{date.today().strftime('%Y-%m')}",
                    )

                    st.success(
                        result.get(
                            "message",
                            "Count updated.",
                        )
                    )
                    st.rerun()

                except AppError as exc:
                    st.error(str(exc))

        else:
            st.warning(
                "User editing is closed. "
                "Only the administrator can change today's count now."
            )

            st.number_input(
                "Tiffin count",
                min_value=0,
                max_value=MAX_DAILY_COUNT,
                value=(
                    saved
                    if has_entry
                    else 1
                ),
                disabled=True,
                key="closed_user_count",
            )

    # -----------------------------------------------------------------
    # USER MONTHLY REPORT — LAZY BY SELECTED MONTH
    # -----------------------------------------------------------------

    elif page == "🗓️ Monthly Report":
        try:
            base_report = lazy_load(
                "user_month_auto",
                lambda: api_post(
                    "user_monthly_report",
                    month="",
                ),
                ttl_seconds=60,
            )
        except AppError as exc:
            st.error(str(exc))
            st.stop()

        month_options = base_report.get(
            "available_months",
            [],
        )

        if not month_options:
            st.info("No monthly data is available yet.")
            st.stop()

        month_labels = {
            str(item.get("key", "")):
            str(item.get("label", ""))
            for item in month_options
        }

        month_keys = [
            str(item.get("key", ""))
            for item in month_options
        ]

        default_month = str(
            base_report.get(
                "selected_month",
                month_keys[0],
            )
        )

        if default_month not in month_keys:
            default_month = month_keys[0]

        selected_month = st.selectbox(
            "Select month",
            month_keys,
            index=month_keys.index(default_month),
            format_func=lambda key: month_labels.get(
                key,
                key,
            ),
            key="user_month_selector",
        )

        cache_key = (
            f"user_month_{selected_month}"
        )

        refresh = refresh_button(
            cache_key,
            "refresh_user_month",
        )

        if (
            selected_month ==
            str(
                base_report.get(
                    "selected_month",
                    "",
                )
            )
            and not refresh
        ):
            report = base_report
        else:
            try:
                report = lazy_load(
                    cache_key,
                    lambda: api_post(
                        "user_monthly_report",
                        month=selected_month,
                    ),
                    ttl_seconds=60,
                    force=refresh,
                )
            except AppError as exc:
                st.error(str(exc))
                st.stop()

        st.markdown(
            f"### {report.get('month_label', selected_month)} report"
        )

        m1, m2, m3, m4, m5 = st.columns(5)

        m1.metric(
            "Total Tiffins",
            int(report.get("total_tiffins", 0) or 0),
        )

        m2.metric(
            "Amount",
            format_money(
                report.get("amount", 0)
            ),
        )

        m3.metric(
            "Order Days",
            int(report.get("active_days", 0) or 0),
        )

        m4.metric(
            "Submitted Days",
            int(report.get("submitted_days", 0) or 0),
        )

        m5.metric(
            "Avg / Order Day",
            f"{float(report.get('average_per_active_day', 0) or 0):.2f}",
        )

        details = report.get(
            "details",
            [],
        )

        if details:
            st.markdown("### Daily order pattern")

            st.bar_chart(
                [
                    {
                        "Date": item.get("date", ""),
                        "Tiffins": int(
                            item.get("count", 0) or 0
                        ),
                    }
                    for item in details
                ],
                x="Date",
                y="Tiffins",
                use_container_width=True,
            )

            st.markdown("### Daily details")

            st.dataframe(
                [
                    {
                        "Date": item.get("date", ""),
                        "Day": item.get("day", ""),
                        "Status": item.get("status", ""),
                        "Tiffins": item.get("count", 0),
                        "Amount": item.get("amount", 0),
                    }
                    for item in details
                ],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info(
                "There are no tracker rows for this month."
            )

    # -----------------------------------------------------------------
    # USER STATS — ONLY CALCULATED WHEN OPENED
    # -----------------------------------------------------------------

    elif page == "📊 My Stats":
        refresh = refresh_button(
            "user_stats",
            "refresh_user_stats",
        )

        with st.spinner(
            "Loading your history only because you opened this page..."
        ):
            try:
                data = lazy_load(
                    "user_stats",
                    lambda: api_post("user_stats"),
                    ttl_seconds=20,
                    force=refresh,
                )
            except AppError as exc:
                st.error(str(exc))
                st.stop()

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "This Month",
            int(data.get("month_total", 0) or 0),
        )

        c2.metric(
            "This Month Amount",
            format_money(
                data.get(
                    "monthly_amount",
                    0,
                )
            ),
        )

        c3.metric(
            "Outstanding Due",
            format_money(
                data.get(
                    "total_outstanding_due",
                    0,
                )
            ),
        )

        c4.metric(
            "Overall Tiffins",
            int(data.get("overall_total", 0) or 0),
        )

        dues = data.get("dues_history", [])

        if dues:
            st.markdown("### Monthly dues")

            st.dataframe(
                [
                    {
                        "Month": x.get("month_label", ""),
                        "Tiffins": x.get("tiffins", 0),
                        "Amount": x.get("amount", 0),
                        "Status": (
                            "PAID"
                            if x.get("paid")
                            else "UNPAID"
                        ),
                        "Paid On": x.get("paid_on", ""),
                    }
                    for x in dues
                ],
                hide_index=True,
                use_container_width=True,
            )

        history = data.get("history", [])

        if history:
            st.markdown("### Recent entries")

            st.dataframe(
                [
                    {
                        "Date": x.get("date", ""),
                        "Tiffins": x.get("count", 0),
                        "Amount": x.get("amount", 0),
                    }
                    for x in history
                ],
                hide_index=True,
                use_container_width=True,
            )

    # -----------------------------------------------------------------
    # USER ACCOUNT
    # -----------------------------------------------------------------

    elif page == "⚙️ My Account":
        st.markdown("### Change login details")

        with st.form("user_credentials_form"):
            new_username = st.text_input(
                "User ID",
                value=username,
            )

            new_pin = st.text_input(
                "New Password / PIN",
                type="password",
                placeholder="Leave blank to keep current password",
            )

            update_clicked = st.form_submit_button(
                "Update Login",
                type="primary",
                use_container_width=True,
            )

        if update_clicked:
            try:
                result = api_post(
                    "change_credentials",
                    new_username=new_username,
                    new_pin=new_pin,
                )

                st.session_state["username"] = str(
                    result.get(
                        "username",
                        new_username,
                    )
                )

                if new_pin.strip():
                    st.session_state["pin"] = new_pin.strip()

                st.success("Login details updated.")
                st.rerun()

            except AppError as exc:
                st.error(str(exc))

    st.stop()


# =====================================================================
# ADMIN APP
# =====================================================================

if role == "admin":
    hero(
        "MegaServe Tiffin Control",
        "Live ordering, service-center reporting and member administration.",
    )

    page = st.radio(
        "Admin navigation",
        [
            "🏠 Dashboard",
            "📋 Today Report",
            "📅 Monthly Analytics",
            "🗓️ Day Report",
            "🍽️ Today Menu",
            "👥 Members",
            "💰 Dues",
            "⚙️ Account",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="admin_nav",
    )

    # -----------------------------------------------------------------
    # DASHBOARD — LIGHTWEIGHT
    # -----------------------------------------------------------------

    if page == "🏠 Dashboard":
        refresh = refresh_button(
            "admin_summary",
            "refresh_admin_dashboard",
        )

        try:
            data = lazy_load(
                "admin_summary",
                lambda: api_post("admin_summary"),
                ttl_seconds=6,
                force=refresh,
            )
        except AppError as exc:
            st.error(str(exc))
            st.stop()

        window_open = bool(
            data.get(
                "user_count_window_open",
                False,
            )
        )

        window_badge(
            window_open,
            str(data.get("count_window", "")),
            str(data.get("server_time", "")),
        )

        st.write("")

        active_members = int(
            data.get("active_members", 0) or 0
        )
        submitted_members = int(
            data.get("submitted_members", 0) or 0
        )
        ordering_persons = int(
            data.get("ordering_persons", 0) or 0
        )
        total_tiffins = int(
            data.get("total_tiffins_today", 0) or 0
        )
        pending_members = int(
            data.get("pending_members", 0) or 0
        )
        zero_members = int(
            data.get("zero_count_members", 0) or 0
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Active Members",
            active_members,
        )

        c2.metric(
            "Submitted",
            submitted_members,
        )

        c3.metric(
            "Ordering",
            ordering_persons,
        )

        c4.metric(
            "Total Tiffins",
            total_tiffins,
        )

        c5.metric(
            "Pending",
            pending_members,
        )

        rate = float(
            data.get(
                "submission_rate",
                0,
            )
            or 0
        )

        st.markdown(
            f"**Submission progress · {rate:.1f}%**"
        )

        st.progress(
            max(
                0.0,
                min(
                    1.0,
                    rate / 100.0,
                ),
            )
        )

        # -------------------------------------------------------------
        # QUICK ANALYTICS — computed locally from already-loaded data.
        # No extra API / Google Sheet request.
        # -------------------------------------------------------------

        orders = data.get("orders", [])

        average_per_orderer = (
            total_tiffins / ordering_persons
            if ordering_persons > 0
            else 0
        )

        largest_order = 0
        largest_order_name = "—"

        if orders:
            largest = max(
                orders,
                key=lambda x: int(
                    x.get("count", 0) or 0
                ),
            )
            largest_order = int(
                largest.get("count", 0) or 0
            )
            largest_order_name = str(
                largest.get("person_name", "—")
            )

        insight1, insight2, insight3 = st.columns(3)

        with insight1:
            analytics_card(
                "Average order",
                f"{average_per_orderer:.2f}",
                "Tiffins per ordering person",
            )

        with insight2:
            analytics_card(
                "Largest order",
                str(largest_order),
                largest_order_name,
            )

        with insight3:
            analytics_card(
                "Current status",
                (
                    "Live"
                    if window_open
                    else "Cutoff complete"
                ),
                (
                    "Users may still edit"
                    if window_open
                    else "Admin-only corrections"
                ),
            )

        st.markdown("### Today at a glance")

        chart_left, chart_right = st.columns([1, 1.35])

        with chart_left:
            st.caption(
                "Submission mix · uses the dashboard data already loaded"
            )

            submission_chart = [
                {
                    "Status": "Ordering",
                    "People": ordering_persons,
                },
                {
                    "Status": "No Tiffin",
                    "People": zero_members,
                },
                {
                    "Status": "Pending",
                    "People": pending_members,
                },
            ]

            st.bar_chart(
                submission_chart,
                x="Status",
                y="People",
                use_container_width=True,
            )

        with chart_right:
            st.caption(
                "Tiffins by person · positive orders only"
            )

            if orders:
                order_chart = [
                    {
                        "Name": str(
                            item.get(
                                "person_name",
                                "",
                            )
                        ),
                        "Tiffins": int(
                            item.get(
                                "count",
                                0,
                            )
                            or 0
                        ),
                    }
                    for item in sorted(
                        orders,
                        key=lambda x: int(
                            x.get("count", 0) or 0
                        ),
                        reverse=True,
                    )
                ]

                st.bar_chart(
                    order_chart,
                    x="Name",
                    y="Tiffins",
                    use_container_width=True,
                )
            else:
                st.info(
                    "Positive orders will appear here as users submit counts."
                )

        st.markdown("### Operations")

        left, right = st.columns([1.15, 1])

        with left:
            st.markdown("#### Today's order list")

            if orders:
                st.dataframe(
                    [
                        {
                            "Name": x.get("person_name", ""),
                            "Count": x.get("count", 0),
                        }
                        for x in orders
                    ],
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.info("No positive tiffin orders yet.")

        with right:
            menu_card(
                str(
                    data.get(
                        "today_menu",
                        "",
                    )
                    or ""
                ),
                str(
                    data.get(
                        "menu_updated_at",
                        "",
                    )
                    or ""
                ),
            )

            pending = data.get(
                "pending_names",
                [],
            )

            if pending:
                st.markdown("#### Pending members")

                st.caption(
                    ", ".join(
                        str(x)
                        for x in pending
                    )
                )
            else:
                st.success(
                    "All active members have submitted."
                )

    # -----------------------------------------------------------------
    # TODAY REPORT + ADMIN COUNT CORRECTION
    # -----------------------------------------------------------------

    elif page == "📋 Today Report":
        refresh = refresh_button(
            "admin_today_report",
            "refresh_today_report",
        )

        try:
            data = lazy_load(
                "admin_today_report",
                lambda: api_post("admin_today_report"),
                ttl_seconds=5,
                force=refresh,
            )
        except AppError as exc:
            st.error(str(exc))
            st.stop()

        is_open = bool(
            data.get(
                "user_count_window_open",
                False,
            )
        )

        window_badge(
            is_open,
            str(data.get("count_window", "")),
            str(data.get("server_time", "")),
        )

        st.write("")

        if is_open:
            st.info(
                "This is a LIVE report. Users can still change counts before 11:00 AM."
            )
        else:
            st.success(
                "User cutoff is over. This report is ready to send to the service center."
            )

        r1, r2, r3, r4, r5 = st.columns(5)

        r1.metric(
            "Total Tiffins",
            int(data.get("total_tiffins_today", 0) or 0),
        )

        r2.metric(
            "Persons Ordering",
            int(data.get("ordering_persons", 0) or 0),
        )

        r3.metric(
            "Submitted",
            int(data.get("submitted_members", 0) or 0),
        )

        r4.metric(
            "No Tiffin",
            int(data.get("zero_count_members", 0) or 0),
        )

        r5.metric(
            "Pending",
            int(data.get("pending_members", 0) or 0),
        )

        positive = data.get(
            "positive_orders",
            [],
        )

        zero_orders = data.get(
            "zero_orders",
            [],
        )

        pending = data.get(
            "pending",
            [],
        )

        st.markdown("### Report analytics")

        report_chart_left, report_chart_right = st.columns([1, 1.4])

        with report_chart_left:
            status_chart = [
                {
                    "Status": "Ordering",
                    "People": int(
                        data.get(
                            "ordering_persons",
                            0,
                        )
                        or 0
                    ),
                },
                {
                    "Status": "No Tiffin",
                    "People": int(
                        data.get(
                            "zero_count_members",
                            0,
                        )
                        or 0
                    ),
                },
                {
                    "Status": "Pending",
                    "People": int(
                        data.get(
                            "pending_members",
                            0,
                        )
                        or 0
                    ),
                },
            ]

            st.bar_chart(
                status_chart,
                x="Status",
                y="People",
                use_container_width=True,
            )

        with report_chart_right:
            if positive:
                positive_chart = [
                    {
                        "Name": str(
                            x.get(
                                "person_name",
                                "",
                            )
                        ),
                        "Tiffins": int(
                            x.get(
                                "count",
                                0,
                            )
                            or 0
                        ),
                    }
                    for x in sorted(
                        positive,
                        key=lambda item: int(
                            item.get(
                                "count",
                                0,
                            )
                            or 0
                        ),
                        reverse=True,
                    )
                ]

                st.bar_chart(
                    positive_chart,
                    x="Name",
                    y="Tiffins",
                    use_container_width=True,
                )
            else:
                st.info(
                    "No positive orders to chart yet."
                )

        st.markdown("### Service-center message")

        report_text = str(
            data.get(
                "service_report_text",
                "",
            )
        )

        st.code(
            report_text,
            language=None,
        )

        st.download_button(
            "Download report as TXT",
            data=report_text.encode("utf-8"),
            file_name="tiffin_report_today.txt",
            mime="text/plain",
            use_container_width=True,
        )

        if positive:
            st.markdown("### Positive orders")

            st.dataframe(
                [
                    {
                        "Name": x.get("person_name", ""),
                        "User ID": x.get("username", ""),
                        "Count": x.get("count", 0),
                    }
                    for x in positive
                ],
                hide_index=True,
                use_container_width=True,
            )

            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(
                ["Name", "User ID", "Count"]
            )

            for x in positive:
                writer.writerow(
                    [
                        x.get("person_name", ""),
                        x.get("username", ""),
                        x.get("count", 0),
                    ]
                )

            st.download_button(
                "Download positive orders CSV",
                data=csv_buffer.getvalue().encode("utf-8"),
                file_name="tiffin_positive_orders.csv",
                mime="text/csv",
                use_container_width=True,
            )

        zcol, pcol = st.columns(2)

        with zcol:
            st.markdown("### Submitted 0")

            if zero_orders:
                st.caption(
                    ", ".join(
                        x.get("person_name", "")
                        for x in zero_orders
                    )
                )
            else:
                st.caption("None")

        with pcol:
            st.markdown("### Not submitted")

            if pending:
                st.caption(
                    ", ".join(
                        x.get("person_name", "")
                        for x in pending
                    )
                )
            else:
                st.caption("Everyone submitted.")

        st.divider()
        st.markdown("### Admin correction")

        all_rows = data.get("rows", [])

        if all_rows:
            lookup = {
                f"{x.get('person_name', '')} ({x.get('username', '')})": x
                for x in all_rows
            }

            selected_label = st.selectbox(
                "Select member",
                list(lookup.keys()),
                key="admin_today_member",
            )

            selected = lookup[selected_label]

            has_entry = bool(
                selected.get(
                    "submitted",
                    False,
                )
            )

            current = int(
                selected.get(
                    "count",
                    0,
                )
                or 0
            )

            with st.form("admin_correct_count_form"):
                corrected = st.number_input(
                    "Today's count",
                    min_value=0,
                    max_value=MAX_DAILY_COUNT,
                    value=(
                        current
                        if has_entry
                        else 1
                    ),
                    step=1,
                )

                correct_clicked = st.form_submit_button(
                    "Set / Correct Count",
                    type="primary",
                    use_container_width=True,
                )

            if correct_clicked:
                try:
                    result = api_post(
                        "admin_update_today_count",
                        target_member_id=selected.get(
                            "member_id",
                            "",
                        ),
                        count=int(corrected),
                    )

                    clear_page_cache(
                        "admin_today_report",
                        "admin_summary",
                        "admin_month_auto",
                        f"admin_month_{date.today().strftime('%Y-%m')}",
                        "user_month_auto",
                        f"user_month_{date.today().strftime('%Y-%m')}",
                    )

                    st.success(
                        result.get(
                            "message",
                            "Count updated.",
                        )
                    )
                    st.rerun()

                except AppError as exc:
                    st.error(str(exc))

    # -----------------------------------------------------------------
    # MONTHLY ANALYTICS — LAZY BY SELECTED MONTH
    # -----------------------------------------------------------------

    elif page == "📅 Monthly Analytics":
        try:
            base_report = lazy_load(
                "admin_month_auto",
                lambda: api_post(
                    "admin_monthly_report",
                    month="",
                ),
                ttl_seconds=60,
            )
        except AppError as exc:
            st.error(str(exc))
            st.stop()

        month_options = base_report.get(
            "available_months",
            [],
        )

        if not month_options:
            st.info("No monthly data is available yet.")
            st.stop()

        month_labels = {
            str(item.get("key", "")):
            str(item.get("label", ""))
            for item in month_options
        }

        month_keys = [
            str(item.get("key", ""))
            for item in month_options
        ]

        default_month = str(
            base_report.get(
                "selected_month",
                month_keys[0],
            )
        )

        if default_month not in month_keys:
            default_month = month_keys[0]

        selected_month = st.selectbox(
            "Select month",
            month_keys,
            index=month_keys.index(default_month),
            format_func=lambda key: month_labels.get(
                key,
                key,
            ),
            key="admin_month_selector",
        )

        cache_key = (
            f"admin_month_{selected_month}"
        )

        refresh = refresh_button(
            cache_key,
            "refresh_admin_month",
        )

        if (
            selected_month ==
            str(
                base_report.get(
                    "selected_month",
                    "",
                )
            )
            and not refresh
        ):
            report = base_report
        else:
            try:
                report = lazy_load(
                    cache_key,
                    lambda: api_post(
                        "admin_monthly_report",
                        month=selected_month,
                    ),
                    ttl_seconds=60,
                    force=refresh,
                )
            except AppError as exc:
                st.error(str(exc))
                st.stop()

        st.markdown(
            f"### {report.get('month_label', selected_month)} analytics"
        )

        st.caption(
            "Historical analytics are calculated directly from Monthly Tracker data."
        )

        top_member = report.get(
            "top_member",
            None,
        ) or {}

        a1, a2, a3, a4, a5 = st.columns(5)

        a1.metric(
            "Total Tiffins",
            int(report.get("total_tiffins", 0) or 0),
        )

        a2.metric(
            "Total Value",
            format_money(
                report.get("total_amount", 0)
            ),
        )

        a3.metric(
            "Order Days",
            int(report.get("days_with_orders", 0) or 0),
        )

        a4.metric(
            "Avg / Order Day",
            f"{float(report.get('average_tiffins_per_order_day', 0) or 0):.2f}",
        )

        a5.metric(
            "Top Member",
            str(
                top_member.get(
                    "person_name",
                    "—",
                )
            ),
            delta=(
                f"{int(top_member.get('total_tiffins', 0) or 0)} tiffins"
                if top_member
                else None
            ),
        )

        members = report.get(
            "members",
            [],
        )

        daily_rows = report.get(
            "daily_rows",
            [],
        )

        chart1, chart2 = st.columns([1.25, 1])

        with chart1:
            st.markdown("#### Tiffins by member")

            positive_members = [
                row
                for row in members
                if int(
                    row.get(
                        "total_tiffins",
                        0,
                    )
                    or 0
                ) > 0
            ]

            if positive_members:
                st.bar_chart(
                    [
                        {
                            "Name": row.get(
                                "person_name",
                                "",
                            ),
                            "Tiffins": int(
                                row.get(
                                    "total_tiffins",
                                    0,
                                )
                                or 0
                            ),
                        }
                        for row in positive_members
                    ],
                    x="Name",
                    y="Tiffins",
                    use_container_width=True,
                )
            else:
                st.info(
                    "No positive orders in this month."
                )

        with chart2:
            st.markdown("#### Daily tiffin trend")

            if daily_rows:
                st.line_chart(
                    [
                        {
                            "Date": row.get("date", ""),
                            "Tiffins": int(
                                row.get(
                                    "total_tiffins",
                                    0,
                                )
                                or 0
                            ),
                        }
                        for row in daily_rows
                    ],
                    x="Date",
                    y="Tiffins",
                    use_container_width=True,
                )
            else:
                st.info(
                    "No daily rows for this month."
                )

        st.markdown("### Member breakdown")

        if members:
            st.dataframe(
                [
                    {
                        "Name": row.get("person_name", ""),
                        "User ID": row.get("username", ""),
                        "Tiffins": row.get("total_tiffins", 0),
                        "Order Days": row.get("active_days", 0),
                        "Submitted Days": row.get("submitted_days", 0),
                        "Zero Days": row.get("zero_days", 0),
                        "Avg / Order Day": row.get(
                            "average_per_active_day",
                            0,
                        ),
                        "Amount": row.get("amount", 0),
                    }
                    for row in members
                ],
                hide_index=True,
                use_container_width=True,
            )

        st.markdown("### Daily breakdown")

        if daily_rows:
            st.dataframe(
                [
                    {
                        "Date": row.get("date", ""),
                        "Day": row.get("day", ""),
                        "Total Tiffins": row.get(
                            "total_tiffins",
                            0,
                        ),
                        "Ordering": row.get(
                            "ordering_persons",
                            0,
                        ),
                        "Submitted": row.get(
                            "submitted",
                            0,
                        ),
                        "No Tiffin": row.get(
                            "zero_count",
                            0,
                        ),
                        "Pending": row.get(
                            "pending",
                            0,
                        ),
                    }
                    for row in daily_rows
                ],
                hide_index=True,
                use_container_width=True,
            )

    # -----------------------------------------------------------------
    # DAY REPORT — ANY TODAY/PAST DATE + ADMIN CORRECTION
    # -----------------------------------------------------------------

    elif page == "🗓️ Day Report":
        selected_date = st.date_input(
            "Select date",
            value=date.today(),
            max_value=date.today(),
            key="admin_day_picker",
        )

        date_key = selected_date.isoformat()
        cache_key = f"admin_day_{date_key}"

        refresh = refresh_button(
            cache_key,
            "refresh_admin_day",
        )

        try:
            report = lazy_load(
                cache_key,
                lambda: api_post(
                    "admin_day_report",
                    date=date_key,
                ),
                ttl_seconds=20,
                force=refresh,
            )
        except AppError as exc:
            st.error(str(exc))
            st.stop()

        st.markdown(
            f"### Day report · {report.get('date_label', date_key)}"
        )

        st.caption(
            "Historical values come directly from Monthly Tracker and can be corrected by admin."
        )

        d1, d2, d3, d4, d5 = st.columns(5)

        d1.metric(
            "Total Tiffins",
            int(report.get("total_tiffins", 0) or 0),
        )

        d2.metric(
            "Ordering",
            int(report.get("ordering_persons", 0) or 0),
        )

        d3.metric(
            "Submitted",
            int(report.get("submitted_members", 0) or 0),
        )

        d4.metric(
            "No Tiffin",
            int(report.get("zero_count_members", 0) or 0),
        )

        d5.metric(
            "Pending",
            int(report.get("pending_members", 0) or 0),
        )

        all_rows = report.get(
            "rows",
            [],
        )

        positive = report.get(
            "positive_orders",
            [],
        )

        chart_left, chart_right = st.columns([1, 1.4])

        with chart_left:
            st.bar_chart(
                [
                    {
                        "Status": "Ordering",
                        "People": int(
                            report.get(
                                "ordering_persons",
                                0,
                            )
                            or 0
                        ),
                    },
                    {
                        "Status": "No Tiffin",
                        "People": int(
                            report.get(
                                "zero_count_members",
                                0,
                            )
                            or 0
                        ),
                    },
                    {
                        "Status": "Pending",
                        "People": int(
                            report.get(
                                "pending_members",
                                0,
                            )
                            or 0
                        ),
                    },
                ],
                x="Status",
                y="People",
                use_container_width=True,
            )

        with chart_right:
            if positive:
                st.bar_chart(
                    [
                        {
                            "Name": row.get(
                                "person_name",
                                "",
                            ),
                            "Tiffins": int(
                                row.get(
                                    "count",
                                    0,
                                )
                                or 0
                            ),
                        }
                        for row in positive
                    ],
                    x="Name",
                    y="Tiffins",
                    use_container_width=True,
                )
            else:
                st.info(
                    "No positive orders on this date."
                )

        st.markdown("### Service-center style report")

        report_text = str(
            report.get(
                "service_report_text",
                "",
            )
        )

        st.code(
            report_text,
            language=None,
        )

        st.download_button(
            "Download day report",
            data=report_text.encode("utf-8"),
            file_name=(
                f"tiffin_report_{date_key}.txt"
            ),
            mime="text/plain",
            use_container_width=True,
        )

        st.markdown("### Member details")

        if all_rows:
            st.dataframe(
                [
                    {
                        "Name": row.get("person_name", ""),
                        "User ID": row.get("username", ""),
                        "Status": (
                            "Ordered"
                            if (
                                row.get("submitted")
                                and int(
                                    row.get("count", 0)
                                    or 0
                                ) > 0
                            )
                            else (
                                "No Tiffin"
                                if row.get("submitted")
                                else "Pending"
                            )
                        ),
                        "Count": row.get("count", 0),
                    }
                    for row in all_rows
                ],
                hide_index=True,
                use_container_width=True,
            )

            st.divider()
            st.markdown(
                "### Correct count for this date"
            )

            lookup = {
                f"{row.get('person_name', '')} ({row.get('username', '')})": row
                for row in all_rows
            }

            selected_label = st.selectbox(
                "Select member",
                list(lookup.keys()),
                key="admin_day_member_selector",
            )

            selected_row = lookup[selected_label]

            has_entry = bool(
                selected_row.get(
                    "submitted",
                    False,
                )
            )

            current_count = int(
                selected_row.get(
                    "count",
                    0,
                )
                or 0
            )

            with st.form("admin_day_count_form"):
                corrected_count = st.number_input(
                    "Count",
                    min_value=0,
                    max_value=MAX_DAILY_COUNT,
                    value=(
                        current_count
                        if has_entry
                        else 1
                    ),
                    step=1,
                )

                update_day_clicked = st.form_submit_button(
                    "Update Selected Day",
                    type="primary",
                    use_container_width=True,
                )

            if update_day_clicked:
                try:
                    result = api_post(
                        "admin_update_day_count",
                        target_member_id=selected_row.get(
                            "member_id",
                            "",
                        ),
                        date=date_key,
                        count=int(corrected_count),
                    )

                    clear_page_cache(
                        cache_key,
                        "admin_today_report",
                        "admin_summary",
                        "admin_month_auto",
                        f"admin_month_{date_key[:7]}",
                        "user_month_auto",
                        f"user_month_{date_key[:7]}",
                        "admin_dues",
                        "user_stats",
                    )

                    st.success(
                        result.get(
                            "message",
                            "Count updated.",
                        )
                    )
                    st.rerun()

                except AppError as exc:
                    st.error(str(exc))

    # -----------------------------------------------------------------
    # MENU
    # -----------------------------------------------------------------

    elif page == "🍽️ Today Menu":
        try:
            summary = lazy_load(
                "admin_summary",
                lambda: api_post("admin_summary"),
                ttl_seconds=6,
            )
        except AppError as exc:
            st.error(str(exc))
            st.stop()

        current_menu = str(
            summary.get(
                "today_menu",
                "",
            )
            or ""
        )

        menu_card(
            current_menu,
            str(
                summary.get(
                    "menu_updated_at",
                    "",
                )
                or ""
            ),
        )

        with st.form("admin_menu_form"):
            menu_text = st.text_area(
                "Today's menu",
                value=current_menu,
                height=220,
                placeholder=(
                    "Example:\n"
                    "Dal Tadka\n"
                    "Jeera Rice\n"
                    "4 Roti\n"
                    "Mix Veg\n"
                    "Salad"
                ),
            )

            save_menu = st.form_submit_button(
                "Publish Today's Menu",
                type="primary",
                use_container_width=True,
            )

        if save_menu:
            try:
                result = api_post(
                    "admin_update_today_menu",
                    menu=menu_text,
                )

                clear_page_cache(
                    "admin_summary",
                    "user_home",
                )

                st.success(
                    result.get(
                        "message",
                        "Menu updated.",
                    )
                )
                st.rerun()

            except AppError as exc:
                st.error(str(exc))

        if st.button(
            "Clear Today's Menu",
            use_container_width=True,
        ):
            try:
                result = api_post(
                    "admin_update_today_menu",
                    menu="",
                )

                clear_page_cache(
                    "admin_summary",
                    "user_home",
                )

                st.success(
                    result.get(
                        "message",
                        "Menu cleared.",
                    )
                )
                st.rerun()

            except AppError as exc:
                st.error(str(exc))

        st.caption(
            "The menu is optional. Tiffin count entry works independently."
        )

    # -----------------------------------------------------------------
    # MEMBERS — ONLY LOADS USER DETAILS
    # -----------------------------------------------------------------

    elif page == "👥 Members":
        refresh = refresh_button(
            "admin_members",
            "refresh_members",
        )

        try:
            data = lazy_load(
                "admin_members",
                lambda: api_post("admin_members"),
                ttl_seconds=15,
                force=refresh,
            )
        except AppError as exc:
            st.error(str(exc))
            st.stop()

        members = data.get("members", [])

        m1, m2 = st.columns(2)

        m1.metric(
            "Total Members",
            int(data.get("total_members", 0) or 0),
        )

        m2.metric(
            "Active Members",
            int(data.get("active_members", 0) or 0),
        )

        if members:
            st.dataframe(
                [
                    {
                        "Member ID": x.get("member_id", ""),
                        "Name": x.get("person_name", ""),
                        "User ID": x.get("username", ""),
                        "Status": (
                            "Active"
                            if x.get("active")
                            else "Inactive"
                        ),
                        "Notes": x.get("notes", ""),
                    }
                    for x in members
                ],
                hide_index=True,
                use_container_width=True,
            )

        add_tab, edit_tab = st.tabs(
            ["Add Member", "Edit Member"]
        )

        with add_tab:
            with st.form("add_member_form"):
                a1, a2 = st.columns(2)

                with a1:
                    new_user = st.text_input(
                        "New User ID"
                    )

                    new_name = st.text_input(
                        "Person Name"
                    )

                with a2:
                    new_pin = st.text_input(
                        "Password / PIN",
                        type="password",
                    )

                    new_active = st.checkbox(
                        "Active",
                        value=True,
                    )

                new_notes = st.text_input("Notes")

                add_clicked = st.form_submit_button(
                    "Add Member",
                    type="primary",
                    use_container_width=True,
                )

            if add_clicked:
                try:
                    result = api_post(
                        "admin_add_member",
                        new_username=new_user,
                        new_pin=new_pin,
                        person_name=new_name,
                        active=new_active,
                        notes=new_notes,
                    )

                    clear_page_cache(
                        "admin_members",
                        "admin_summary",
                        "admin_today_report",
                    )

                    st.success(
                        result.get(
                            "message",
                            "Member added.",
                        )
                    )
                    st.rerun()

                except AppError as exc:
                    st.error(str(exc))

        with edit_tab:
            if not members:
                st.info("No members available.")
            else:
                lookup = {
                    f"{x.get('person_name', '')} ({x.get('username', '')})": x
                    for x in members
                }

                label = st.selectbox(
                    "Select member",
                    list(lookup.keys()),
                    key="edit_member_select",
                )

                selected = lookup[label]

                with st.form("edit_member_form"):
                    edit_user = st.text_input(
                        "User ID",
                        value=str(
                            selected.get(
                                "username",
                                "",
                            )
                        ),
                    )

                    edit_name = st.text_input(
                        "Person Name",
                        value=str(
                            selected.get(
                                "person_name",
                                "",
                            )
                        ),
                    )

                    edit_pin = st.text_input(
                        "New Password / PIN",
                        type="password",
                        placeholder="Leave blank to keep current password",
                    )

                    edit_notes = st.text_input(
                        "Notes",
                        value=str(
                            selected.get(
                                "notes",
                                "",
                            )
                        ),
                    )

                    edit_clicked = st.form_submit_button(
                        "Update Member",
                        type="primary",
                        use_container_width=True,
                    )

                if edit_clicked:
                    try:
                        result = api_post(
                            "admin_update_member",
                            target_member_id=selected.get(
                                "member_id",
                                "",
                            ),
                            new_username=edit_user,
                            new_pin=edit_pin,
                            new_person_name=edit_name,
                            notes=edit_notes,
                        )

                        clear_page_cache(
                            "admin_members",
                            "admin_summary",
                            "admin_today_report",
                        )

                        st.success(
                            result.get(
                                "message",
                                "Member updated.",
                            )
                        )
                        st.rerun()

                    except AppError as exc:
                        st.error(str(exc))

                if bool(selected.get("active", False)):
                    if st.button(
                        "Mark Inactive",
                        use_container_width=True,
                    ):
                        try:
                            api_post(
                                "admin_set_active",
                                target_member_id=selected.get(
                                    "member_id",
                                    "",
                                ),
                                active=False,
                            )

                            clear_page_cache(
                                "admin_members",
                                "admin_summary",
                                "admin_today_report",
                            )

                            st.rerun()
                        except AppError as exc:
                            st.error(str(exc))
                else:
                    if st.button(
                        "Mark Active",
                        use_container_width=True,
                    ):
                        try:
                            api_post(
                                "admin_set_active",
                                target_member_id=selected.get(
                                    "member_id",
                                    "",
                                ),
                                active=True,
                            )

                            clear_page_cache(
                                "admin_members",
                                "admin_summary",
                                "admin_today_report",
                            )

                            st.rerun()
                        except AppError as exc:
                            st.error(str(exc))

    # -----------------------------------------------------------------
    # DUES — HEAVY WORK HAPPENS ONLY HERE
    # -----------------------------------------------------------------

    elif page == "💰 Dues":
        top_a, top_b = st.columns([1, 1])

        with top_a:
            refresh = st.button(
                "↻ Refresh Dues",
                use_container_width=True,
            )

        with top_b:
            recalc = st.button(
                "⟳ Recalculate Completed Months",
                use_container_width=True,
            )

        if refresh:
            clear_page_cache("admin_dues")

        try:
            with st.spinner(
                "Loading dues only because you opened the Dues page..."
            ):
                if recalc:
                    data = api_post(
                        "admin_recalculate_dues"
                    )
                    clear_page_cache("admin_dues")
                else:
                    data = lazy_load(
                        "admin_dues",
                        lambda: api_post("admin_dues"),
                        ttl_seconds=30,
                        force=refresh,
                    )
        except AppError as exc:
            st.error(str(exc))
            st.stop()

        st.metric(
            "Total Outstanding",
            format_money(
                data.get(
                    "total_outstanding_due",
                    0,
                )
            ),
        )

        members = data.get("members", [])
        rows = data.get("rows", [])

        if members:
            st.markdown("### Member due summary")

            st.dataframe(
                [
                    {
                        "Name": x.get("person_name", ""),
                        "User ID": x.get("username", ""),
                        "Outstanding": x.get("total_due", 0),
                        "Unpaid Months": x.get("unpaid_months", 0),
                    }
                    for x in members
                ],
                hide_index=True,
                use_container_width=True,
            )

        if rows:
            st.markdown("### Monthly ledger")

            st.dataframe(
                [
                    {
                        "Name": x.get("person_name", ""),
                        "Month": x.get("month_label", ""),
                        "Tiffins": x.get("tiffins", 0),
                        "Amount": x.get("amount", 0),
                        "Status": (
                            "PAID"
                            if x.get("paid")
                            else "UNPAID"
                        ),
                        "Paid On": x.get("paid_on", ""),
                    }
                    for x in rows
                ],
                hide_index=True,
                use_container_width=True,
            )

            row_lookup = {
                (
                    f"{x.get('person_name', '')} · "
                    f"{x.get('month_label', '')} · "
                    f"{'PAID' if x.get('paid') else 'UNPAID'}"
                ): x
                for x in rows
            }

            selected_label = st.selectbox(
                "Change payment status",
                list(row_lookup.keys()),
            )

            selected_row = row_lookup[
                selected_label
            ]

            new_status = st.radio(
                "Status",
                ["PAID", "UNPAID"],
                horizontal=True,
                index=(
                    0
                    if selected_row.get("paid")
                    else 1
                ),
            )

            if st.button(
                "Update Payment Status",
                type="primary",
                use_container_width=True,
            ):
                try:
                    result = api_post(
                        "admin_set_payment",
                        target_member_id=selected_row.get(
                            "member_id",
                            "",
                        ),
                        month=selected_row.get(
                            "month",
                            "",
                        ),
                        paid=(
                            new_status == "PAID"
                        ),
                    )

                    clear_page_cache("admin_dues")

                    st.success(
                        result.get(
                            "message",
                            "Payment updated.",
                        )
                    )
                    st.rerun()

                except AppError as exc:
                    st.error(str(exc))

    # -----------------------------------------------------------------
    # ADMIN ACCOUNT
    # -----------------------------------------------------------------

    elif page == "⚙️ Account":
        st.markdown("### Administrator login")

        with st.form("admin_credentials_form"):
            new_username = st.text_input(
                "Admin User ID",
                value=username,
            )

            new_pin = st.text_input(
                "New Password / PIN",
                type="password",
                placeholder="Leave blank to keep current password",
            )

            update_clicked = st.form_submit_button(
                "Update Administrator Login",
                type="primary",
                use_container_width=True,
            )

        if update_clicked:
            try:
                result = api_post(
                    "change_credentials",
                    new_username=new_username,
                    new_pin=new_pin,
                )

                st.session_state["username"] = str(
                    result.get(
                        "username",
                        new_username,
                    )
                )

                if new_pin.strip():
                    st.session_state["pin"] = new_pin.strip()

                st.success("Administrator login updated.")
                st.rerun()

            except AppError as exc:
                st.error(str(exc))

    st.stop()


# =====================================================================
# INVALID SESSION ROLE
# =====================================================================

st.warning(
    "This login session is invalid or belongs to an older app version."
)

if st.button(
    "Reset Session & Login Again",
    type="primary",
):
    logout()
