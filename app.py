from __future__ import annotations

import logging
from typing import Any

import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# CONFIGURATION
# ============================================================

GOOGLE_SCRIPT_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbwNBXfLdk5VWmvyRYyuG6SYJtqYb8OFuhFfynrZ211bOn0m9lN3yuzv8ox66iQJHnA/"
    "exec"
)

EXPECTED_CODE_VERSION = "2026-09-16-ONE-TIME-USER-ENTRY-V5"
REQUEST_TIMEOUT_SECONDS = 20
MAX_DAILY_COUNT = 10


# ============================================================
# PAGE / LOGGING
# ============================================================

st.set_page_config(
    page_title="Tiffin Tracker",
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
    """Safe application error."""


# ============================================================
# HTTP CLIENT
# ============================================================

@st.cache_resource
def get_http_session() -> requests.Session:
    session = requests.Session()

    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        raise_on_status=False,
    )

    session.mount(
        "https://",
        HTTPAdapter(max_retries=retry),
    )

    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "TiffinTracker/3.0",
        }
    )

    return session


def parse_response(
    response: requests.Response,
) -> dict[str, Any]:
    if response.status_code in (401, 403):
        raise AppError(
            f"Google Apps Script access error: HTTP {response.status_code}."
        )

    if not response.ok:
        logger.error(
            "Apps Script HTTP %s: %s",
            response.status_code,
            response.text[:1000],
        )
        raise AppError(
            f"Google Apps Script returned HTTP {response.status_code}."
        )

    try:
        data = response.json()
    except ValueError as exc:
        logger.error(
            "Non-JSON response: %s",
            response.text[:1000],
        )
        raise AppError(
            "Google Apps Script did not return JSON."
        ) from exc

    if not isinstance(data, dict):
        raise AppError(
            "Unexpected response from Google Apps Script."
        )

    if not data.get("ok", False):
        raise AppError(
            str(
                data.get(
                    "message",
                    "Google Sheet operation failed.",
                )
            )
        )

    return data


def api_get() -> dict[str, Any]:
    try:
        response = get_http_session().get(
            GOOGLE_SCRIPT_URL,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        raise AppError(
            f"Could not connect to Google Apps Script: {exc}"
        ) from exc

    return parse_response(response)


def api_post(
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        response = get_http_session().post(
            GOOGLE_SCRIPT_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
            headers={"Content-Type": "application/json"},
        )
    except requests.RequestException as exc:
        raise AppError(
            f"Could not connect to Google Apps Script: {exc}"
        ) from exc

    return parse_response(response)


# ============================================================
# API ACTIONS
# ============================================================

def login(
    username: str,
    pin: str,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "login",
            "username": username.strip(),
            "pin": pin.strip(),
        }
    )


def get_user_stats(
    username: str,
    pin: str,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "stats",
            "username": username,
            "pin": pin,
        }
    )


def save_today(
    username: str,
    pin: str,
    count: int,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "update_today",
            "username": username,
            "pin": pin,
            "count": int(count),
        }
    )


def change_credentials(
    username: str,
    pin: str,
    new_username: str,
    new_pin: str,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "change_credentials",
            "username": username,
            "pin": pin,
            "new_username": new_username.strip(),
            "new_pin": new_pin.strip(),
        }
    )


def admin_dashboard(
    username: str,
    pin: str,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "admin_dashboard",
            "username": username,
            "pin": pin,
        }
    )


def admin_add_member(
    username: str,
    pin: str,
    new_username: str,
    new_pin: str,
    person_name: str,
    active: bool,
    notes: str,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "admin_add_member",
            "username": username,
            "pin": pin,
            "new_username": new_username.strip(),
            "new_pin": new_pin.strip(),
            "person_name": person_name.strip(),
            "active": bool(active),
            "notes": notes.strip(),
        }
    )


def admin_update_member(
    username: str,
    pin: str,
    member_id: str,
    new_username: str,
    new_pin: str,
    new_person_name: str,
    notes: str,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "admin_update_member",
            "username": username,
            "pin": pin,
            "target_member_id": member_id,
            "new_username": new_username.strip(),
            "new_pin": new_pin.strip(),
            "new_person_name": new_person_name.strip(),
            "notes": notes.strip(),
        }
    )


def admin_set_active(
    username: str,
    pin: str,
    member_id: str,
    active: bool,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "admin_set_active",
            "username": username,
            "pin": pin,
            "target_member_id": member_id,
            "active": bool(active),
        }
    )


def admin_user_detail(
    username: str,
    pin: str,
    member_id: str,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "admin_user_detail",
            "username": username,
            "pin": pin,
            "target_member_id": member_id,
        }
    )


def admin_update_today_count(
    username: str,
    pin: str,
    member_id: str,
    count: int,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "admin_update_today_count",
            "username": username,
            "pin": pin,
            "target_member_id": member_id,
            "count": int(count),
        }
    )


def admin_set_payment(
    username: str,
    pin: str,
    member_id: str,
    month: str,
    paid: bool,
) -> dict[str, Any]:
    return api_post(
        {
            "action": "admin_set_payment",
            "username": username,
            "pin": pin,
            "target_member_id": member_id,
            "month": month,
            "paid": bool(paid),
        }
    )


# ============================================================
# SESSION
# ============================================================

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


def set_login_session(
    result: dict[str, Any],
    username: str,
    pin: str,
) -> None:
    st.session_state["logged_in"] = True
    st.session_state["role"] = str(
        result.get("role", "")
    )
    st.session_state["member_id"] = str(
        result.get("member_id", "")
    )
    st.session_state["username"] = str(
        result.get("username", username)
    )
    st.session_state["pin"] = pin
    st.session_state["person_name"] = str(
        result.get("person_name", "")
    )


def logout() -> None:
    for key, value in DEFAULT_SESSION.items():
        st.session_state[key] = value
    st.rerun()


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1180px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 12px;
        padding: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOGIN
# ============================================================

if not st.session_state["logged_in"]:
    st.title("🍱 Tiffin Tracker")
    st.caption(
        "Users can update today's tiffin. "
        "Administrators can manage members, dues and payment status."
    )

    with st.expander("Connection test"):
        if st.button(
            "Test Google Sheet Connection",
            use_container_width=True,
        ):
            try:
                health = api_get()
                st.success("Connection is working.")
                st.json(health)
            except AppError as exc:
                st.error(str(exc))

    with st.form("login_form"):
        username_input = st.text_input(
            "User ID",
            placeholder="Example: sahil or admin",
        )
        pin_input = st.text_input(
            "Password / PIN",
            type="password",
        )
        login_clicked = st.form_submit_button(
            "Login",
            type="primary",
            use_container_width=True,
        )

    if login_clicked:
        if not username_input.strip() or not pin_input.strip():
            st.error(
                "Please enter both User ID and PIN."
            )
        else:
            try:
                result = login(
                    username_input,
                    pin_input,
                )
                set_login_session(
                    result,
                    username_input.strip().lower(),
                    pin_input.strip(),
                )
                st.rerun()
            except AppError as exc:
                st.error(str(exc))

    st.stop()


username = st.session_state["username"]
pin = st.session_state["pin"]
role = st.session_state["role"]
person_name = st.session_state["person_name"]


# ============================================================
# COMMON HEADER
# ============================================================

head_left, head_right = st.columns([5, 1])

with head_left:
    st.title("🍱 Tiffin Tracker")
    st.caption(
        f"Logged in as **{person_name}** "
        f"({role.title()})"
    )

with head_right:
    if st.button(
        "Logout",
        use_container_width=True,
    ):
        logout()


# ============================================================
# USER PANEL
# ============================================================

if role == "user":
    try:
        stats = get_user_stats(
            username,
            pin,
        )
    except AppError as exc:
        st.error(str(exc))
        st.stop()

    total_due = float(
        stats.get(
            "total_outstanding_due",
            0,
        )
        or 0
    )

    previous_due = float(
        stats.get(
            "previous_month_due",
            0,
        )
        or 0
    )

    if total_due > 0:
        st.warning(
            f"Outstanding previous-month dues: "
            f"₹{total_due:,.0f}"
        )

        if previous_due > 0:
            st.caption(
                f"Immediate previous month due: "
                f"₹{previous_due:,.0f}"
            )

    today_has_entry = bool(
        stats.get(
            "today_has_entry",
            False,
        )
    )

    saved_today = int(
        stats.get(
            "today_count",
            0,
        )
        or 0
    )

    # Requested behavior:
    # default is 1 only when the user has not submitted today yet.
    # If they deliberately saved 0, keep 0.
    default_today = (
        saved_today
        if today_has_entry
        else 1
    )

    tab_today, tab_stats, tab_account = st.tabs(
        [
            "Today's Tiffin",
            "My Stats & Dues",
            "My Account",
        ]
    )

    with tab_today:
        st.subheader(
            f"Today's Entry — "
            f"{stats.get('today_label', '')}"
        )

        if today_has_entry:
            st.success(
                f"Saved today: {saved_today} tiffin(s)"
            )
            st.warning(
                "This entry is locked. You cannot edit it again. "
                "If the count is wrong, contact the administrator."
            )

            st.number_input(
                "Today's tiffin count",
                min_value=0,
                max_value=MAX_DAILY_COUNT,
                value=int(saved_today),
                step=1,
                disabled=True,
                key="locked_today_count",
            )

        else:
            st.info(
                "No entry has been saved today. "
                "Default count is 1. After you save it, "
                "the entry will be locked."
            )

            with st.form("today_form"):
                count = st.number_input(
                    "Today's tiffin count",
                    min_value=0,
                    max_value=MAX_DAILY_COUNT,
                    value=1,
                    step=1,
                )

                submit_today = st.form_submit_button(
                    "Save & Lock Today's Count",
                    type="primary",
                    use_container_width=True,
                )

            if submit_today:
                try:
                    result = save_today(
                        username,
                        pin,
                        int(count),
                    )
                    st.success(
                        result.get(
                            "message",
                            "Saved and locked.",
                        )
                    )
                    st.rerun()
                except AppError as exc:
                    st.error(str(exc))

    with tab_stats:
        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "This Month",
            f"{int(stats.get('month_total', 0) or 0)} tiffins",
        )

        c2.metric(
            "Current Month Amount",
            f"₹{float(stats.get('monthly_amount', 0) or 0):,.0f}",
        )

        c3.metric(
            "Outstanding Due",
            f"₹{total_due:,.0f}",
        )

        c4.metric(
            "Unpaid Months",
            int(
                stats.get(
                    "unpaid_months",
                    0,
                )
                or 0
            ),
        )

        dues_history = stats.get(
            "dues_history",
            [],
        )

        if dues_history:
            st.subheader("Monthly Payment History")

            st.dataframe(
                [
                    {
                        "Month": row.get(
                            "month_label",
                            row.get(
                                "month",
                                "",
                            ),
                        ),
                        "Tiffins": row.get(
                            "tiffins",
                            0,
                        ),
                        "Rate": row.get(
                            "rate",
                            0,
                        ),
                        "Amount": row.get(
                            "amount",
                            0,
                        ),
                        "Status": (
                            "PAID"
                            if row.get("paid")
                            else "UNPAID"
                        ),
                        "Paid On": row.get(
                            "paid_on",
                            "",
                        ),
                    }
                    for row in dues_history
                ],
                hide_index=True,
                use_container_width=True,
            )

        history = stats.get(
            "history",
            [],
        )

        if history:
            st.subheader("Recent Daily Entries")

            st.dataframe(
                [
                    {
                        "Date": row.get(
                            "date",
                            "",
                        ),
                        "Tiffins": row.get(
                            "count",
                            0,
                        ),
                        "Amount": row.get(
                            "amount",
                            0,
                        ),
                    }
                    for row in history
                ],
                hide_index=True,
                use_container_width=True,
            )

    with tab_account:
        st.subheader("Change My Login ID / PIN")

        st.caption(
            "Changing your login ID or PIN does not "
            "change your old tiffin or dues history."
        )

        with st.form("self_credentials"):
            new_username = st.text_input(
                "User ID",
                value=username,
            )

            new_pin = st.text_input(
                "New Password / PIN",
                type="password",
                placeholder=(
                    "Leave blank to keep current PIN"
                ),
            )

            change_clicked = st.form_submit_button(
                "Update Login Details",
                type="primary",
                use_container_width=True,
            )

        if change_clicked:
            try:
                result = change_credentials(
                    username,
                    pin,
                    new_username,
                    new_pin,
                )

                st.session_state["username"] = str(
                    result.get(
                        "username",
                        new_username,
                    )
                )

                if new_pin.strip():
                    st.session_state["pin"] = (
                        new_pin.strip()
                    )

                st.success(
                    "Login details updated."
                )
                st.rerun()

            except AppError as exc:
                st.error(str(exc))

    st.stop()


# ============================================================
# ADMIN PANEL
# ============================================================

if role == "admin":
    try:
        dashboard = admin_dashboard(
            username,
            pin,
        )
    except AppError as exc:
        st.error(str(exc))
        st.stop()

    members = dashboard.get(
        "members",
        [],
    )

    st.subheader("Administrator Panel")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Total Members",
        int(
            dashboard.get(
                "total_members",
                0,
            )
            or 0
        ),
    )

    m2.metric(
        "Active",
        int(
            dashboard.get(
                "active_members",
                0,
            )
            or 0
        ),
    )

    m3.metric(
        "Current Month",
        f"₹{float(dashboard.get('current_month_amount', 0) or 0):,.0f}",
    )

    m4.metric(
        "Outstanding Dues",
        f"₹{float(dashboard.get('total_outstanding_due', 0) or 0):,.0f}",
    )

    (
        overview_tab,
        today_count_tab,
        member_tab,
        dues_tab,
        admin_account_tab,
    ) = st.tabs(
        [
            "Overview",
            "Today's Counts",
            "Members",
            "Dues & Payments",
            "My Admin Account",
        ]
    )

    # --------------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------------

    with overview_tab:
        if members:
            st.dataframe(
                [
                    {
                        "Member ID": row.get(
                            "member_id",
                            "",
                        ),
                        "Name": row.get(
                            "person_name",
                            "",
                        ),
                        "User ID": row.get(
                            "username",
                            "",
                        ),
                        "Status": (
                            "Active"
                            if row.get("active")
                            else "Inactive"
                        ),
                        "Current Tiffins": row.get(
                            "current_month_tiffins",
                            0,
                        ),
                        "Current Amount": row.get(
                            "current_month_amount",
                            0,
                        ),
                        "Previous Due": row.get(
                            "previous_month_due",
                            0,
                        ),
                        "Total Due": row.get(
                            "total_outstanding_due",
                            0,
                        ),
                    }
                    for row in members
                ],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No members yet.")

    # --------------------------------------------------------
    # TODAY'S COUNTS — ADMIN CAN CORRECT / OVERWRITE
    # --------------------------------------------------------

    with today_count_tab:
        st.subheader("Today's Tiffin Counts")

        st.caption(
            "Normal users can save today's count only once. "
            "Only the administrator can correct or overwrite it afterward."
        )

        if not members:
            st.info("No members available.")
        else:
            today_rows = [
                {
                    "Member ID": row.get("member_id", ""),
                    "Name": row.get("person_name", ""),
                    "User ID": row.get("username", ""),
                    "Today's Count": (
                        row.get("today_count", 0)
                        if row.get("today_has_entry")
                        else "Not submitted"
                    ),
                    "Entry Status": (
                        "Locked"
                        if row.get("today_has_entry")
                        else "Not submitted"
                    ),
                }
                for row in members
            ]

            st.dataframe(
                today_rows,
                hide_index=True,
                use_container_width=True,
            )

            today_lookup = {
                (
                    f"{m.get('person_name', '')} "
                    f"({m.get('username', '')})"
                ): m
                for m in members
            }

            today_member_label = st.selectbox(
                "Select member to set/correct today's count",
                list(today_lookup.keys()),
                key="admin_today_member_select",
            )

            today_member = today_lookup[
                today_member_label
            ]

            current_admin_count = int(
                today_member.get(
                    "today_count",
                    0,
                )
                or 0
            )

            has_admin_today_entry = bool(
                today_member.get(
                    "today_has_entry",
                    False,
                )
            )

            if has_admin_today_entry:
                st.info(
                    f"Currently saved: {current_admin_count} tiffin(s). "
                    "You can overwrite this value."
                )
            else:
                st.info(
                    "This member has not submitted today's count yet. "
                    "Admin may create it directly."
                )

            with st.form("admin_today_count_form"):
                corrected_count = st.number_input(
                    "Today's tiffin count",
                    min_value=0,
                    max_value=MAX_DAILY_COUNT,
                    value=(
                        current_admin_count
                        if has_admin_today_entry
                        else 1
                    ),
                    step=1,
                )

                admin_today_submit = st.form_submit_button(
                    "Set / Correct Today's Count",
                    type="primary",
                    use_container_width=True,
                )

            if admin_today_submit:
                try:
                    result = admin_update_today_count(
                        username,
                        pin,
                        str(
                            today_member.get(
                                "member_id",
                                "",
                            )
                        ),
                        int(corrected_count),
                    )
                    st.success(
                        result.get(
                            "message",
                            "Today's count updated.",
                        )
                    )
                    st.rerun()
                except AppError as exc:
                    st.error(str(exc))

    # --------------------------------------------------------
    # MEMBER MANAGEMENT
    # --------------------------------------------------------

    with member_tab:
        st.subheader("Add New Member")

        with st.form("add_member_form"):
            add_col1, add_col2 = st.columns(2)

            with add_col1:
                new_member_username = st.text_input(
                    "New User ID"
                )
                new_member_name = st.text_input(
                    "Person Name"
                )

            with add_col2:
                new_member_pin = st.text_input(
                    "Password / PIN",
                    type="password",
                )
                new_member_active = st.checkbox(
                    "Active",
                    value=True,
                )

            new_member_notes = st.text_input(
                "Notes"
            )

            add_clicked = st.form_submit_button(
                "Add Member",
                type="primary",
                use_container_width=True,
            )

        if add_clicked:
            try:
                result = admin_add_member(
                    username,
                    pin,
                    new_member_username,
                    new_member_pin,
                    new_member_name,
                    new_member_active,
                    new_member_notes,
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

        if members:
            st.divider()
            st.subheader("Edit Existing Member")

            member_lookup = {
                (
                    f"{m.get('person_name', '')} "
                    f"({m.get('username', '')})"
                ):
                    m
                for m in members
            }

            selected_label = st.selectbox(
                "Select member",
                list(
                    member_lookup.keys()
                ),
                key="edit_member_select",
            )

            selected = member_lookup[
                selected_label
            ]

            st.caption(
                f"Member ID: "
                f"{selected.get('member_id', '')}"
            )

            with st.form("edit_member_form"):
                edit_username = st.text_input(
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

                reset_pin = st.text_input(
                    "New Password / PIN",
                    type="password",
                    placeholder=(
                        "Leave blank to keep existing PIN"
                    ),
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

                update_member_clicked = (
                    st.form_submit_button(
                        "Update Member",
                        type="primary",
                        use_container_width=True,
                    )
                )

            if update_member_clicked:
                try:
                    result = admin_update_member(
                        username,
                        pin,
                        str(
                            selected.get(
                                "member_id",
                                "",
                            )
                        ),
                        edit_username,
                        reset_pin,
                        edit_name,
                        edit_notes,
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

            target_active = bool(
                selected.get(
                    "active",
                    False,
                )
            )

            if target_active:
                if st.button(
                    "Mark Member Inactive",
                    key="deactivate_member",
                    use_container_width=True,
                ):
                    try:
                        result = admin_set_active(
                            username,
                            pin,
                            str(
                                selected.get(
                                    "member_id",
                                    "",
                                )
                            ),
                            False,
                        )
                        st.success(
                            result.get(
                                "message",
                                "Member deactivated.",
                            )
                        )
                        st.rerun()
                    except AppError as exc:
                        st.error(str(exc))
            else:
                if st.button(
                    "Mark Member Active",
                    key="activate_member",
                    use_container_width=True,
                ):
                    try:
                        result = admin_set_active(
                            username,
                            pin,
                            str(
                                selected.get(
                                    "member_id",
                                    "",
                                )
                            ),
                            True,
                        )
                        st.success(
                            result.get(
                                "message",
                                "Member activated.",
                            )
                        )
                        st.rerun()
                    except AppError as exc:
                        st.error(str(exc))

    # --------------------------------------------------------
    # DUES
    # --------------------------------------------------------

    with dues_tab:
        if not members:
            st.info("No members available.")
        else:
            due_lookup = {
                (
                    f"{m.get('person_name', '')} "
                    f"({m.get('username', '')})"
                ):
                    m
                for m in members
            }

            due_label = st.selectbox(
                "Select member",
                list(
                    due_lookup.keys()
                ),
                key="due_member_select",
            )

            due_member = due_lookup[
                due_label
            ]

            try:
                detail = admin_user_detail(
                    username,
                    pin,
                    str(
                        due_member.get(
                            "member_id",
                            "",
                        )
                    ),
                )
            except AppError as exc:
                st.error(str(exc))
                detail = {}

            if detail:
                d1, d2, d3, d4 = st.columns(4)

                d1.metric(
                    "Current Month Tiffins",
                    int(
                        detail.get(
                            "month_total",
                            0,
                        )
                        or 0
                    ),
                )

                d2.metric(
                    "Current Month Amount",
                    f"₹{float(detail.get('monthly_amount', 0) or 0):,.0f}",
                )

                d3.metric(
                    "Previous Month Due",
                    f"₹{float(detail.get('previous_month_due', 0) or 0):,.0f}",
                )

                d4.metric(
                    "Total Outstanding",
                    f"₹{float(detail.get('total_outstanding_due', 0) or 0):,.0f}",
                )

                dues_history = detail.get(
                    "dues_history",
                    [],
                )

                if dues_history:
                    st.dataframe(
                        [
                            {
                                "Month": row.get(
                                    "month_label",
                                    row.get(
                                        "month",
                                        "",
                                    ),
                                ),
                                "Tiffins": row.get(
                                    "tiffins",
                                    0,
                                ),
                                "Rate": row.get(
                                    "rate",
                                    0,
                                ),
                                "Amount": row.get(
                                    "amount",
                                    0,
                                ),
                                "Status": (
                                    "PAID"
                                    if row.get("paid")
                                    else "UNPAID"
                                ),
                                "Paid On": row.get(
                                    "paid_on",
                                    "",
                                ),
                            }
                            for row in dues_history
                        ],
                        hide_index=True,
                        use_container_width=True,
                    )

                    month_options = {
                        (
                            f"{row.get('month_label', row.get('month', ''))} "
                            f"— ₹{float(row.get('amount', 0) or 0):,.0f} "
                            f"— {'PAID' if row.get('paid') else 'UNPAID'}"
                        ):
                            row
                        for row in dues_history
                    }

                    selected_due_label = st.selectbox(
                        "Select month to change payment status",
                        list(
                            month_options.keys()
                        ),
                    )

                    selected_due = month_options[
                        selected_due_label
                    ]

                    desired_paid = st.radio(
                        "Payment status",
                        ["PAID", "UNPAID"],
                        horizontal=True,
                        index=(
                            0
                            if selected_due.get("paid")
                            else 1
                        ),
                    )

                    if st.button(
                        "Update Payment Status",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            result = admin_set_payment(
                                username,
                                pin,
                                str(
                                    due_member.get(
                                        "member_id",
                                        "",
                                    )
                                ),
                                str(
                                    selected_due.get(
                                        "month",
                                        "",
                                    )
                                ),
                                desired_paid == "PAID",
                            )

                            st.success(
                                result.get(
                                    "message",
                                    "Payment status updated.",
                                )
                            )
                            st.rerun()

                        except AppError as exc:
                            st.error(str(exc))
                else:
                    st.info(
                        "No completed-month dues exist for this member yet."
                    )

    # --------------------------------------------------------
    # ADMIN OWN ACCOUNT
    # --------------------------------------------------------

    with admin_account_tab:
        st.subheader("Change Administrator Login")

        st.caption(
            "The administrator User ID and PIN are also stored "
            "in the User Details sheet."
        )

        with st.form("admin_credentials"):
            admin_new_username = st.text_input(
                "Admin User ID",
                value=username,
            )

            admin_new_pin = st.text_input(
                "New Admin Password / PIN",
                type="password",
                placeholder=(
                    "Leave blank to keep current PIN"
                ),
            )

            admin_change_clicked = (
                st.form_submit_button(
                    "Update Administrator Login",
                    type="primary",
                    use_container_width=True,
                )
            )

        if admin_change_clicked:
            try:
                result = change_credentials(
                    username,
                    pin,
                    admin_new_username,
                    admin_new_pin,
                )

                st.session_state["username"] = str(
                    result.get(
                        "username",
                        admin_new_username,
                    )
                )

                if admin_new_pin.strip():
                    st.session_state["pin"] = (
                        admin_new_pin.strip()
                    )

                st.success(
                    "Administrator login updated."
                )
                st.rerun()

            except AppError as exc:
                st.error(str(exc))

    st.stop()


if role not in {"user", "admin"}:
    st.warning(
        "Your login session is invalid or belongs to an older app version."
    )
    if st.button(
        "Reset Session & Login Again",
        type="primary",
        use_container_width=True,
    ):
        logout()
    st.stop()
