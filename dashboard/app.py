"""app.py — TradeAI live dashboard (Plotly Dash).

A read-only visualizer for the trading simulation. It repeatedly parses the
log the simulation already writes (``src_cpp/bourse.log``) and renders, live:

  * a leaderboard of the agents ranked by net worth,
  * net-worth (equity) curves over time,
  * price charts per ticker with each agent's executed BUY/SELL markers.

It imports nothing from the simulation — it only reads the log file. Start this
BEFORE or DURING a run; charts refresh automatically every ~0.8s.

Run:
    python3 app.py                 # then open http://127.0.0.1:8050
    TRADEAI_LOG=/path/to/log python3 app.py
"""

from __future__ import annotations

import os

import plotly.graph_objects as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots

from log_parser import SimState, current_networth, parse_log

# ---------------------------------------------------------------------------
# Config / theme
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.environ.get("TRADEAI_LOG", os.path.join(HERE, "..", "src_cpp", "bourse.log"))
REFRESH_MS = 800

BG = "#0e1117"
PANEL = "#161b22"
GRID = "#2a2f3a"
TEXT = "#e6edf3"
MUTED = "#8b949e"
GREEN = "#3fb950"
RED = "#f85149"

# Stable colour per agent (extra agents fall back to the palette by index).
AGENT_COLORS = ["#00d4ff", "#ff6ec7", "#ffd93d", "#a371f7", "#7ee787"]


def agent_color(agent_id: str, idx: int) -> str:
    return AGENT_COLORS[idx % len(AGENT_COLORS)]


def _base_layout(fig: go.Figure, title: str, height: int) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT, size=16)),
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT),
        margin=dict(l=50, r=20, t=50, b=40),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------
def build_networth_fig(state: SimState) -> go.Figure:
    fig = go.Figure()
    for idx, (aid, ag) in enumerate(sorted(state.agents.items())):
        if not ag.networth_hist:
            continue
        n = len(ag.networth_hist)
        fig.add_trace(
            go.Scatter(
                x=state.times[:n],
                y=ag.networth_hist,
                mode="lines",
                name=aid,
                line=dict(color=agent_color(aid, idx), width=2.5),
            )
        )
        fig.add_hline(
            y=ag.initial_cash,
            line=dict(color=agent_color(aid, idx), width=1, dash="dot"),
            opacity=0.35,
        )
    return _base_layout(fig, "💰 Net worth over time (cash + holdings)", 340)


def build_price_fig(state: SimState) -> go.Figure:
    tickers = state.tickers or []
    rows = max(len(tickers), 1)
    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        subplot_titles=[f"{t}  (€)" for t in tickers] or ["No data yet"],
    )

    for r, ticker in enumerate(tickers, start=1):
        series = state.prices.get(ticker, [])
        fig.add_trace(
            go.Scatter(
                x=state.times, y=series, mode="lines", name=ticker,
                line=dict(color="#58a6ff", width=1.8), showlegend=False,
                connectgaps=True,
            ),
            row=r, col=1,
        )

        # price lookup at a given timestamp for placing trade markers
        price_at = {t: p for t, p in zip(state.times, series) if p is not None}

        for idx, (aid, ag) in enumerate(sorted(state.agents.items())):
            for action, symbol in (("BUY", "triangle-up"), ("SELL", "triangle-down")):
                xs, ys, texts = [], [], []
                for tr in ag.trades:
                    if tr.ticker != ticker or tr.action != action or tr.status != "OK":
                        continue
                    y = price_at.get(tr.time)
                    if y is None:
                        continue
                    xs.append(tr.time)
                    ys.append(y)
                    texts.append(f"{aid} {action} {tr.qty}")
                if not xs:
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=xs, y=ys, mode="markers", name=f"{aid} {action}",
                        text=texts, hovertemplate="%{text}<br>%{y:.2f}€<extra></extra>",
                        marker=dict(
                            symbol=symbol, size=11,
                            color=agent_color(aid, idx),
                            line=dict(width=1, color="#0e1117"),
                        ),
                        showlegend=(r == 1),
                        legendgroup=aid,
                    ),
                    row=r, col=1,
                )

    fig = _base_layout(fig, "📈 Prices & executed trades", 240 * rows + 60)
    fig.update_xaxes(gridcolor=GRID)
    fig.update_yaxes(gridcolor=GRID)
    return fig


def build_leaderboard(state: SimState) -> html.Table:
    header = [
        "#", "Agent", "Net worth", "Return", "Cash", "Holdings", "Buys", "Sells", "Rejects",
    ]
    td_base = {"padding": "10px 12px", "borderBottom": f"1px solid {GRID}"}

    def cell(value, extra=None):
        return html.Td(value, style={**td_base, **(extra or {})})

    rows = []
    order = sorted(state.agents)  # for stable colour assignment
    ranked = sorted(
        state.agents.items(), key=lambda kv: current_networth(state, kv[1]), reverse=True
    )
    for rank, (aid, ag) in enumerate(ranked, start=1):
        nw = current_networth(state, ag)
        holdings = nw - ag.cash
        ret = (nw - ag.initial_cash) / ag.initial_cash * 100 if ag.initial_cash else 0.0
        ret_color = GREEN if ret >= 0 else RED
        color = agent_color(aid, order.index(aid))
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, str(rank))
        rows.append(
            html.Tr(
                [
                    cell(medal, {"textAlign": "center"}),
                    cell(aid, {"color": color, "fontWeight": "bold"}),
                    cell(f"{nw:,.2f} €", {"fontWeight": "bold"}),
                    cell(f"{ret:+.1f} %", {"color": ret_color, "fontWeight": "bold"}),
                    cell(f"{ag.cash:,.2f} €"),
                    cell(f"{holdings:,.2f} €"),
                    cell(str(ag.n_buy), {"color": GREEN}),
                    cell(str(ag.n_sell), {"color": RED}),
                    cell(str(ag.n_reject), {"color": MUTED}),
                ]
            )
        )

    th_style = {
        "padding": "8px 12px", "textAlign": "left", "color": MUTED,
        "borderBottom": f"1px solid {GRID}", "fontSize": "12px",
        "textTransform": "uppercase", "letterSpacing": "0.5px",
    }

    return html.Table(
        [html.Thead(html.Tr([html.Th(h, style=th_style) for h in header])), html.Tbody(rows)],
        style={
            "width": "100%", "borderCollapse": "collapse",
            "backgroundColor": PANEL, "color": TEXT, "fontSize": "15px",
        },
    )


def status_badge(state: SimState) -> html.Span:
    if state.finished:
        label, color = "● FINISHED", MUTED
    elif state.n_ticks > 0:
        label, color = "● LIVE", GREEN
    else:
        label, color = "● WAITING FOR DATA", "#d29922"
    return html.Span(
        label,
        style={
            "color": color, "fontWeight": "bold", "fontSize": "14px",
            "padding": "4px 12px", "border": f"1px solid {color}",
            "borderRadius": "20px",
        },
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Dash(__name__, title="TradeAI Dashboard")
server = app.server  # for optional WSGI hosting

app.layout = html.Div(
    style={
        "backgroundColor": BG, "minHeight": "100vh", "padding": "24px 32px",
        "fontFamily": "Segoe UI, Roboto, system-ui, sans-serif", "color": TEXT,
    },
    children=[
        html.Div(
            style={"display": "flex", "alignItems": "center", "gap": "16px",
                   "marginBottom": "8px"},
            children=[
                html.H1("📊 TradeAI — Live Dashboard",
                        style={"margin": 0, "fontSize": "26px"}),
                html.Div(id="status-badge"),
                html.Span(id="tick-counter", style={"color": MUTED, "fontSize": "14px"}),
            ],
        ),
        html.P(
            f"Reading: {os.path.relpath(LOG_PATH, HERE)}  ·  auto-refresh "
            f"{REFRESH_MS/1000:.1f}s  ·  read-only observer of the simulation",
            style={"color": MUTED, "marginTop": 0, "fontSize": "13px"},
        ),
        html.Div(
            id="leaderboard",
            style={"backgroundColor": PANEL, "borderRadius": "10px",
                   "padding": "12px 16px", "marginBottom": "20px",
                   "border": f"1px solid {GRID}"},
        ),
        dcc.Graph(id="networth-graph", config={"displayModeBar": False}),
        html.Div(style={"height": "20px"}),
        dcc.Graph(id="price-graph", config={"displayModeBar": False}),
        dcc.Interval(id="refresh", interval=REFRESH_MS, n_intervals=0),
    ],
)


@app.callback(
    Output("networth-graph", "figure"),
    Output("price-graph", "figure"),
    Output("leaderboard", "children"),
    Output("status-badge", "children"),
    Output("tick-counter", "children"),
    Input("refresh", "n_intervals"),
)
def refresh(_n):
    state = parse_log(LOG_PATH)
    counter = f"{state.n_ticks} ticks · {len(state.agents)} agents"
    return (
        build_networth_fig(state),
        build_price_fig(state),
        build_leaderboard(state),
        status_badge(state),
        counter,
    )


if __name__ == "__main__":
    print(f"[dashboard] reading log: {LOG_PATH}")
    print("[dashboard] open http://127.0.0.1:8050")
    app.run(host="127.0.0.1", port=8050, debug=False)
