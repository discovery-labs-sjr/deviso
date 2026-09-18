from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import requests

API_BASE = "https://api.frankfurter.app"

# Fallbacks are intentionally limited to a small set of common currencies.
# They are only used when the live provider is unavailable.
TAUX_SECOURS: dict[str, float] = {
    "EUR": 1.0,
    "USD": 1.085,
    "GBP": 0.842,
    "JPY": 162.4,
    "CAD": 1.48,
    "CHF": 0.955,
    "XOF": 655.957,
}

NOMS_DEVISES: dict[str, str] = {
    "EUR": "Euro",
    "USD": "Dollar américain",
    "GBP": "Livre sterling",
    "JPY": "Yen japonais",
    "CAD": "Dollar canadien",
    "CHF": "Franc suisse",
    "AUD": "Dollar australien",
    "NZD": "Dollar néo-zélandais",
    "CNY": "Yuan chinois",
    "HKD": "Dollar de Hong Kong",
    "SGD": "Dollar de Singapour",
    "KRW": "Won sud-coréen",
    "INR": "Roupie indienne",
    "BRL": "Real brésilien",
    "MXN": "Peso mexicain",
    "ZAR": "Rand sud-africain",
    "SEK": "Couronne suédoise",
    "NOK": "Couronne norvégienne",
    "DKK": "Couronne danoise",
    "PLN": "Zloty polonais",
    "CZK": "Couronne tchèque",
    "HUF": "Forint hongrois",
    "RON": "Leu roumain",
    "BGN": "Lev bulgare",
    "TRY": "Livre turque",
    "ILS": "Nouveau shekel israélien",
    "ISK": "Couronne islandaise",
    "THB": "Baht thaïlandais",
    "MYR": "Ringgit malaisien",
    "PHP": "Peso philippin",
    "IDR": "Roupie indonésienne",
    "XOF": "Franc CFA (BCEAO)",
}

SYMBOLES = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "JPY": "¥",
    "XOF": "CFA",
}

FLAGS = {
    "EUR": "🇪🇺",
    "USD": "🇺🇸",
    "GBP": "🇬🇧",
    "JPY": "🇯🇵",
    "CAD": "🇨🇦",
    "CHF": "🇨🇭",
    "AUD": "🇦🇺",
    "NZD": "🇳🇿",
    "CNY": "🇨🇳",
    "HKD": "🇭🇰",
    "SGD": "🇸🇬",
    "KRW": "🇰🇷",
    "INR": "🇮🇳",
    "BRL": "🇧🇷",
    "MXN": "🇲🇽",
    "ZAR": "🇿🇦",
    "SEK": "🇸🇪",
    "NOK": "🇳🇴",
    "DKK": "🇩🇰",
    "PLN": "🇵🇱",
    "CZK": "🇨🇿",
    "HUF": "🇭🇺",
    "RON": "🇷🇴",
    "BGN": "🇧🇬",
    "TRY": "🇹🇷",
    "ILS": "🇮🇱",
    "ISK": "🇮🇸",
    "THB": "🇹🇭",
    "MYR": "🇲🇾",
    "PHP": "🇵🇭",
    "IDR": "🇮🇩",
    "XOF": "🌍",
}


def currency_label(code: str) -> str:
    name = NOMS_DEVISES.get(code, code)
    flag = FLAGS.get(code, "◉")
    return f"{flag}  {code} — {name}"


def clean_rates(raw: dict[str, Any]) -> dict[str, float]:
    rates: dict[str, float] = {"EUR": 1.0}
    for code, value in raw.items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric > 0:
            rates[str(code).upper()] = numeric

    # XOF is kept explicit so a provider response can never silently replace it.
    rates["XOF"] = TAUX_SECOURS["XOF"]
    return rates


def fetch_live_rates() -> tuple[dict[str, float], bool, str]:
    try:
        response = requests.get(
            f"{API_BASE}/latest",
            params={"from": "EUR"},
            timeout=6,
        )
        response.raise_for_status()
        payload = response.json()
        raw_rates = payload.get("rates", {})
        if not isinstance(raw_rates, dict):
            raise ValueError("Réponse de taux invalide")
        rates = clean_rates(raw_rates)
        if len(rates) <= 1:
            raise ValueError("Aucun taux retourné")
        return rates, True, str(payload.get("date", ""))
    except Exception:
        return clean_rates(TAUX_SECOURS), False, ""


def fetch_history_direct(src: str, tgt: str, days: int = 30) -> pd.DataFrame | None:
    end_day = date.today()
    start_day = end_day - timedelta(days=days)

    try:
        response = requests.get(
            f"{API_BASE}/{start_day.isoformat()}..{end_day.isoformat()}",
            params={"from": src, "to": tgt},
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("rates", {})
        if not isinstance(rows, dict) or not rows:
            return None

        parsed: list[dict[str, Any]] = []
        for day, values in rows.items():
            if not isinstance(values, dict) or tgt not in values:
                continue
            try:
                rate = float(values[tgt])
            except (TypeError, ValueError):
                continue
            if rate > 0:
                parsed.append({"Date": pd.to_datetime(day), "Taux": rate})

        if len(parsed) < 2:
            return None

        return pd.DataFrame(parsed).sort_values("Date").drop_duplicates("Date")


def fetch_history_xof_pair(src: str, tgt: str, days: int = 30) -> tuple[pd.DataFrame | None, str]:
    # XOF is handled through the EUR reference instead of pretending the provider
    # has a native XOF historical series.
    if src == "XOF" and tgt == "XOF":
        end_day = date.today()
        dates = pd.date_range(end=end_day, periods=days + 1, freq="D")
        return pd.DataFrame({"Date": dates, "Taux": 1.0}), "dérivé"

    other = tgt if src == "XOF" else src
    if other == "EUR":
        end_day = date.today()
        dates = pd.date_range(end=end_day, periods=days + 1, freq="D")
        if src == "XOF":
            value = 1.0 / TAUX_SECOURS["XOF"]
        else:
            value = float(TAUX_SECOURS["XOF"])
        return pd.DataFrame({"Date": dates, "Taux": value}), "dérivé"

    eur_other = fetch_history_direct("EUR", other, days=days)
    if eur_other is None or eur_other.empty:
        return None, "indisponible"

    if src == "XOF":
        values = eur_other["Taux"] / TAUX_SECOURS["XOF"]
    else:
        values = TAUX_SECOURS["XOF"] / eur_other["Taux"]

    frame = eur_other[["Date"]].copy()
    frame["Taux"] = values.astype(float)
    return frame, "dérivé"


def fetch_history(src: str, tgt: str, days: int = 30) -> tuple[pd.DataFrame | None, str]:
    if src == tgt:
        end_day = date.today()
        dates = pd.date_range(end=end_day, periods=days + 1, freq="D")
        return pd.DataFrame({"Date": dates, "Taux": 1.0}), "réel"

    if src == "XOF" or tgt == "XOF":
        return fetch_history_xof_pair(src, tgt, days)

    frame = fetch_history_direct(src, tgt, days)
    return frame, "réel" if frame is not None else "indisponible"


def convert_amount(
    amount: float,
    src: str,
    tgt: str,
    rates: dict[str, float],
    fee_pct: float = 0.0,
) -> dict[str, float]:
    src_rate = float(rates.get(src, 0.0))
    tgt_rate = float(rates.get(tgt, 0.0))
    if src_rate <= 0 or tgt_rate <= 0:
        raise ValueError("Taux de conversion indisponible")

    gross = (float(amount) / src_rate) * tgt_rate
    fee = gross * (max(0.0, float(fee_pct)) / 100.0)
    net = max(0.0, gross - fee)
    rate = tgt_rate / src_rate

    return {
        "gross": gross,
        "fee": fee,
        "net": net,
        "rate": rate,
    }


def format_number(value: float, decimals: int = 2) -> str:
    formatted = f"{float(value):,.{decimals}f}"
    return formatted.replace(",", " ").replace(".", ",")


def format_date(iso_date: str) -> str:
    if not iso_date:
        return "non disponible"
    try:
        return datetime.fromisoformat(iso_date).strftime("%d/%m/%Y")
    except ValueError:
        return iso_date
