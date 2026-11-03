
from textwrap import dedent

import streamlit as st
import pandas as pd
import plotly.express as px

from datetime import date


from agents.data_loader import load_data
from agents.orchestrator import FashionIQAgent

from tools.inventory_tools import (
    get_inventory,
    get_inventory_summary,
    get_low_stock,
    get_reorder_suggestions,
)

from tools.sales_tools import (
    calculate_revenue,
    get_category_sales,
    get_best_selling_products,
    compare_branch_sales,
)

from tools.business_insights import (
    calculate_slow_moving_capital,
    get_slow_moving_inventory,
    generate_business_recommendations,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FashionIQ | Retail Intelligence",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DESIGN SYSTEM
# ============================================================

st.markdown("""
<style>

/* Main background */

.stApp {
    background:
        radial-gradient(
            circle at 80% 0%,
            rgba(105, 76, 180, 0.13),
            transparent 35%
        ),
        #0B1020;
    color: #F4F5FA;
}

/* Main content */

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background: #10172A;
    border-right: 1px solid #252D45;
}

/* Typography */

h1, h2, h3 {
    color: #F4F5FA !important;
    letter-spacing: -0.5px;
}

p, label, span {
    color: #C5CBDA;
}

/* Metric cards */

div[data-testid="stMetric"] {
    background: linear-gradient(
        145deg,
        #19233C,
        #141B30
    );
    border: 1px solid #303B5A;
    border-radius: 16px;
    padding: 19px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

div[data-testid="stMetricLabel"] {
    color: #A8B2CC;
}

div[data-testid="stMetricValue"] {
    color: #FFFFFF;
    font-weight: 700;
}

/* Buttons */

.stButton > button {
    background: linear-gradient(
        100deg,
        #7257D9,
        #4F75DB
    );
    color: white;
    border: none;
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
    transition: 0.2s ease;
}

.stButton > button:hover {
    border: 1px solid #A995FF;
    color: white;
    transform: translateY(-2px);
}

/* Inputs */

.stTextInput input,
.stNumberInput input,
.stDateInput input {
    background: #151E33;
    color: white;
    border: 1px solid #35415E;
    border-radius: 9px;
}

div[data-baseweb="select"] > div {
    background: #151E33;
    border-color: #35415E;
}

/* Chat */

div[data-testid="stChatMessage"] {
    background: #151E33;
    border: 1px solid #293653;
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 12px;
}

/* Dataframes */

div[data-testid="stDataFrame"] {
    border: 1px solid #293653;
    border-radius: 12px;
}

/* Dividers */

hr {
    border-color: #293653;
}

/* Custom components */

.hero-card {
    background: linear-gradient(
        115deg,
        #25234B,
        #182B4A,
        #14213A
    );
    padding: 28px;
    border-radius: 20px;
    border: 1px solid #46446D;
    margin-bottom: 24px;
}

.hero-label {
    color: #B6A9FF;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.hero-title {
    color: #FFFFFF;
    font-size: 31px;
    font-weight: 750;
    margin-top: 8px;
}

.hero-description {
    color: #BEC9E3;
    font-size: 14px;
    margin-top: 8px;
}

.section-label {
    color: #A995FF;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.status-dot {
    color: #52D6A0;
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA AND AGENT
# ============================================================

@st.cache_resource
def get_store_data():
    return load_data()


@st.cache_resource
def get_ai_agent():
    return FashionIQAgent()


inventory, sales = get_store_data()

agent = get_ai_agent()

summary = get_inventory_summary(inventory)


# ============================================================
# SESSION STATE
# ============================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ============================================================
# CONSTANTS AND HELPERS
# ============================================================

# Assessment reporting period
DEFAULT_START = date(2026, 10, 1)
DEFAULT_END = date(2026, 10, 31)

PLOTLY_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#DCE3F5"},
    "margin": {"l": 15, "r": 15, "t": 40, "b": 15},
}

def money(value):
    return f"₹{value:,.2f}"


def section_heading(label, heading, description=None):
    st.markdown(
        f'<div class="section-label">{label}</div>',
        unsafe_allow_html=True,
    )
    st.subheader(heading)

    if description:
        st.caption(description)


def date_filters():
    col1, col2 = st.columns(2)

    with col1:
        start = st.date_input(
            "Start date",
            value=DEFAULT_START,
            key="filter_start",
        )

    with col2:
        end = st.date_input(
            "End date",
            value=DEFAULT_END,
            key="filter_end",
        )

    return start.isoformat(), end.isoformat()


def chart_style(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
    )
    fig.update_yaxes(
        gridcolor="#293653",
        zeroline=False,
    )
    return fig


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="padding:12px 0 22px 0;">
            <div style="font-size:30px;font-weight:800;color:white;">
                ✦ FashionIQ
            </div>
            <div style="color:#929DB9;font-size:12px;">
                RETAIL INTELLIGENCE PLATFORM
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<span class="status-dot">●</span> Claude API Connected',
        unsafe_allow_html=True,
    )

    st.caption(f"Active model: {agent.model}")

    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "AI Assistant",
            "Inventory",
            "Sales Analytics",
            "Business Insights",
        ],
        label_visibility="visible",
    )

    st.divider()

    st.markdown("**STORE INFORMATION**")

    st.metric(
        "Unique products",
        summary["unique_products"],
    )

    st.metric(
        "Known stock",
        f"{summary['total_known_stock']:,.0f} pieces",
    )

    st.divider()

    st.caption("FashionIQ v1.0")
    st.caption("Powered by Claude + Python")


# ============================================================
# PAGE 1: OVERVIEW
# ============================================================

if page == "Overview":

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-label">INTELLIGENT RETAIL OPERATIONS</div>
            <div class="hero-title">
                Welcome to FashionIQ.
            </div>
            <div class="hero-description">
                Your business, understood through data.
                Monitor inventory, discover sales patterns,
                and make smarter decisions with AI.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_heading(
        "BUSINESS OVERVIEW",
        "Performance at a glance",
        "Reporting period: October 2026",
    )

    revenue_data = calculate_revenue(
        sales,
        "2026-10-01",
        "2026-10-31",
    )

    revenue = revenue_data["total_revenue"]

    category_data = get_category_sales(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31",
    )

    reorder_data = get_reorder_suggestions(inventory)

    low_stock_data = get_low_stock(inventory)

    slow_capital = calculate_slow_moving_capital(
        sales,
        inventory,
        "2026-10-01",
        "2026-10-31",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "October Revenue",
            money(revenue),
            help="Revenue calculated by the sales analytics tool.",
        )

    with col2:
        st.metric(
            "Transactions",
            f"{revenue_data['transactions_included']:,}",
        )

    with col3:
        st.metric(
            "Inventory Records",
            f"{summary['total_inventory_records']:,}",
        )

    with col4:
        st.metric(
            "Low Stock Records",
            f"{len(low_stock_data):,}",
        )

    st.write("")

    # Charts
    left, right = st.columns([1.5, 1])

    with left:

        section_heading(
            "CATEGORY PERFORMANCE",
            "Revenue by category",
        )

        fig = px.bar(
            category_data.sort_values(
                "revenue",
                ascending=True,
            ),
            x="revenue",
            y="category",
            orientation="h",
            text_auto=".2s",
            color="revenue",
            color_continuous_scale=[
                "#5143A8",
                "#9175F5",
                "#49A6E9",
            ],
        )

        fig.update_layout(
            coloraxis_showscale=False,
            xaxis_title="Revenue (₹)",
            yaxis_title="",
        )

        st.plotly_chart(
            chart_style(fig),
            use_container_width=True,
        )

    
    with right:

        section_heading(
            "INVENTORY HEALTH",
            "Stock by branch",
        )

        stock_by_branch = (
            inventory.groupby("branch")["stock_qty"]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            stock_by_branch,
            x="branch",
            y="stock_qty",
            text="stock_qty",
            color="branch",
            color_discrete_map={
                "Branch 1": "#8269E8",
                "Branch 2": "#49A6E9",
            },
        )

        fig.update_traces(
            texttemplate="%{text:.0f} pieces",
            textposition="outside",
            cliponaxis=False,
        )

        fig.update_layout(
            height=390,
            showlegend=False,
            xaxis_title="",
            yaxis_title="Stock quantity (pieces)",
            yaxis=dict(
                range=[0, 310],
                gridcolor="#293653",
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key="stock_by_branch_chart",
        )

        st.caption(
            "Branch 1: 259 pieces | Branch 2: 218 pieces"
        )

    # Business alerts
    st.divider()

    section_heading(
        "BUSINESS ALERTS",
        "Items requiring attention",
    )

    a, b = st.columns(2)

    with a:

        st.markdown("### ⚠️ Replenishment")

        st.metric(
            "Products requiring reorder",
            len(reorder_data),
        )

        if not reorder_data.empty:
            st.dataframe(
                reorder_data[
                    [
                        "product_id",
                        "product_name",
                        "branch",
                        "stock_qty",
                        "suggested_reorder_qty",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

    with b:

        st.markdown("### 💰 Capital tied up")

        st.metric(
            "Known slow-moving stock value",
            money(slow_capital["known_stock_value"]),
        )

        st.caption(
            f"{slow_capital['slow_moving_product_records']} "
            "slow-moving product-branch records."
        )

        st.caption(
            f"{slow_capital['records_with_unknown_value']} "
            "records have unknown stock value."
        )


# ============================================================
# PAGE 2: AI ASSISTANT
# ============================================================


elif page == "AI Assistant":

    # --------------------------------------------------------
    # TOOL DESCRIPTIONS
    # --------------------------------------------------------

    TOOL_DESCRIPTIONS = {
        "get_inventory": "Retrieved product and branch inventory.",
        "get_inventory_summary": "Calculated overall inventory statistics.",
        "get_low_stock": "Identified products at or below reorder levels.",
        "get_reorder_recommendations": "Calculated branch-wise reorder quantities.",
        "search_products": "Searched the product catalogue.",
        "calculate_revenue": "Calculated revenue for the selected period.",
        "compare_branch_sales": "Compared sales performance across branches.",
        "get_best_selling_products": "Identified the best-selling products.",
        "get_category_sales": "Calculated sales performance by category.",
        "get_sales_by_period": "Retrieved sales transactions for the period.",
        "get_slow_moving_products": "Identified products with low sales.",
        "calculate_slow_moving_capital": "Calculated capital tied up in slow-moving stock.",
        "get_slow_moving_inventory": "Retrieved slow-moving inventory records.",
        "get_branch_performance_insights": "Analysed branch performance.",
        "generate_business_recommendations": "Generated business recommendations.",
        "get_category_revenue_metrics":"Calculated category revenue and percentage contribution.",

        "compare_category_revenue":"Calculated the exact revenue difference between two categories.",
    }

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:18px;
        ">
            <div>
                <div class="section-label">INTELLIGENCE ENGINE</div>
                <div style="
                    font-size:29px;
                    font-weight:750;
                    color:#FFFFFF;
                    margin-top:5px;
                ">
                    AI Business Assistant
                </div>
                <div style="color:#929DB9;font-size:13px;margin-top:5px;">
                    Your intelligent partner for fashion retail decisions.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # EMPTY STATE
    # --------------------------------------------------------

    if not st.session_state.chat_history:

        
        
        st.markdown(
            """
<div class="hero-card">
<div class="hero-label">✦ FASHIONIQ INTELLIGENCE</div>
<div class="hero-title">Your business. Your data. Smarter decisions.</div>
<div class="hero-description">
Ask questions in natural language. FashionIQ analyses your actual
business data using Claude and Python analytics tools.
</div>
</div>
""",
            unsafe_allow_html=True,
        )



        st.markdown("### Explore what FashionIQ can do")

        prompts = [
            (
                "📦",
                "Inventory",
                "Which products should I reorder before Diwali? Give quantities per branch.",
            ),
            (
                "💰",
                "Sales performance",
                "What was our total revenue in October 2026, and which category contributed the most?",
            ),
            (
                "📊",
                "Branch comparison",
                "Compare saree sales between Branch 1 and Branch 2 last month.",
            ),
            (
                "⚠️",
                "Slow-moving stock",
                "Which items are not selling and how much stock capital is tied up?",
            ),
            (
                "🔍",
                "Product lookup",
                "How many pieces of TZ-999 do we have?",
            ),
        ]

        prompt_cols = st.columns(2)

        for index, (emoji, label, prompt) in enumerate(prompts):

            with prompt_cols[index % 2]:

                if st.button(
                    f"{emoji}  {label}  →",
                    key=f"premium_prompt_{index}",
                    use_container_width=True,
                ):
                    st.session_state.pending_question = prompt
                    st.rerun()

    else:

        # ----------------------------------------------------
        # ACTIVE CONVERSATION HEADER
        # ----------------------------------------------------

        left, right = st.columns([4, 1])

        with left:
            st.caption(
                f"CONVERSATION · {len(st.session_state.chat_history)} messages"
            )

        with right:
            if st.button(
                "＋ New chat",
                use_container_width=True,
            ):
                st.session_state.chat_history = []
                st.session_state.pending_question = None
                st.rerun()

    # --------------------------------------------------------
    # RENDER CONVERSATION HISTORY
    # --------------------------------------------------------

    for message_index, message in enumerate(
        st.session_state.chat_history
    ):

       with st.chat_message(
    message["role"],
    avatar="👤" if message["role"] == "user" else "🤖",
):

            st.markdown(message["content"])

            calls = message.get("tool_calls", [])

            if message["role"] == "assistant" and calls:

                with st.expander(
                    f"✦ Agent Activity · {len(calls)} tools executed",
                    expanded=False,
                ):

                    st.caption(
                        "FashionIQ used the following Python tools "
                        "to produce this response."
                    )

                    for call_index, call in enumerate(calls, 1):

                        tool_name = call.get(
                            "tool_name",
                            "Unknown tool",
                        )

                        description = TOOL_DESCRIPTIONS.get(
                            tool_name,
                            "Executed a business analytics operation.",
                        )

                        with st.status(
                            f"{tool_name}",
                            state="complete",
                            expanded=False,
                        ):

                            st.markdown(description)

                            st.success("Execution completed")

                            st.divider()

                            st.markdown("**Developer details**")

                            with st.expander(
                                "View actual tool inputs",
                                expanded=False,
                            ):
                                st.json(
                                    call.get("tool_input", {})
                                )

                            with st.expander(
                                "View actual tool output",
                                expanded=False,
                            ):
                                st.json(
                                    call.get("tool_result", {})
                                )

    # --------------------------------------------------------
    # CHAT INPUT
    # --------------------------------------------------------

    question = st.chat_input(
        "Ask FashionIQ about your store, inventory or sales..."
    )

    if st.session_state.pending_question:

        question = st.session_state.pending_question
        st.session_state.pending_question = None

    # --------------------------------------------------------
    # PROCESS QUESTION
    # --------------------------------------------------------

    if question:

        previous_history = [
            {
                "role": item["role"],
                "content": item["content"],
            }
            for item in st.session_state.chat_history
        ]

        st.session_state.chat_history.append({
            "role": "user",
            "content": question,
        })

        with st.chat_message(
            "user",
            avatar="👤",
        ):
            st.markdown(question)

        with st.chat_message(
    "assistant",
    avatar="🤖",
):

            try:

                with st.spinner(
                    "FashionIQ is analysing your business data..."
                ):

                    result = agent.run(
                        question,
                        conversation_history=previous_history,
                    )

                answer = result["answer"]
                calls = result.get("tool_calls", [])

                st.markdown(answer)

                # Visual activity summary
                if calls:

                    with st.expander(
                        f"✦ Agent Activity · {len(calls)} tools executed",
                        expanded=True,
                    ):

                        for call in calls:

                            tool_name = call.get(
                                "tool_name",
                                "Unknown tool",
                            )

                            description = TOOL_DESCRIPTIONS.get(
                                tool_name,
                                "Executed a business analytics operation.",
                            )

                            with st.status(
                                tool_name,
                                state="complete",
                                expanded=False,
                            ):

                                st.markdown(description)

                                st.success("Execution completed")

                                with st.expander(
                                    "Developer details · Input",
                                    expanded=False,
                                ):
                                    st.json(
                                        call.get("tool_input", {})
                                    )

                                with st.expander(
                                    "Developer details · Output",
                                    expanded=False,
                                ):
                                    st.json(
                                        call.get("tool_result", {})
                                    )

                else:

                    st.caption(
                        "No Python tools were required for this response."
                    )

                # Save complete assistant message
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "tool_calls": calls,
                })

            except Exception as error:

                error_message = (
                    f"Sorry, FashionIQ encountered an error: {error}"
                )

                st.error(error_message)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_message,
                    "tool_calls": [],
                })

    # --------------------------------------------------------
    # CHAT CONTROLS
    # --------------------------------------------------------

    if st.session_state.chat_history:

        st.divider()

        left, right = st.columns([3, 1])

        with left:
            st.caption(
                "Powered by Claude Haiku 5.5 · Python Tool Execution"
            )

        with right:

            if st.button(
                "Clear conversation",
                use_container_width=True,
            ):
                st.session_state.chat_history = []
                st.session_state.pending_question = None
                st.rerun()


# ============================================================
# PAGE 3: INVENTORY
# ============================================================

elif page == "Inventory":

    section_heading(
        "STOCK MANAGEMENT",
        "Inventory Intelligence",
        "Monitor product availability and replenishment across both branches.",
    )

    branch = st.selectbox(
        "Select branch",
        ["All Branches", "Branch 1", "Branch 2"],
    )

    selected_branch = (
        None if branch == "All Branches" else branch
    )

    stock = get_inventory(
        inventory,
        branch=selected_branch,
    )

    low_stock = get_low_stock(
        inventory,
        branch=selected_branch,
    )

    reorder = get_reorder_suggestions(
        inventory,
        branch=selected_branch,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Inventory Records",
            len(stock),
        )

    with col2:
        st.metric(
            "Low Stock",
            len(low_stock),
        )

    with col3:
        st.metric(
            "Reorder Suggestions",
            len(reorder),
        )

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "All Products",
        "Low Stock Alerts",
        "Reorder Recommendations",
    ])

    with tab1:

        search = st.text_input(
            "Search by product name or product ID"
        )

        display_stock = stock.copy()

        if search:
            mask = (
                display_stock["product_name"]
                .astype(str)
                .str.contains(search, case=False, na=False)
                |
                display_stock["product_id"]
                .astype(str)
                .str.contains(search, case=False, na=False)
            )

            display_stock = display_stock[mask]

        st.dataframe(
            display_stock,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"Showing {len(display_stock)} inventory records."
        )

    with tab2:

        st.warning(
            "Products at or below their reorder level."
        )

        st.dataframe(
            low_stock,
            use_container_width=True,
            hide_index=True,
        )

    with tab3:

        st.info(
            "Suggested quantities are based on the existing "
            "inventory recommendation logic."
        )

        st.dataframe(
            reorder,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# PAGE 4: SALES ANALYTICS
# ============================================================

elif page == "Sales Analytics":

    section_heading(
        "REVENUE INTELLIGENCE",
        "Sales Analytics",
        "Understand revenue, product performance and branch comparisons.",
    )

    start, end = date_filters()

    if start > end:
        st.error("Start date must be before or equal to end date.")

    else:

        revenue_data = calculate_revenue(
            sales,
            start,
            end,
        )

        category_data = get_category_sales(
            sales,
            inventory,
            start,
            end,
        )

        best_sellers = get_best_selling_products(
            sales,
            inventory,
            start,
            end,
            top_n=10,
        )

        branch_data = compare_branch_sales(
            sales,
            inventory,
            start,
            end,
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Total Revenue",
                money(revenue_data["total_revenue"]),
            )

        with c2:
            st.metric(
                "Transactions",
                f"{revenue_data['transactions_included']:,}",
            )

        with c3:
            st.metric(
                "Excluded Transactions",
                f"{revenue_data['transactions_excluded']:,}",
            )

        st.divider()

        left, right = st.columns(2)

        with left:

            st.markdown("### Category Revenue")

            fig = px.bar(
                category_data,
                x="category",
                y="revenue",
                color="category",
                color_discrete_sequence=px.colors.qualitative.Prism,
                text_auto=".2s",
            )

            fig.update_layout(
                showlegend=False,
                xaxis_title="Category",
                yaxis_title="Revenue (₹)",
            )

            st.plotly_chart(
                chart_style(fig),
                use_container_width=True,
            )

        with right:

            st.markdown("### Branch Performance")

            fig = px.bar(
                branch_data,
                x="branch",
                y="revenue",
                color="branch",
                text_auto=".2s",
                color_discrete_sequence=[
                    "#8269E8",
                    "#49A6E9",
                ],
            )

            fig.update_layout(
                showlegend=False,
                yaxis_title="Revenue (₹)",
            )

            st.plotly_chart(
                chart_style(fig),
                use_container_width=True,
            )

        st.divider()

        st.markdown("### Top Selling Products")

        st.dataframe(
            best_sellers,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Branch Comparison")

        st.dataframe(
            branch_data,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# PAGE 5: BUSINESS INSIGHTS
# ============================================================

elif page == "Business Insights":

    section_heading(
        "DECISION INTELLIGENCE",
        "Business Insights",
        "Discover slow-moving inventory and actionable business opportunities.",
    )

    start, end = date_filters()

    if start > end:
        st.error("Start date must be before or equal to end date.")

    else:

        capital = calculate_slow_moving_capital(
            sales,
            inventory,
            start,
            end,
        )

        slow_stock = get_slow_moving_inventory(
            sales,
            inventory,
            start,
            end,
        )

        recommendations = generate_business_recommendations(
            inventory,
            sales,
            start,
            end,
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Slow-moving Records",
                capital["slow_moving_product_records"],
            )

        with col2:
            st.metric(
                "Known Stock Value",
                money(capital["known_stock_value"]),
            )

        with col3:
            st.metric(
                "Unknown Value Records",
                capital["records_with_unknown_value"],
            )

        st.divider()

        st.markdown("### Slow-moving Inventory")

        st.dataframe(
            slow_stock,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        st.markdown("### AI Business Recommendations")

        for item in recommendations:

            with st.container(border=True):

                priority = item.get(
                    "priority",
                    "normal",
                ).upper()

                st.markdown(
                    f"**{item.get('title', 'Recommendation')}**"
                )

                st.caption(
                    f"Type: {item.get('type', 'General')} "
                    f"| Priority: {priority}"
                )

                st.write(
                    item.get("details", "")
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#77839F;
        padding:15px;
        font-size:12px;
    ">
        FASHIONIQ · AI-POWERED RETAIL INTELLIGENCE
        <br>
        Built with Python, Claude, Streamlit and Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
