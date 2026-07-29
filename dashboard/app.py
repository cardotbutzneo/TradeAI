"""app.py — TradeAI live dashboard (Plotly Dash).

A read-only visualizer for the trading simulation. It repeatedly parses the
log the simulation already writes (``logs/simulation.log``) and renders, live:

  * KPI tiles (ticks, agents, trades, best performer),
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
# Config
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.environ.get("TRADEAI_LOG", os.path.join(HERE, "..", "logs", "simulation.log"))
REFRESH_MS = 800

# ---------------------------------------------------------------------------
# Theme — validated dark palette (dataviz skill, references/palette.md).
# Six-checks validator run on this exact set: all PASS in dark mode, first
# three categorical slots also clear the stricter all-pairs check used for
# the scatter-style trade markers.
# ---------------------------------------------------------------------------
PAGE = "#0d0d0d"            # page plane
SURFACE = "#1a1a19"         # card / chart surface
INK = "#ffffff"             # primary text
INK_SECONDARY = "#c3c2b7"
INK_MUTED = "#898781"
GRID = "#2c2c2a"
BASELINE = "#383835"
BORDER = "rgba(255,255,255,0.10)"
FONT = "Segoe UI, system-ui, -apple-system, sans-serif"

GOOD = "#0ca30c"
WARNING = "#fab219"
CRITICAL = "#d03b3b"

# Categorical identity, fixed order — never cycle or reassign per filter.
AGENT_COLORS = [
    "#3987e5", "#d95926", "#199e70", "#c98500",
    "#d55181", "#008300", "#9085e9", "#e66767",
]


def agent_color(idx: int) -> str:
    return AGENT_COLORS[idx % len(AGENT_COLORS)]


# ---------------------------------------------------------------------------
# Figure builders
# ---------------------------------------------------------------------------
def _base_layout(fig: go.Figure, title: str, height: int, legend_pos: str = "top") -> go.Figure:
    if legend_pos == "top":
        legend = dict(
            bgcolor="rgba(0,0,0,0)", font=dict(color=INK_SECONDARY, size=12),
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        )
    else:
        legend = dict(
            bgcolor="rgba(0,0,0,0)", font=dict(color=INK_SECONDARY, size=12),
            orientation="h", yanchor="top", y=-0.14, xanchor="left", x=0,
        )
    fig.update_layout(
        title=dict(text=title, font=dict(color=INK, size=15, family=FONT)),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(color=INK_SECONDARY, family=FONT, size=12),
        margin=dict(l=48, r=20, t=52, b=36),
        height=height,
        legend=legend,
        hovermode="x unified",
        hoverlabel=dict(bgcolor=PAGE, font=dict(color=INK, size=12), bordercolor=BORDER),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=BASELINE, linecolor=BASELINE, showline=True)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=BASELINE, linecolor=BASELINE, showline=True)
    return fig


def build_networth_fig(state: SimState) -> go.Figure:
    fig = go.Figure()
    for idx, (aid, ag) in enumerate(sorted(state.agents.items())):
        if not ag.networth_hist:
            continue
        n = len(ag.networth_hist)
        color = agent_color(idx)
        fig.add_trace(
            go.Scatter(
                x=state.times[:n],
                y=ag.networth_hist,
                mode="lines",
                name=aid,
                line=dict(color=color, width=2),
                hovertemplate=f"{aid}: %{{y:,.2f}} €<extra></extra>",
            )
        )
        fig.add_hline(
            y=ag.initial_cash,
            line=dict(color=color, width=1, dash="dot"),
            opacity=0.3,
        )
    if not state.agents:
        fig.add_annotation(
            text="No data yet — start a simulation",
            showarrow=False, font=dict(color=INK_MUTED, size=13),
        )
    return _base_layout(fig, "Net worth over time", 360)


def build_price_fig(state: SimState) -> go.Figure:
    tickers = state.tickers or []
    n = max(len(tickers), 1)
    cols = 2 if len(tickers) > 1 else 1
    rows = (n + cols - 1) // cols
    fig = make_subplots(
        rows=rows, cols=cols, shared_xaxes=False,
        horizontal_spacing=0.07, vertical_spacing=0.16,
        subplot_titles=tickers or ["No data yet"],
    )

    for i, ticker in enumerate(tickers):
        r, c = i // cols + 1, i % cols + 1
        series = state.prices.get(ticker, [])
        fig.add_trace(
            go.Scatter(
                x=state.times, y=series, mode="lines", name=ticker,
                line=dict(color=AGENT_COLORS[0], width=2), showlegend=False,
                connectgaps=True, hovertemplate="%{y:.2f} €<extra></extra>",
            ),
            row=r, col=c,
        )

        price_at = {t: p for t, p in zip(state.times, series) if p is not None}

        for idx, (aid, ag) in enumerate(sorted(state.agents.items())):
            color = agent_color(idx)
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
                        x=xs, y=ys, mode="markers", name=aid,
                        text=texts, hovertemplate="%{text}<br>%{y:.2f} €<extra></extra>",
                        marker=dict(
                            symbol=symbol, size=11, color=color,
                            line=dict(width=2, color=SURFACE),
                        ),
                        showlegend=(i == 0),
                        legendgroup=aid,
                    ),
                    row=r, col=c,
                )

    fig = _base_layout(fig, "Prices & executed trades", 280 * rows + 40, legend_pos="bottom")
    fig.update_annotations(font=dict(color=INK_SECONDARY, size=13, family=FONT))
    return fig


# ---------------------------------------------------------------------------
# HTML components
# ---------------------------------------------------------------------------
def stat_tile(label: str, value: str, delta: float | None = None) -> html.Div:
    children = [
        html.Div(label, className="stat-label"),
        html.Div(value, className="stat-value"),
    ]
    if delta is not None:
        color = GOOD if delta >= 0 else CRITICAL
        sign = "+" if delta >= 0 else ""
        children.append(
            html.Div(f"{sign}{delta:.1f} %", className="stat-delta", style={"color": color})
        )
    return html.Div(children, className="stat-tile")


def build_stat_row(state: SimState) -> list[html.Div]:
    n_agents = len(state.agents)
    n_trades = sum(ag.n_buy + ag.n_sell for ag in state.agents.values())
    n_rejects = sum(ag.n_reject for ag in state.agents.values())

    best_label, best_delta = "—", None
    if state.agents:
        best_aid, best_ag = max(
            state.agents.items(),
            key=lambda kv: current_networth(state, kv[1]),
        )
        nw = current_networth(state, best_ag)
        best_delta = (nw - best_ag.initial_cash) / best_ag.initial_cash * 100 if best_ag.initial_cash else 0.0
        best_label = best_aid

    return [
        stat_tile("Ticks processed", f"{state.n_ticks:,}"),
        stat_tile("Active agents", str(n_agents)),
        stat_tile("Trades executed", f"{n_trades:,}"),
        stat_tile("Rejected orders", f"{n_rejects:,}"),
        stat_tile("Best performer", best_label, best_delta),
    ]


def build_leaderboard(state: SimState) -> html.Table:
    if not state.agents:
        return html.Div("No agents yet — start a simulation to see the leaderboard.", className="lb-empty")

    header = ["#", "Agent", "Net worth", "Return", "Cash", "Holdings", "Buys", "Sells", "Rejects"]
    order = sorted(state.agents)  # stable colour assignment
    ranked = sorted(
        state.agents.items(), key=lambda kv: current_networth(state, kv[1]), reverse=True
    )

    rows = []
    for rank, (aid, ag) in enumerate(ranked, start=1):
        nw = current_networth(state, ag)
        holdings = nw - ag.cash
        ret = (nw - ag.initial_cash) / ag.initial_cash * 100 if ag.initial_cash else 0.0
        ret_color = GOOD if ret >= 0 else CRITICAL
        color = agent_color(order.index(aid))
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, str(rank))
        rows.append(
            html.Tr(
                [
                    html.Td(medal, style={"textAlign": "center"}),
                    html.Td(aid, style={"color": color, "fontWeight": 600}),
                    html.Td(f"{nw:,.2f} €", style={"fontWeight": 600}),
                    html.Td(f"{ret:+.1f} %", style={"color": ret_color, "fontWeight": 600}),
                    html.Td(f"{ag.cash:,.2f} €"),
                    html.Td(f"{holdings:,.2f} €"),
                    html.Td(str(ag.n_buy), style={"color": GOOD}),
                    html.Td(str(ag.n_sell), style={"color": CRITICAL}),
                    html.Td(str(ag.n_reject), style={"color": INK_MUTED}),
                ],
                className="lb-row",
            )
        )

    table = html.Table(
        [html.Thead(html.Tr([html.Th(h) for h in header])), html.Tbody(rows)],
        className="lb-table",
    )
    return html.Div(table, className="lb-scroll")


def status_badge(state: SimState) -> html.Span:
    if state.finished:
        label, cls = "● FINISHED", "badge-muted"
    elif state.n_ticks > 0:
        label, cls = "● LIVE", "badge-good"
    else:
        label, cls = "● WAITING FOR DATA", "badge-warning"
    return html.Span(label, className=f"badge {cls}")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Dash(__name__, title="TradeAI Dashboard")

app.layout = html.Div(
    className="app-root",
    children=[
        html.Header(
            className="app-header",
            children=[
                html.Div(
                    className="brand",
                    children=[
                        html.Img(src=app.get_asset_url("logo.svg"), className="brand-logo"),
                        html.Div(
                            className="brand-text",
                            children=[
                                html.Span("TradeAI", className="brand-name"),
                                html.Span("Live simulation dashboard", className="brand-tag"),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="header-status",
                    children=[
                        html.Div(id="status-badge"),
                        html.Span(id="tick-counter", className="tick-counter"),
                    ],
                ),
            ],
        ),
        html.Div(id="stat-row", className="stat-row"),
        html.Div(
            className="card section-card",
            children=[
                html.H2("Leaderboard", className="card-title"),
                html.Div(id="leaderboard"),
            ],
        ),
        html.Div(
            className="card section-card",
            children=[dcc.Graph(id="networth-graph", config={"displayModeBar": False})],
        ),
        html.Div(
            className="card section-card",
            children=[dcc.Graph(id="price-graph", config={"displayModeBar": False})],
        ),
        dcc.Interval(id="refresh", interval=REFRESH_MS, n_intervals=0),
    ],
)


@app.callback(
    Output("networth-graph", "figure"),
    Output("price-graph", "figure"),
    Output("leaderboard", "children"),
    Output("stat-row", "children"),
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
        build_stat_row(state),
        status_badge(state),
        counter,
    )


if __name__ == "__main__":
    print(f"[dashboard] reading log: {LOG_PATH}")
    print("[dashboard] open http://127.0.0.1:8050")
    app.run(host="127.0.0.1", port=8050, debug=False)
