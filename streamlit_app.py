import json
import math
import os
import time
import urllib.error
import urllib.request

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="ALPHA IDX • IHSG & ISSI Quantitative Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Dark Fintech Styling
st.markdown(
    """
    <style>
    .stApp { background-color: #070b14; color: #e2e8f0; }
    section[data-testid="stSidebar"] { background-color: #0b1120; border-right: 1px solid #1e293b; }
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(148, 163, 184, 0.15);
        padding: 12px 16px;
        border-radius: 12px;
    }
    .plan-box {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }
    .plan-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .plan-val { font-size: 17px; font-weight: 800; font-family: monospace; margin-top: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ========================
# DATA & RUMUS KUANTITATIF
# ========================
DEFAULT_ISSI = {
    "AADI", "AALI", "ABMM", "ACES", "ADHI", "ADMR", "ADRO", "AGII", "AKRA", "ALDO",
    "AMFG", "AMMN", "AMRT", "ANJT", "ANTM", "APLN", "ARCI", "ARNA", "ARTO", "ASII",
    "ASRI", "ASSA", "AUTO", "AVIA", "BALI", "BANK", "BELI", "BEST", "BIRD", "BISI",
    "BKSL", "BMHS", "BMTR", "BREN", "BRIS", "BRMS", "BRPT", "BSDE", "BSSR", "BTPS",
    "BUDI", "BUKA", "BULL", "BUMI", "BWPT", "BYAN", "CAMP", "CARE", "CARS", "CEKA",
    "CENT", "CINT", "CLEO", "CMNP", "CMRY", "CPIN", "CSAP", "CTBN", "CTRA", "CUAN",
    "DCII", "DEWA", "DGNS", "DIVA", "DKFT", "DMAS", "DMMX", "DOID", "DOOH", "DRMA",
    "DSNG", "DVLA", "EAST", "ECII", "EDGE", "EKAD", "ELSA", "EMTK", "ENRG", "EPMT",
    "ERAA", "ESSA", "EXCL", "FAST", "FILM", "FIRE", "FPNI", "GEMS", "GHSI", "GJTL",
    "GLVA", "GOOD", "GOTO", "GZCO", "HALO", "HEAL", "HERO", "HOKI", "HRUM", "ICBP",
    "IFII", "IGAR", "IMAS", "INAI", "INCO", "INDF", "INDY", "INET", "INKP", "INTP",
    "IPCC", "IPCM", "IRRA", "ISAT", "ISSP", "ITMG", "JECC", "JPFA", "JRPT", "JSMR",
    "KAEF", "KBLI", "KBLM", "KEEN", "KEJU", "KIJA", "KKGI", "KLBF", "KMTR", "KPIG",
    "KRAS", "LION", "LPCK", "LPIN", "LPKR", "LPPF", "LSIP", "MAIN", "MAPA", "MAPB",
    "MAPI", "MARK", "MBAP", "MBMA", "MBSS", "MCAS", "MDKA", "MEDC", "MERK", "MIDI",
    "MIKA", "MMLP", "MNCN", "MPMX", "MPPA", "MTEL", "MTDL", "MTLA", "MYOH", "MYOR",
    "NCKL", "NFCX", "NRCA", "NSSS", "PANI", "PBID", "PEHA", "PGAS", "PGEO", "PJAA",
    "PLIN", "PNBS", "POWR", "PPRE", "PRDA", "PSAB", "PTBA", "PTPP", "PTRO", "PWON",
    "PYFA", "PZZA", "RAAM", "RAJA", "RALS", "RDTX", "RMKE", "ROTI", "SAME", "SCCO",
    "SCMA", "SGER", "SGRO", "SHIP", "SIDO", "SILO", "SIMP", "SKBM", "SLIS", "SMDR",
    "SMGR", "SMRA", "SMSM", "SOHO", "SPMA", "SRAJ", "SRTG", "SSIA", "SSMS", "STAA",
    "STTP", "TAPG", "TBIG", "TBLA", "TCPI", "TGKA", "TINS", "TKIM", "TLKM", "TMAS",
    "TOBA", "TOTL", "TOTO", "TOWR", "TPIA", "TRGU", "TSPC", "ULTJ", "UNTR", "UNVR",
    "VKTR", "VOKS", "WEGE", "WEHA", "WIFI", "WIKA", "WOOD", "WTON", "ZINC", "ZONE",
}

NON_SYARIAH_TICKERS = {
    "BBCA", "BBRI", "BMRI", "BBNI", "BBTN", "BDMN", "BNGA", "BNLI", "MEGA", "NISP",
    "PNBN", "BBKP", "BJBR", "BJTM", "BTPN", "BNII", "MAYA", "AGRO", "BBYB", "AMAR",
    "GGRM", "HMSP", "WIIM", "RMBA", "ITIC", "MLBI", "DLTA", "ADMF", "BFIN", "CFIN",
    "PNLF", "PNIN", "ASRM", "LPGI", "TUGU", "MREI", "TRIM", "PANS",
}

NON_SYARIAH_KEYWORDS = (
    "tobacco", "brewer", "distiller", "casino", "gambling", "insurance", "consumer finance"
)

ISSI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "issi_list.txt")

FULL_COLS = [
    "name", "description", "sector", "industry", "close", "open", "high", "low",
    "change", "volume", "average_volume_10d_calc", "relative_volume_10d_calc",
    "market_cap_basic", "RSI", "RSI[1]", "Stoch.K", "Stoch.D", "MACD.macd",
    "MACD.signal", "EMA10", "EMA20", "EMA50", "EMA200", "SMA20", "SMA50", "SMA200",
    "ADX", "ADX+DI", "ADX-DI", "BB.upper", "BB.lower", "ATR", "VWAP", "VWMA",
    "Recommend.All", "Perf.W", "Perf.1M", "price_52_week_high", "price_52_week_low",
    "Pivot.M.Classic.S1", "Pivot.M.Classic.R1", "Pivot.M.Classic.R2",
    "price_earnings_ttm", "price_book_fq", "dividends_yield_current",
    "return_on_equity", "net_margin_ttm", "total_debt", "total_assets",
]

SAFE_COLS = [
    "name", "description", "sector", "industry", "close", "open", "high", "low",
    "change", "volume", "average_volume_10d_calc", "relative_volume_10d_calc",
    "market_cap_basic", "RSI", "RSI[1]", "Stoch.K", "Stoch.D", "MACD.macd",
    "MACD.signal", "EMA10", "EMA20", "EMA50", "EMA200", "SMA20", "SMA50", "SMA200",
    "ADX", "ADX+DI", "ADX-DI", "BB.upper", "BB.lower", "ATR", "VWMA",
    "Recommend.All", "Perf.W", "Perf.1M", "price_52_week_high", "price_52_week_low",
    "Pivot.M.Classic.S1", "Pivot.M.Classic.R1", "Pivot.M.Classic.R2",
    "price_earnings_ttm", "price_book_fq",
]


def load_issi_set():
    s = set(DEFAULT_ISSI)
    if os.path.exists(ISSI_FILE):
        try:
            with open(ISSI_FILE, "r", encoding="utf-8") as f:
                tokens = [t.strip().upper().replace("IDX:", "") for t in f.read().replace(",", "\n").splitlines()]
            custom = {t for t in tokens if 3 <= len(t) <= 5 and t.isalpha()}
            if custom:
                s = custom
        except Exception:
            pass
    return s


def round_fraksi_bei(price):
    if price is None or price <= 0:
        return 0
    tick = 1 if price < 200 else (2 if price < 500 else (5 if price < 2000 else (10 if price < 5000 else 25)))
    return int(round(price / tick) * tick)


def floor_fraksi_bei(price):
    if price is None or price <= 0:
        return 0
    tick = 1 if price < 200 else (2 if price < 500 else (5 if price < 2000 else (10 if price < 5000 else 25)))
    return max(50, int(math.floor(price / tick) * tick))


def safe_num(val, default=None):
    if val is None:
        return default
    try:
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return default


def post_tv_scanner(columns):
    payload = {
        "filter": [
            {"left": "exchange", "operation": "equal", "right": "IDX"},
            {"left": "close", "operation": "greater", "right": 50},
            {"left": "volume", "operation": "greater", "right": 0},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": columns,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 950],
    }
    req = urllib.request.Request(
        "https://scanner.tradingview.com/indonesia/scan",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def analyze_stock(row_dict, issi_set):
    ticker = (row_dict.get("name") or "").upper()
    close = safe_num(row_dict.get("close"), 0)
    if not ticker or close <= 0:
        return None

    open_p = safe_num(row_dict.get("open"), close)
    high_p = safe_num(row_dict.get("high"), close)
    low_p = safe_num(row_dict.get("low"), close)
    change = safe_num(row_dict.get("change"), 0)
    volume = safe_num(row_dict.get("volume"), 0)
    avg_vol = safe_num(row_dict.get("average_volume_10d_calc"), 0)
    rvol = safe_num(row_dict.get("relative_volume_10d_calc"))
    if rvol is None and avg_vol and avg_vol > 0:
        rvol = volume / avg_vol
    rvol = rvol or 1.0

    val_traded = close * volume
    rsi = safe_num(row_dict.get("RSI"), 50)
    rsi_prev = safe_num(row_dict.get("RSI[1]"), rsi)
    stoch_k = safe_num(row_dict.get("Stoch.K"), 50)
    stoch_d = safe_num(row_dict.get("Stoch.D"), 50)
    macd = safe_num(row_dict.get("MACD.macd"), 0)
    macd_sig = safe_num(row_dict.get("MACD.signal"), 0)
    macd_hist = macd - macd_sig

    ema10 = safe_num(row_dict.get("EMA10"), close)
    ema20 = safe_num(row_dict.get("EMA20"), close)
    ema50 = safe_num(row_dict.get("EMA50"), close)
    ema200 = safe_num(row_dict.get("EMA200"), ema50)
    sma20 = safe_num(row_dict.get("SMA20"), ema20)
    vwap = safe_num(row_dict.get("VWAP"), (high_p + low_p + close) / 3)
    vwma = safe_num(row_dict.get("VWMA"), sma20)

    adx = safe_num(row_dict.get("ADX"), 15)
    di_plus = safe_num(row_dict.get("ADX+DI"), 20)
    di_minus = safe_num(row_dict.get("ADX-DI"), 20)

    bb_up = safe_num(row_dict.get("BB.upper"), close * 1.05)
    bb_low = safe_num(row_dict.get("BB.lower"), close * 0.95)
    bbw = (bb_up - bb_low) / sma20 if sma20 > 0 else 0.15

    atr = safe_num(row_dict.get("ATR"))
    if not atr or atr <= 0:
        atr = max(close * 0.025, high_p - low_p)

    high_52w = safe_num(row_dict.get("price_52_week_high"), close)
    piv_s1 = safe_num(row_dict.get("Pivot.M.Classic.S1"), close * 0.95)
    piv_r1 = safe_num(row_dict.get("Pivot.M.Classic.R1"), close * 1.06)
    piv_r2 = safe_num(row_dict.get("Pivot.M.Classic.R2"), close * 1.12)

    pe = safe_num(row_dict.get("price_earnings_ttm"))
    pbv = safe_num(row_dict.get("price_book_fq"))
    roe = safe_num(row_dict.get("return_on_equity"))
    npm = safe_num(row_dict.get("net_margin_ttm"))
    div_yield = safe_num(row_dict.get("dividends_yield_current"), 0)
    tot_debt = safe_num(row_dict.get("total_debt"))
    tot_assets = safe_num(row_dict.get("total_assets"))
    tv_rec = safe_num(row_dict.get("Recommend.All"), 0)

    sector = row_dict.get("sector") or "-"
    industry = row_dict.get("industry") or "-"
    desc = row_dict.get("description") or ticker

    # 1. ISSI Syariah + OJK Debt/Asset <= 45%
    debt_asset_ratio = round((tot_debt / tot_assets) * 100, 1) if (tot_debt is not None and tot_assets and tot_assets > 0) else None
    ind_lower = (industry + " " + sector).lower()
    is_haram = any(k in ind_lower for k in NON_SYARIAH_KEYWORDS) or ("bank" in ind_lower and ticker not in {"BRIS", "BTPS", "PNBS", "BANK"})
    is_issi = (ticker in issi_set) and (ticker not in NON_SYARIAH_TICKERS) and (not is_haram) and (True if debt_asset_ratio is None else debt_asset_ratio <= 45.0)

    # 2. Smart Money VPA (Max 28)
    smart_score = 0
    tags = []
    if rvol >= 2.0 and close >= open_p:
        smart_score += 12
        tags.append("Volume Spike Institusi")
    elif rvol >= 1.35 and close >= open_p:
        smart_score += 8
        tags.append("Akumulasi Volume")
    elif rvol >= 1.5 and change > -1.5 and close > (low_p + (high_p - low_p) * 0.55):
        smart_score += 7
        tags.append("Absorption")

    if close > vwap:
        smart_score += 6
    if vwma > sma20:
        smart_score += 6
        tags.append("VWMA Bullish")
    if val_traded >= 5_000_000_000:
        smart_score += 4

    # 3. Trend SEPA (Max 27)
    trend_score = 0
    if close > ema20:
        trend_score += 6
    if ema20 > ema50:
        trend_score += 6
    if ema50 > ema200:
        trend_score += 6
    if close > ema20 > ema50 > ema200:
        tags.append("Stage-2 Uptrend")
    if adx >= 22 and di_plus > di_minus:
        trend_score += 5
    if high_52w > 0 and close >= high_52w * 0.78:
        trend_score += 4

    # 4. Momentum & Squeeze (Max 25)
    mom_score = 0
    is_squeeze = bbw <= 0.12
    is_breakout = close > ema20 and rvol >= 1.3 and change > 1.2 and (is_squeeze or close >= bb_up * 0.985)
    is_rebound = (26 <= rsi <= 43) and (rsi > rsi_prev) and (stoch_k > stoch_d) and (close >= open_p)

    if is_breakout:
        mom_score += 10
        tags.append("Squeeze Breakout" if is_squeeze else "Breakout")
    elif is_rebound:
        mom_score += 9
        tags.append("Sniper Rebound")

    if 50 <= rsi <= 68:
        mom_score += 7
    elif 43 <= rsi < 50 and rsi > rsi_prev:
        mom_score += 5
    elif rsi > 76:
        mom_score -= 6

    if macd > macd_sig and macd_hist > 0:
        mom_score += 6
    elif macd > macd_sig:
        mom_score += 4
    if stoch_k > stoch_d and stoch_k < 80:
        mom_score += 2

    # 5. GARP Fundamental (Max 20)
    fund_score = 0
    if pe is not None and 0 < pe <= 15:
        fund_score += 7
        tags.append("PER Murah")
    elif pe is not None and 15 < pe <= 24:
        fund_score += 4
    if pbv is not None and 0 < pbv <= 1.8:
        fund_score += 4
    elif pbv is not None and 1.8 < pbv <= 3.0:
        fund_score += 2
    if roe is not None and roe >= 12:
        fund_score += 5
        tags.append("ROE Tinggi")
    elif roe is not None and roe >= 6:
        fund_score += 3
    if npm is not None and npm >= 8:
        fund_score += 2
    if div_yield >= 3:
        fund_score += 2

    if tv_rec >= 0.4:
        smart_score += 2
    elif tv_rec <= -0.4:
        trend_score = max(0, trend_score - 5)

    alpha_score = max(0, min(100, round(smart_score + trend_score + mom_score + fund_score)))

    # 6. Exact Buy/Sell Plan (Fraksi BEI)
    risk_unit = max(atr * 1.45, close * 0.03)
    if is_rebound:
        entry_low = floor_fraksi_bei(close * 0.985)
        entry_high = round_fraksi_bei(close * 1.005)
        sl_raw = min(low_p * 0.98, close - risk_unit)
    elif is_breakout:
        entry_low = floor_fraksi_bei(max(ema20 * 0.99, close * 0.985))
        entry_high = round_fraksi_bei(close * 1.01)
        sl_raw = max(ema20 * 0.97, close - risk_unit)
    else:
        base_sup = min(ema20, vwap) if ema20 > 0 else close * 0.97
        entry_low = floor_fraksi_bei(max(base_sup, close * 0.97))
        entry_high = round_fraksi_bei(close)
        sl_raw = min(piv_s1, close - risk_unit)

    stop_loss = floor_fraksi_bei(min(sl_raw, entry_low * 0.96))
    if stop_loss >= entry_low:
        stop_loss = floor_fraksi_bei(entry_low * 0.94)

    risk_per_share = max(1, entry_high - stop_loss)
    tp1_calc = entry_high + (risk_per_share * 2.0)
    tp2_calc = entry_high + (risk_per_share * 3.5)

    tp1 = round_fraksi_bei(max(tp1_calc, piv_r1 if piv_r1 > entry_high * 1.03 else tp1_calc))
    tp2 = round_fraksi_bei(max(tp2_calc, piv_r2 if piv_r2 > tp1 * 1.03 else tp2_calc))
    rr_ratio = round((tp1 - entry_high) / risk_per_share, 2)

    if rsi >= 76 and change > 4:
        signal = "TAKE PROFIT / SELL"
        note = f"RSI Overbought ekstrem ({rsi:.1f}). Amankan profit bertahap atau pasang Trailing Stop di EMA10 (Rp {round_fraksi_bei(ema10):,})."
    elif alpha_score >= 76 and close > ema20 and rsi < 74:
        signal = "STRONG BUY"
        note = f"Konfluensi kuat (Skor {alpha_score}/100): aliran dana institusi & tren Stage-2 sejalan. Akumulasi di Rp {entry_low:,}–{entry_high:,}."
    elif is_breakout and alpha_score >= 62:
        signal = "BUY BREAKOUT"
        note = f"Breakout terkonfirmasi RVOL {rvol:.2f}x. Entry jika bertahan di atas Rp {entry_low:,} dengan disiplin SL Rp {stop_loss:,}."
    elif is_rebound and alpha_score >= 54:
        signal = "BUY ON WEAKNESS"
        note = f"Pantulan awal dari area jenuh jual (RSI {rsi:.1f}). Speculative buy dekat support menuju TP1 Rp {tp1:,}."
    elif close < ema50 and ema20 < ema50 and tv_rec < -0.15:
        signal = "SELL / AVOID"
        note = f"Struktur masih downtrend di bawah EMA50 (Rp {round_fraksi_bei(ema50):,}). Hindari dulu atau jual saat rebound."
    elif alpha_score >= 58:
        signal = "ACCUMULATE / WATCH"
        note = f"Struktur cukup baik (Skor {alpha_score}). Tunggu konfirmasi volume atau antre di support Rp {entry_low:,}."
    else:
        signal = "HOLD / NEUTRAL"
        note = "Momentum belum konvergen. Tunggu harga menembus EMA20 dengan volume di atas rata-rata."

    return {
        "ticker": ticker,
        "name": desc,
        "sector": sector,
        "is_issi": is_issi,
        "close": int(round(close, 0)),
        "change": round(change, 2),
        "alpha_score": alpha_score,
        "signal": signal,
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": stop_loss,
        "tp1": tp1,
        "tp2": tp2,
        "rr": rr_ratio,
        "sl_pct": round(((stop_loss - entry_high) / entry_high) * 100, 1),
        "tp1_pct": round(((tp1 - entry_high) / entry_high) * 100, 1),
        "tp2_pct": round(((tp2 - entry_high) / entry_high) * 100, 1),
        "rvol": round(rvol, 2),
        "rsi": round(rsi, 1),
        "adx": round(adx, 1),
        "value_b": round(val_traded / 1e9, 2),
        "pe": round(pe, 1) if pe is not None else None,
        "pbv": round(pbv, 2) if pbv is not None else None,
        "roe": round(roe, 1) if roe is not None else None,
        "div_yield": round(div_yield, 2),
        "debt_asset": debt_asset_ratio,
        "ema20": round_fraksi_bei(ema20),
        "ema50": round_fraksi_bei(ema50),
        "vwma_bull": vwma > sma20,
        "macd_bull": macd > macd_sig,
        "is_breakout": is_breakout,
        "is_rebound": is_rebound,
        "is_squeeze": is_squeeze,
        "p_smart": round(smart_score),
        "p_trend": round(trend_score),
        "p_mom": round(mom_score),
        "p_fund": round(fund_score),
        "tags": " • ".join(tags[:4]) if tags else sector,
        "note": note,
    }


@st.cache_data(ttl=30, show_spinner=False)
def fetch_tv_market_data():
    cols_used = FULL_COLS
    try:
        raw = post_tv_scanner(FULL_COLS)
    except urllib.error.HTTPError:
        cols_used = SAFE_COLS
        raw = post_tv_scanner(SAFE_COLS)

    issi_set = load_issi_set()
    rows = []
    for item in raw.get("data", []):
        row_dict = dict(zip(cols_used, item.get("d", [])))
        analyzed = analyze_stock(row_dict, issi_set)
        if analyzed:
            rows.append(analyzed)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["alpha_score", "value_b"], ascending=[False, False]).reset_index(drop=True)
    return df, time.strftime("%Y-%m-%d %H:%M:%S WIB")


# ========================
# UI HEADER & TICKER TAPE
# ========================
components.html(
    """
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {
        "symbols": [
          {"description":"IHSG","proName":"IDX:COMPOSITE"},
          {"description":"BRIS","proName":"IDX:BRIS"},
          {"description":"TLKM","proName":"IDX:TLKM"},
          {"description":"ADRO","proName":"IDX:ADRO"},
          {"description":"AMMN","proName":"IDX:AMMN"},
          {"description":"ANTM","proName":"IDX:ANTM"},
          {"description":"ASII","proName":"IDX:ASII"},
          {"description":"ICBP","proName":"IDX:ICBP"},
          {"description":"PGEO","proName":"IDX:PGEO"}
        ],
        "showSymbolLogo": true,
        "isTransparent": true,
        "displayMode": "adaptive",
        "colorTheme": "dark",
        "locale": "id"
      }
      </script>
    </div>
    """,
    height=48,
)

col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("α ALPHA IDX • IHSG & ISSI Quantitative Screener")
    st.caption("5-Pillar Institutional Engine • Live TradingView Data & Chart • OJK Syariah Filter • Fraksi BEI")
with col_h2:
    if st.button("🔄 Scan Ulang Live", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ========================
# SIDEBAR CONTROLS
# ========================
with st.sidebar:
    st.header("⚙️ Filter & Strategi")
    only_issi = st.toggle("☪ Khusus ISSI Syariah", value=True)
    preset = st.selectbox(
        "Strategi Screening",
        [
            "🌐 Semua Saham",
            "🏆 Top Alpha Sniper (Skor ≥ 70)",
            "🐋 Bandar Accumulation",
            "⚡ Squeeze Breakout",
            "💎 Value Growth (GARP)",
            "🎯 Rebound / Buy on Weakness",
        ],
    )
    min_val = st.selectbox(
        "Filter Likuiditas Harian",
        [0.0, 1.0, 5.0, 20.0],
        index=1,
        format_func=lambda x: "Semua Likuiditas" if x == 0 else f"Transaksi ≥ Rp {int(x)} Miliar",
    )
    search_q = st.text_input("Cari Kode / Nama Saham", placeholder="Mis: BRIS, TLKM, ADRO").strip().upper()

    st.divider()
    st.subheader("💰 Kalkulator Lot")
    capital = st.number_input("Modal Trading (Rp)", min_value=100_000, value=20_000_000, step=1_000_000)
    risk_pct = st.slider("Risiko Maks / Trade (%)", 0.5, 5.0, 2.0, 0.5)

    st.divider()
    with st.expander("☪ Update Daftar ISSI (DES OJK)"):
        current_issi = "\n".join(sorted(load_issi_set()))
        new_issi = st.text_area("Kode Saham ISSI (1 per baris / koma)", value=current_issi, height=160)
        if st.button("Simpan Daftar ISSI"):
            tokens = [t.strip().upper().replace("IDX:", "") for t in new_issi.replace(",", "\n").splitlines()]
            valid = sorted({t for t in tokens if 3 <= len(t) <= 5 and t.isalpha()})
            if valid:
                with open(ISSI_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(valid))
                st.cache_data.clear()
                st.success(f"{len(valid)} saham ISSI disimpan!")
                st.rerun()
            else:
                st.error("Tidak ada kode saham valid.")

# Fetch live data
with st.spinner("Mengambil data live seluruh saham IDX dari TradingView..."):
    try:
        df, updated_at = fetch_tv_market_data()
    except Exception as e:
        st.error(f"Gagal terhubung ke TradingView Scanner: {e}")
        st.stop()

# Apply Filters
fdf = df.copy()
if only_issi:
    fdf = fdf[fdf["is_issi"]]
if min_val > 0:
    fdf = fdf[fdf["value_b"] >= min_val]
if search_q:
    fdf = fdf[fdf["ticker"].str.contains(search_q) | fdf["name"].str.upper().str.contains(search_q)]

if "Top Alpha" in preset:
    fdf = fdf[fdf["alpha_score"] >= 70]
elif "Bandar" in preset:
    fdf = fdf[(fdf["rvol"] >= 1.35) & (fdf["vwma_bull"]) & (fdf["p_smart"] >= 16)]
elif "Squeeze" in preset:
    fdf = fdf[(fdf["is_breakout"]) | ((fdf["is_squeeze"]) & (fdf["alpha_score"] >= 60))]
elif "Value" in preset:
    fdf = fdf[fdf["pe"].notna() & (fdf["pe"] > 0) & (fdf["pe"] <= 18) & (fdf["roe"].isna() | (fdf["roe"] >= 10)) & (fdf["alpha_score"] >= 55)]
elif "Rebound" in preset:
    fdf = fdf[(fdf["is_rebound"]) | ((fdf["rsi"] <= 42) & (fdf["macd_bull"]))]

fdf = fdf.reset_index(drop=True)

# KPI Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Emiten IDX Terpantau", f"{len(df)}", "TradingView Live")
k2.metric("Lolos Filter ISSI", f"{int(df['is_issi'].sum())}", "DES + Debt/Asset ≤ 45%")
k3.metric("Strong Buy / Breakout", f"{int(df['signal'].isin(['STRONG BUY', 'BUY BREAKOUT']).sum())}", "Konfluensi Tinggi")
k4.metric("Hasil Filter Saat Ini", f"{len(fdf)}", f"Update: {updated_at}")

if fdf.empty:
    st.warning("Tidak ada saham yang memenuhi kriteria filter. Ubah preset atau turunkan minimal transaksi di sidebar.")
    st.stop()

# ========================
# TABEL HASIL SCREENING
# ========================
st.subheader(f"📊 Tabel Screener ({len(fdf)} Saham)")

display_cols = [
    "ticker", "is_issi", "close", "change", "alpha_score", "signal",
    "entry_low", "entry_high", "stop_loss", "tp1", "tp2", "rr",
    "rvol", "rsi", "value_b", "tags",
]
tbl_col, exp_col = st.columns([5, 1])
with exp_col:
    csv_bytes = fdf[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="screener_ihsg_issi.csv", mime="text/csv", use_container_width=True)

st.dataframe(
    fdf[display_cols],
    use_container_width=True,
    height=380,
    hide_index=True,
    column_config={
        "ticker": st.column_config.TextColumn("Kode", width="small"),
        "is_issi": st.column_config.CheckboxColumn("ISSI"),
        "close": st.column_config.NumberColumn("Harga", format="Rp %d"),
        "change": st.column_config.NumberColumn("Chg %", format="%.2f%%"),
        "alpha_score": st.column_config.ProgressColumn("Skor α", min_value=0, max_value=100, format="%d"),
        "signal": st.column_config.TextColumn("Rekomendasi"),
        "entry_low": st.column_config.NumberColumn("Beli Bawah", format="Rp %d"),
        "entry_high": st.column_config.NumberColumn("Beli Atas", format="Rp %d"),
        "stop_loss": st.column_config.NumberColumn("Cut Loss", format="Rp %d"),
        "tp1": st.column_config.NumberColumn("TP 1", format="Rp %d"),
        "tp2": st.column_config.NumberColumn("TP 2", format="Rp %d"),
        "rr": st.column_config.NumberColumn("R:R", format="1:%.1f"),
        "rvol": st.column_config.NumberColumn("RVOL", format="%.2fx"),
        "rsi": st.column_config.NumberColumn("RSI", format="%.1f"),
        "value_b": st.column_config.NumberColumn("Val (M)", format="%.1f M"),
        "tags": st.column_config.TextColumn("Pemicu Strategi"),
    },
)

# ========================
# INSPEKTOR SAHAM & LIVE TRADINGVIEW CHART
# ========================
st.divider()
sel_col1, sel_col2 = st.columns([3, 1])
with sel_col1:
    options = fdf["ticker"].tolist()
    labels = {
        r["ticker"]: f"IDX:{r['ticker']} — {r['name']} | {r['signal']} (Skor {r['alpha_score']}/100)"
        for _, r in fdf.iterrows()
    }
    selected_ticker = st.selectbox("🔍 Pilih Saham untuk Rencana Beli/Jual & Live Chart TradingView:", options, format_func=lambda t: labels[t])
with sel_col2:
    tf = st.selectbox("Timeframe Chart", ["15", "60", "D", "W"], index=2, format_func=lambda x: {"15": "15 Menit", "60": "1 Jam", "D": "Daily", "W": "Weekly"}[x])

s = fdf[fdf["ticker"] == selected_ticker].iloc[0]

# Header info saham terpilih
issi_tag = "☪ ISSI SYARIAH" if s["is_issi"] else "NON-ISSI"
st.markdown(f"### `IDX:{s['ticker']}` — {s['name']}  |  **Rp {s['close']:,}** ({s['change']:+.2f}%)  |  `{issi_tag}`  |  **{s['signal']}**")

# 4 Kotak Trade Plan
b1, b2, b3, b4 = st.columns(4)
b1.markdown(f"<div class='plan-box' style='border-color:#06b6d4'><div class='plan-label' style='color:#67e8f9'>Area Beli (Entry)</div><div class='plan-val'>Rp {s['entry_low']:,} – {s['entry_high']:,}</div></div>", unsafe_allow_html=True)
b2.markdown(f"<div class='plan-box' style='border-color:#f43f5e'><div class='plan-label' style='color:#fda4af'>Cut Loss (Stop Loss)</div><div class='plan-val' style='color:#fb7185'>Rp {s['stop_loss']:,} ({s['sl_pct']}%)</div></div>", unsafe_allow_html=True)
b3.markdown(f"<div class='plan-box' style='border-color:#10b981'><div class='plan-label' style='color:#6ee7b7'>Target Jual 1 (TP1)</div><div class='plan-val' style='color:#34d399'>Rp {s['tp1']:,} (+{s['tp1_pct']}%)</div></div>", unsafe_allow_html=True)
b4.markdown(f"<div class='plan-box' style='border-color:#f59e0b'><div class='plan-label' style='color:#fcd34d'>Target Jual 2 (TP2)</div><div class='plan-val' style='color:#fbbf24'>Rp {s['tp2']:,} (+{s['tp2_pct']}%)</div></div>", unsafe_allow_html=True)

# Kalkulator Lot + Analisa Catatan
risk_per_share = max(1, s["entry_high"] - s["stop_loss"])
max_loss_rp = capital * (risk_pct / 100.0)
lots = max(0, min(int(max_loss_rp // (risk_per_share * 100)), int(capital // (s["entry_high"] * 100))))
buy_val = lots * 100 * s["entry_high"]
pot_profit = lots * 100 * (s["tp1"] - s["entry_high"])
pot_loss = lots * 100 * risk_per_share

st.info(
    f"**Analisa Sistem:** {s['note']}  \n"
    f"**Money Management (Risk {risk_pct}% dari Rp {capital:,}):** Beli Maks **{lots} Lot** (Rp {buy_val:,}) • "
    f"Potensi Profit TP1: **+Rp {pot_profit:,}** • Risiko SL: **-Rp {pot_loss:,}** (R:R `1 : {s['rr']}`)"
)

# Pilar Skor & Fundamental
p1, p2, p3, p4, p5 = st.columns(5)
p1.metric("Bandar VPA", f"{s['p_smart']}/28")
p2.metric("Trend SEPA", f"{s['p_trend']}/27")
p3.metric("Momentum", f"{s['p_mom']}/25")
p4.metric("GARP Fund.", f"{s['p_fund']}/20")
p5.metric("Rasio Utang/Aset", f"{s['debt_asset']}%" if pd.notna(s["debt_asset"]) else "-", f"PER {s['pe']}x | ROE {s['roe']}%")

# Live TradingView Chart + Technical Gauge
chart_col, gauge_col = st.columns([2, 1])

with chart_col:
    st.markdown(f"**📈 Live TradingView Chart: `IDX:{s['ticker']}`**")
    components.html(
        f"""
        <div id="tv_chart" style="height:540px;width:100%;"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
          new TradingView.widget({{
            "autosize": true,
            "symbol": "IDX:{s['ticker']}",
            "interval": "{tf}",
            "timezone": "Asia/Jakarta",
            "theme": "dark",
            "style": "1",
            "locale": "id",
            "toolbar_bg": "#0f172a",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "studies": [
              {{ "id": "MASimple@tv-basicstudies", "inputs": {{ "length": 20 }} }},
              {{ "id": "MASimple@tv-basicstudies", "inputs": {{ "length": 50 }} }},
              "RSI@tv-basicstudies",
              "MACD@tv-basicstudies"
            ],
            "container_id": "tv_chart"
          }});
        </script>
        """,
        height=550,
    )

with gauge_col:
    st.markdown(f"**🧭 Speedometer TradingView: `IDX:{s['ticker']}`**")
    components.html(
        f"""
        <div class="tradingview-widget-container" style="height:540px;width:100%;">
          <div class="tradingview-widget-container__widget"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js" async>
          {{
            "interval": "1D",
            "width": "100%",
            "isTransparent": true,
            "height": "540",
            "symbol": "IDX:{s['ticker']}",
            "showIntervalTabs": true,
            "displayMode": "multiple",
            "locale": "id",
            "colorTheme": "dark"
          }}
          </script>
        </div>
        """,
        height=550,
    )