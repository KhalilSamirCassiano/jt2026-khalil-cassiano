from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs" / "analysis_results"

FILES = {
    "details": ["Details_Itapema.csv", "details.csv"],
    "hosts": ["Hosts_ids_Itapema.csv", "hosts.csv"],
    "mesh": ["Mesh_Ids_Data_Itapema.csv", "mesh.csv"],
    "prices": ["Price_AV_Itapema.csv", "price.csv"],
    "sales": ["VivaReal_Itapema.csv", "vivareal.csv"],
}

RNG = np.random.default_rng(20260826)
HORIZON_DAYS = 90
SEASONALITY_HAIRCUT = 0.75
UNAVAILABLE_BOOKING_SHARE = 0.85
VARIABLE_COST_RATE = 0.33
ACQUISITION_COST_RATE = 0.05


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_suburb(value: object) -> str:
    text = normalize_text(value)
    mapping = {
        "meia praia": "Meia Praia",
        "meia praia - frente mar": "Meia Praia",
        "centro": "Centro",
        "morretes": "Morretes",
        "andorinha": "Andorinha",
        "castelo branco": "Castelo Branco",
        "canto da praia": "Canto da Praia",
        "tabuleiro dos oliveiras": "Tabuleiro dos Oliveiras",
        "tabuleiro": "Tabuleiro dos Oliveiras",
        "taboleiro": "Tabuleiro dos Oliveiras",
        "jardim praia mar": "Jardim Praiamar",
        "jardim praiamar": "Jardim Praiamar",
        "casa branca": "Casa Branca",
        "alto sao bento": "Alto Sao Bento",
        "ilhota": "Ilhota",
        "varzea": "Varzea",
        "sertao do trombudo": "Sertao do Trombudo",
        "sertaozinho": "Sertaozinho",
        "leopoldo zarling": "Leopoldo Zarling",
        "areal": "Areal",
        "lameiro": "Lameiro",
        "estreito": "Estreito",
        "itapema": "Itapema (sem bairro)",
        "ocean tower": "Itapema (sem bairro)",
        "none": "Sem bairro",
        "nan": "Sem bairro",
        "": "Sem bairro",
    }
    return mapping.get(text, str(value).strip() if not pd.isna(value) else "Sem bairro")


def as_bool(series: pd.Series) -> pd.Series:
    return series.map(
        lambda x: (
            True
            if str(x).strip().lower() == "true"
            else False
            if str(x).strip().lower() == "false"
            else np.nan
        )
    )


def bootstrap_median_ci(values: pd.Series, reps: int = 600) -> tuple[float, float]:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(float)
    if len(arr) < 3:
        return (np.nan, np.nan)
    idx = RNG.integers(0, len(arr), size=(reps, len(arr)))
    medians = np.median(arr[idx], axis=1)
    return tuple(np.quantile(medians, [0.025, 0.975]))


def load_data() -> dict[str, pd.DataFrame]:
    frames = {}
    for name, candidates in FILES.items():
        selected = next((DATA_DIR / filename for filename in candidates if (DATA_DIR / filename).exists()), None)
        if selected is None:
            raise FileNotFoundError(f"Nenhum arquivo encontrado para {name}: {candidates}")
        frames[name] = pd.read_csv(selected, low_memory=False, na_values=["<NA>"])
    return frames


def build_availability_metrics(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prices = prices.copy()
    prices["stay_date"] = pd.to_datetime(prices["date"], errors="coerce").dt.normalize()
    prices["capture_ts"] = pd.to_datetime(prices["aquisition_date"], errors="coerce")
    prices["capture_day"] = prices["capture_ts"].dt.normalize()
    prices["lead_days"] = (prices["stay_date"] - prices["capture_day"]).dt.days
    prices = prices.loc[prices["lead_days"].between(1, HORIZON_DAYS)].copy()
    prices = prices.drop_duplicates(["airbnb_listing_id", "capture_day", "stay_date"])

    all_metrics: list[dict] = []
    factors_rows: list[dict] = []
    for capture_day, snap in prices.groupby("capture_day", sort=True):
        listing_median = snap.groupby("airbnb_listing_id")["price"].median().rename("adr_median")
        snap = snap.join(listing_median, on="airbnb_listing_id")
        snap["relative_price"] = (snap["price"] / snap["adr_median"]).clip(0.40, 2.50)
        date_factor = snap.groupby("stay_date")["relative_price"].median().clip(0.55, 2.00)
        date_factor = date_factor / date_factor.mean()
        expected_dates = pd.date_range(
            capture_day + pd.Timedelta(days=1), periods=HORIZON_DAYS, freq="D"
        )
        date_factor = date_factor.reindex(expected_dates).interpolate(limit_direction="both").fillna(1.0)
        for stay_date, factor in date_factor.items():
            factors_rows.append(
                {
                    "capture_day": capture_day,
                    "stay_date": stay_date,
                    "seasonal_price_factor": float(factor),
                }
            )

        available_map = {
            listing_id: set(group["stay_date"])
            for listing_id, group in snap.groupby("airbnb_listing_id")
        }
        for listing_id, group in snap.groupby("airbnb_listing_id"):
            available = available_map[listing_id]
            base_adr = float(group["price"].median())
            expected_price = pd.Series(base_adr * date_factor.to_numpy(), index=expected_dates)
            unavailable_mask = ~expected_price.index.isin(available)
            unavailable_nights = int(unavailable_mask.sum())
            available_nights = HORIZON_DAYS - unavailable_nights
            gross_90 = float(expected_price.loc[unavailable_mask].sum())
            bucket_counts = [
                int(group["lead_days"].between(lo, hi).sum())
                for lo, hi in [(1, 30), (31, 60), (61, 90)]
            ]
            all_metrics.append(
                {
                    "airbnb_listing_id": listing_id,
                    "capture_day": capture_day,
                    "available_nights_90": available_nights,
                    "unavailable_nights_90": unavailable_nights,
                    "occupancy_proxy_90": unavailable_nights / HORIZON_DAYS,
                    "adr_available_median": base_adr,
                    "adr_available_mean": float(group["price"].mean()),
                    "gross_revenue_proxy_90": gross_90,
                    "annual_gross_run_rate": gross_90 / HORIZON_DAYS * 365,
                    "annual_gross_base": gross_90
                    / HORIZON_DAYS
                    * 365
                    * SEASONALITY_HAIRCUT
                    * UNAVAILABLE_BOOKING_SHARE,
                    "max_lead_observed": int(group["lead_days"].max()),
                    "available_days_1_30": bucket_counts[0],
                    "available_days_31_60": bucket_counts[1],
                    "available_days_61_90": bucket_counts[2],
                    "strict_calendar_sample": all(count > 0 for count in bucket_counts),
                }
            )
    return pd.DataFrame(all_metrics), pd.DataFrame(factors_rows)


def prepare_listings(frames: dict[str, pd.DataFrame], metrics: pd.DataFrame) -> pd.DataFrame:
    details = frames["details"].copy()
    hosts = frames["hosts"].copy()
    mesh = frames["mesh"].copy()

    hosts["host_snapshot_date"] = pd.to_datetime(hosts["host_snapshot_date"], errors="coerce")
    hosts = hosts.sort_values("host_snapshot_date").drop_duplicates("owner_id", keep="last")
    host_cols = [
        "owner_id",
        "is_superhost",
        "number_of_reviews_host",
        "is_verified",
        "star_rating_host",
        "years_host",
        "months_host",
    ]
    hosts = hosts[host_cols]

    mesh["suburb_clean"] = mesh["suburb"].map(normalize_suburb)
    mesh = mesh.rename(columns={"latitude": "mesh_latitude", "longitude": "mesh_longitude"})
    mesh = mesh[
        ["airbnb_listing_id", "mesh_latitude", "mesh_longitude", "suburb", "suburb_clean"]
    ]

    for col in ["can_instant_book", "is_professional", "is_new_listing"]:
        details[col] = as_bool(details[col])
    details["is_rated"] = details["star_rating"].gt(0)
    details["star_rating_clean"] = details["star_rating"].where(details["is_rated"])
    details["reviews_log"] = np.log1p(details["number_of_reviews"])
    details["cleaning_fee_log"] = np.log1p(details["cleaning_fee"].clip(lower=0))
    details["bedroom_band"] = details["number_of_bedrooms"].clip(upper=5).astype(int).astype(str)
    details.loc[details["number_of_bedrooms"].gt(5), "bedroom_band"] = "6+"

    amenity_text = (
        details["amenities"].fillna("").map(normalize_text)
        + " "
        + details["ad_description"].fillna("").map(normalize_text)
        + " "
        + details["space"].fillna("").map(normalize_text)
    )
    amenity_patterns = {
        "amenity_pool": r"\bpiscina\b|\bpool\b",
        "amenity_ac": r"ar[- ]condicionado|air conditioning",
        "amenity_parking": r"estacionamento|garagem|parking",
        "amenity_elevator": r"elevador|elevator",
        "amenity_beach": r"acesso (?:a|aa) praia|frente (?:para|ao) mar|beira[- ]mar|vista (?:para|do) mar|ocean view|beach access",
        "amenity_bbq": r"churrasqueira|barbecue|\bgrill\b",
        "amenity_washer": r"maquina de lavar|\bwasher\b",
        "amenity_wifi": r"wi[- ]?fi|wireless internet",
        "amenity_kitchen": r"cozinha|\bkitchen\b",
        "amenity_balcony": r"varanda|sacada|balcony",
    }
    for col, pattern in amenity_patterns.items():
        details[col] = amenity_text.str.contains(pattern, regex=True, na=False)

    metrics_validation = (
        "one_to_one" if not metrics["airbnb_listing_id"].duplicated().any() else "one_to_many"
    )
    listings = (
        details.merge(hosts, on="owner_id", how="left", validate="many_to_one")
        .merge(mesh, on="airbnb_listing_id", how="left", validate="one_to_one")
        .merge(metrics, on="airbnb_listing_id", how="inner", validate=metrics_validation)
    )
    listings["listing_type"] = listings["listing_type"].str.strip().str.lower()
    listings["is_superhost"] = listings["is_superhost"].fillna(False).astype(bool)
    listings["host_reviews_log"] = np.log1p(listings["number_of_reviews_host"].fillna(0))
    listings["host_experience_years"] = listings["years_host"].fillna(0) + listings[
        "months_host"
    ].fillna(0) / 12
    listings["lat_grid_500m"] = (listings["mesh_latitude"] / 0.0045).round() * 0.0045
    listings["lon_grid_500m"] = (listings["mesh_longitude"] / 0.0050).round() * 0.0050
    listings["geo_cell"] = (
        listings["lat_grid_500m"].round(4).astype(str)
        + ","
        + listings["lon_grid_500m"].round(4).astype(str)
    )
    return listings


def segment_summary(df: pd.DataFrame, keys: list[str], min_n: int = 10) -> pd.DataFrame:
    rows: list[dict] = []
    for group_key, group in df.groupby(keys, dropna=False, observed=True):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        if len(group) < min_n:
            continue
        lo, hi = bootstrap_median_ci(group["gross_revenue_proxy_90"])
        row = {key: value for key, value in zip(keys, group_key)}
        row.update(
            {
                "n_listings": len(group),
                "median_gross_revenue_proxy_90": group["gross_revenue_proxy_90"].median(),
                "gross_revenue_proxy_90_ci_low": lo,
                "gross_revenue_proxy_90_ci_high": hi,
                "median_annual_gross_base": group["annual_gross_base"].median(),
                "median_adr": group["adr_available_median"].median(),
                "median_occupancy_proxy": group["occupancy_proxy_90"].median(),
                "q25_gross_revenue_proxy_90": group["gross_revenue_proxy_90"].quantile(0.25),
                "q75_gross_revenue_proxy_90": group["gross_revenue_proxy_90"].quantile(0.75),
                "strict_sample_share": group["strict_calendar_sample"].mean(),
            }
        )
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["median_gross_revenue_proxy_90", "n_listings"], ascending=[False, False]
    )


def run_ols_driver_model(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    model = df.loc[df["strict_calendar_sample"]].copy()
    model = model.loc[
        model["gross_revenue_proxy_90"].gt(0)
        & model["number_of_bedrooms"].between(0, 5)
        & model["number_of_guests"].between(1, 16)
    ].copy()
    numeric = [
        "number_of_bedrooms",
        "number_of_bathrooms",
        "number_of_guests",
        "number_of_beds",
        "reviews_log",
        "cleaning_fee_log",
        "picture_count",
        "host_reviews_log",
        "host_experience_years",
    ]
    model["bedrooms_squared"] = model["number_of_bedrooms"] ** 2
    numeric.append("bedrooms_squared")
    binary = [
        "can_instant_book",
        "is_professional",
        "is_guest_favorite",
        "is_superhost",
        "amenity_pool",
        "amenity_ac",
        "amenity_parking",
        "amenity_elevator",
        "amenity_beach",
        "amenity_bbq",
        "amenity_washer",
        "amenity_wifi",
        "amenity_kitchen",
        "amenity_balcony",
    ]
    for col in numeric:
        model[col] = pd.to_numeric(model[col], errors="coerce")
        model[col] = model[col].fillna(model[col].median())
        std = model[col].std(ddof=0)
        model[col] = (model[col] - model[col].mean()) / (std if std > 0 else 1)
    for col in binary:
        model[col] = model[col].fillna(False).astype(int)
    binary = [col for col in binary if model[col].mean() >= 0.05 and model[col].mean() <= 0.95]
    suburb_counts = model["suburb_clean"].value_counts()
    model["suburb_model"] = model["suburb_clean"].where(
        model["suburb_clean"].map(suburb_counts).ge(20), "Outros bairros"
    )
    category = pd.get_dummies(
        model[["suburb_model", "listing_type"]].fillna("Desconhecido"),
        prefix=["bairro", "tipo"],
        drop_first=True,
        dtype=float,
    )
    features = pd.concat([model[numeric + binary].astype(float), category], axis=1)
    X = np.column_stack([np.ones(len(features)), features.to_numpy(float)])
    y = np.log1p(model["gross_revenue_proxy_90"].to_numpy(float))
    names = ["intercept"] + list(features.columns)

    beta = np.linalg.pinv(X) @ y
    fitted = X @ beta
    resid = y - fitted
    xtx_inv = np.linalg.pinv(X.T @ X)
    hat = np.sum((X @ xtx_inv) * X, axis=1).clip(0, 0.9999)
    adj_sq = (resid / (1 - hat)) ** 2
    meat = X.T @ (X * adj_sq[:, None])
    cov_hc3 = xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.clip(np.diag(cov_hc3), 0, None))
    t_stat = np.divide(beta, se, out=np.full_like(beta, np.nan), where=se > 0)
    impact_pct = (np.exp(beta) - 1) * 100

    sse = float(np.sum(resid**2))
    sst = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - sse / sst
    p = X.shape[1] - 1
    adj_r2 = 1 - (1 - r2) * (len(y) - 1) / max(len(y) - p - 1, 1)

    folds = np.arange(len(y)) % 5
    RNG.shuffle(folds)
    pred_cv = np.empty_like(y)
    for fold in range(5):
        train = folds != fold
        test = folds == fold
        b = np.linalg.pinv(X[train]) @ y[train]
        pred_cv[test] = X[test] @ b
    cv_r2 = 1 - float(np.sum((y - pred_cv) ** 2)) / sst

    result = pd.DataFrame(
        {
            "feature": names,
            "coefficient_log": beta,
            "robust_se_hc3": se,
            "t_stat": t_stat,
            "approx_impact_pct": impact_pct,
        }
    )
    result["abs_t"] = result["t_stat"].abs()
    result = result.sort_values("abs_t", ascending=False)
    diagnostics = {
        "n": len(y),
        "features_including_intercept": X.shape[1],
        "r2_in_sample": r2,
        "adjusted_r2": adj_r2,
        "r2_5fold_out_of_sample": cv_r2,
        "target": "log(1 + gross_revenue_proxy_90)",
        "sample": "strict_calendar_sample; 0-5 quartos; receita proxy positiva",
        "warning": "Associações condicionais, não efeitos causais.",
    }
    return result, diagnostics


def prepare_sales(sales: pd.DataFrame) -> pd.DataFrame:
    sales = sales.sort_values("aquisition_date").drop_duplicates("listing_id", keep="last").copy()
    sales["suburb_clean"] = sales["suburb"].map(normalize_suburb)
    sales["listing_type"] = sales["listing_type"].str.strip().str.lower()
    sales["price_per_sqm"] = sales["sale_price"] / sales["usable_area"].replace(0, np.nan)
    sales["bedroom_band"] = sales["bedrooms"].clip(upper=5).astype(int).astype(str)
    sales.loc[sales["bedrooms"].gt(5), "bedroom_band"] = "6+"
    sales["listing_title_normalized"] = sales["listing_title"].map(normalize_text)
    construction_pattern = (
        r"construc|lancamento|na planta|em obra|entrega|previsao|parcel|\bentrada\b|"
        r"\b2026\b|\b2027\b|\b2028\b|\b2029\b|\b2030\b"
    )
    sales["is_presale_or_construction"] = sales["listing_title_normalized"].str.contains(
        construction_pattern, regex=True, na=False
    )
    # Very small values (often R$1 or R$100) behave like portal placeholders.
    # Treat them as missing so the underwriting uses the peer median.
    sales["monthly_condo_fee"] = sales["monthly_condo_fee"].where(
        sales["monthly_condo_fee"].ge(150)
    )
    sales["yearly_iptu"] = sales["yearly_iptu"].where(sales["yearly_iptu"].ge(200))
    return sales


def build_investment_candidates(
    sales: pd.DataFrame, airbnb: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    peers = segment_summary(
        airbnb.loc[(airbnb["listing_type"] == "apartamento") & airbnb["strict_calendar_sample"]],
        ["suburb_clean", "number_of_bedrooms"],
        min_n=8,
    )
    peers = peers.rename(columns={"number_of_bedrooms": "bedrooms"})
    peer_cols = [
        "suburb_clean",
        "bedrooms",
        "n_listings",
        "median_annual_gross_base",
        "median_gross_revenue_proxy_90",
        "median_adr",
        "median_occupancy_proxy",
    ]
    peers = peers[peer_cols]

    clean = sales.loc[
        (sales["business_types"].isin(["Venda", "Ambos"]))
        & (sales["listing_type"] == "apartamento")
        & sales["bedrooms"].between(0, 4)
        & sales["sale_price"].between(250_000, 8_000_000)
        & sales["usable_area"].between(20, 350)
        & sales["price_per_sqm"].between(4_000, 50_000)
    ].copy()
    clean = clean.merge(peers, on=["suburb_clean", "bedrooms"], how="inner", validate="many_to_one")
    clean = clean.loc[clean["n_listings"].ge(8)].copy()

    condo_median = clean.groupby(["suburb_clean", "bedrooms"])["monthly_condo_fee"].transform("median")
    iptu_median = clean.groupby(["suburb_clean", "bedrooms"])["yearly_iptu"].transform("median")
    clean["monthly_condo_fee_used"] = clean["monthly_condo_fee"].fillna(condo_median).fillna(
        clean["monthly_condo_fee"].median()
    )
    clean["yearly_iptu_used"] = clean["yearly_iptu"].fillna(iptu_median).fillna(
        clean["yearly_iptu"].median()
    )
    clean["setup_cost"] = (60_000 + 25_000 * clean["bedrooms"]).clip(upper=175_000)
    clean["total_investment"] = (
        clean["sale_price"] * (1 + ACQUISITION_COST_RATE) + clean["setup_cost"]
    )
    clean["annual_noi_base"] = (
        clean["median_annual_gross_base"] * (1 - VARIABLE_COST_RATE)
        - clean["monthly_condo_fee_used"] * 12
        - clean["yearly_iptu_used"]
    )
    clean["gross_yield_base"] = clean["median_annual_gross_base"] / clean["total_investment"]
    clean["net_yield_base"] = clean["annual_noi_base"] / clean["total_investment"]
    clean["payback_years_base"] = clean["total_investment"] / clean["annual_noi_base"].replace(
        0, np.nan
    )

    for label, seasonal, booked_share in [
        ("low", 0.60, 0.70),
        ("base", SEASONALITY_HAIRCUT, UNAVAILABLE_BOOKING_SHARE),
        ("high", 0.90, 1.00),
    ]:
        gross = (
            clean["median_gross_revenue_proxy_90"]
            / HORIZON_DAYS
            * 365
            * seasonal
            * booked_share
        )
        noi = (
            gross * (1 - VARIABLE_COST_RATE)
            - clean["monthly_condo_fee_used"] * 12
            - clean["yearly_iptu_used"]
        )
        clean[f"annual_gross_{label}"] = gross
        clean[f"annual_noi_{label}"] = noi
        clean[f"net_yield_{label}"] = noi / clean["total_investment"]

    # Avoid selecting an apparent data-entry bargain: keep candidates within the
    # 10th-60th percentile of price/m² of their own neighbourhood-bedroom segment.
    clean["ppsqm_pct"] = clean.groupby(["suburb_clean", "bedrooms"])["price_per_sqm"].rank(
        pct=True
    )
    ranked = clean.loc[
        clean["ppsqm_pct"].between(0.10, 0.60)
        & clean["net_yield_low"].gt(0)
        & clean["median_occupancy_proxy"].between(0.05, 0.95)
        & ~clean["is_presale_or_construction"]
    ].sort_values(["net_yield_base", "n_listings"], ascending=[False, False])

    sales_segments = (
        clean.groupby(["suburb_clean", "bedrooms"], observed=True)
        .agg(
            n_sales=("listing_id", "nunique"),
            median_sale_price=("sale_price", "median"),
            median_usable_area=("usable_area", "median"),
            median_price_per_sqm=("price_per_sqm", "median"),
            median_monthly_condo=("monthly_condo_fee_used", "median"),
            median_yearly_iptu=("yearly_iptu_used", "median"),
        )
        .reset_index()
        .merge(peers, on=["suburb_clean", "bedrooms"], how="left", validate="one_to_one")
    )
    sales_segments["setup_cost"] = (60_000 + 25_000 * sales_segments["bedrooms"]).clip(
        upper=175_000
    )
    sales_segments["total_investment"] = (
        sales_segments["median_sale_price"] * (1 + ACQUISITION_COST_RATE)
        + sales_segments["setup_cost"]
    )
    sales_segments["annual_noi_base"] = (
        sales_segments["median_annual_gross_base"] * (1 - VARIABLE_COST_RATE)
        - sales_segments["median_monthly_condo"] * 12
        - sales_segments["median_yearly_iptu"]
    )
    sales_segments["net_yield_base"] = (
        sales_segments["annual_noi_base"] / sales_segments["total_investment"]
    )
    sales_segments["payback_years_base"] = (
        sales_segments["total_investment"] / sales_segments["annual_noi_base"]
    )
    sales_segments["evidence_level"] = np.select(
        [
            sales_segments["n_listings"].ge(30) & sales_segments["n_sales"].ge(30),
            sales_segments["n_listings"].ge(15) & sales_segments["n_sales"].ge(15),
        ],
        ["Alta", "Média"],
        default="Baixa",
    )
    sales_segments = sales_segments.sort_values(
        ["net_yield_base", "n_listings", "n_sales"], ascending=[False, False, False]
    )
    return ranked, peers, sales_segments


def test_compact_centro_thesis(
    sales: pd.DataFrame, airbnb: pd.DataFrame, reps: int = 5_000
) -> tuple[pd.DataFrame, dict]:
    """Testa Centro 1q contra alternativas usando bootstrap dos componentes do yield.

    Studios (0 quarto) são reportados separadamente porque não há observações no
    Centro. Logo, a evidência direta desta base vale para 1 quarto, não para studio.
    """
    clean_sales = sales.loc[
        sales["business_types"].isin(["Venda", "Ambos"])
        & sales["listing_type"].eq("apartamento")
        & sales["bedrooms"].between(0, 4)
        & sales["sale_price"].between(250_000, 8_000_000)
        & sales["usable_area"].between(20, 350)
        & sales["price_per_sqm"].between(4_000, 50_000)
    ].copy()
    segments = {
        "Centro, 1 quarto": ("Centro", 1),
        "Morretes, 2 quartos": ("Morretes", 2),
        "Meia Praia, 1 quarto": ("Meia Praia", 1),
        "Meia Praia, 2 quartos": ("Meia Praia", 2),
        "Centro, 2 quartos": ("Centro", 2),
    }
    sampling_rng = np.random.default_rng(20260826)
    rows: list[dict] = []
    yield_draws: dict[str, np.ndarray] = {}

    for segment, (suburb, bedrooms) in segments.items():
        a = airbnb.loc[
            airbnb["strict_calendar_sample"]
            & airbnb["listing_type"].eq("apartamento")
            & airbnb["suburb_clean"].eq(suburb)
            & airbnb["number_of_bedrooms"].eq(bedrooms)
        ].copy()
        s = clean_sales.loc[
            clean_sales["suburb_clean"].eq(suburb)
            & clean_sales["bedrooms"].eq(bedrooms)
        ].copy()
        s["condo_used"] = s["monthly_condo_fee"].fillna(s["monthly_condo_fee"].median())
        s["iptu_used"] = s["yearly_iptu"].fillna(s["yearly_iptu"].median())

        revenue = a["gross_revenue_proxy_90"].dropna().to_numpy(float)
        price = s["sale_price"].dropna().to_numpy(float)
        condo = s["condo_used"].dropna().to_numpy(float)
        iptu = s["iptu_used"].dropna().to_numpy(float)
        revenue_medians = np.median(
            sampling_rng.choice(revenue, size=(reps, len(revenue)), replace=True), axis=1
        )
        price_medians = np.median(
            sampling_rng.choice(price, size=(reps, len(price)), replace=True), axis=1
        )
        condo_medians = np.median(
            sampling_rng.choice(condo, size=(reps, len(condo)), replace=True), axis=1
        )
        iptu_medians = np.median(
            sampling_rng.choice(iptu, size=(reps, len(iptu)), replace=True), axis=1
        )

        annual_gross = (
            revenue_medians
            / HORIZON_DAYS
            * 365
            * SEASONALITY_HAIRCUT
            * UNAVAILABLE_BOOKING_SHARE
        )
        setup_cost = min(60_000 + 25_000 * bedrooms, 175_000)
        total_investment = price_medians * (1 + ACQUISITION_COST_RATE) + setup_cost
        annual_noi = (
            annual_gross * (1 - VARIABLE_COST_RATE)
            - condo_medians * 12
            - iptu_medians
        )
        segment_yield = annual_noi / total_investment
        yield_draws[segment] = segment_yield
        rows.append(
            {
                "segment": segment,
                "suburb": suburb,
                "bedrooms": bedrooms,
                "n_airbnb_strict": len(a),
                "n_sales": len(s),
                "revenue_90_median": np.median(revenue),
                "revenue_90_ci_low": np.quantile(revenue_medians, 0.025),
                "revenue_90_ci_high": np.quantile(revenue_medians, 0.975),
                "annual_gross_median": np.median(annual_gross),
                "sale_price_median": np.median(price),
                "total_investment_median": np.median(total_investment),
                "annual_noi_median": np.median(annual_noi),
                "net_yield_median": np.median(segment_yield),
                "net_yield_ci_low": np.quantile(segment_yield, 0.025),
                "net_yield_ci_high": np.quantile(segment_yield, 0.975),
            }
        )

    results = pd.DataFrame(rows)
    by_segment = results.set_index("segment")
    centro = by_segment.loc["Centro, 1 quarto"]
    morretes = by_segment.loc["Morretes, 2 quartos"]
    comparison = {
        "studio_centro_airbnb_count": int(
            (
                airbnb["suburb_clean"].eq("Centro")
                & airbnb["listing_type"].eq("apartamento")
                & airbnb["number_of_bedrooms"].eq(0)
            ).sum()
        ),
        "studio_centro_strict_count": int(
            (
                airbnb["suburb_clean"].eq("Centro")
                & airbnb["listing_type"].eq("apartamento")
                & airbnb["number_of_bedrooms"].eq(0)
                & airbnb["strict_calendar_sample"]
            ).sum()
        ),
        "morretes_2q_revenue_premium_vs_centro_1q": float(
            morretes["revenue_90_median"] / centro["revenue_90_median"] - 1
        ),
        "morretes_2q_noi_premium_vs_centro_1q": float(
            morretes["annual_noi_median"] / centro["annual_noi_median"] - 1
        ),
        "morretes_2q_yield_premium_vs_centro_1q": float(
            morretes["net_yield_median"] / centro["net_yield_median"] - 1
        ),
        "bootstrap_probability_morretes_2q_yield_gt_centro_1q": float(
            np.mean(
                yield_draws["Morretes, 2 quartos"]
                > yield_draws["Centro, 1 quarto"]
            )
        ),
        "bootstrap_repetitions": reps,
        "verdict": (
            "Não sustentada: não há studios no Centro na base; 1 quarto no Centro "
            "tem receita, NOI e yield inferiores a 2 quartos em Morretes."
        ),
    }
    return results, comparison


def capture_stability(all_listings: pd.DataFrame) -> pd.DataFrame:
    outputs = []
    for capture_day, group in all_listings.groupby("capture_day"):
        for dimension in ["suburb_clean", "number_of_bedrooms", "listing_type"]:
            summary = segment_summary(group, [dimension], min_n=10).head(10).copy()
            if summary.empty:
                continue
            summary.insert(0, "dimension", dimension)
            summary.insert(0, "capture_day", capture_day)
            summary = summary.rename(columns={dimension: "segment"})
            outputs.append(summary)
    return pd.concat(outputs, ignore_index=True) if outputs else pd.DataFrame()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa o mercado Airbnb e VivaReal de Itapema para decisão de investimento."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help="Pasta com os cinco CSVs (padrão: ./data).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUT_DIR,
        help="Pasta dos resultados tabulares (padrão: ./outputs/analysis_results).",
    )
    return parser.parse_args()


def main() -> None:
    global DATA_DIR, OUT_DIR
    args = parse_args()
    DATA_DIR = args.data_dir.resolve()
    OUT_DIR = args.output_dir.resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = load_data()
    all_metrics, date_factors = build_availability_metrics(frames["prices"])
    latest_capture = all_metrics["capture_day"].max()
    latest_metrics = all_metrics.loc[all_metrics["capture_day"].eq(latest_capture)].copy()
    latest = prepare_listings(frames, latest_metrics)

    all_listings = prepare_listings(frames, all_metrics)
    sales = prepare_sales(frames["sales"])

    summaries = {
        "by_listing_type": segment_summary(latest, ["listing_type"], 15),
        "by_bedrooms": segment_summary(latest, ["number_of_bedrooms"], 15),
        "by_suburb": segment_summary(latest, ["suburb_clean"], 15),
        "by_suburb_bedrooms": segment_summary(
            latest.loc[latest["listing_type"].eq("apartamento")],
            ["suburb_clean", "number_of_bedrooms"],
            10,
        ),
        "by_professional": segment_summary(latest, ["is_professional"], 15),
        "by_instant_book": segment_summary(latest, ["can_instant_book"], 15),
        "by_guest_favorite": segment_summary(latest, ["is_guest_favorite"], 15),
        "by_superhost": segment_summary(latest, ["is_superhost"], 15),
        "by_geo_cell": segment_summary(latest, ["geo_cell"], 10),
        "strict_by_bedrooms": segment_summary(
            latest.loc[latest["strict_calendar_sample"]], ["number_of_bedrooms"], 15
        ),
        "strict_by_suburb": segment_summary(
            latest.loc[latest["strict_calendar_sample"]], ["suburb_clean"], 15
        ),
        "strict_by_suburb_bedrooms": segment_summary(
            latest.loc[
                latest["strict_calendar_sample"] & latest["listing_type"].eq("apartamento")
            ],
            ["suburb_clean", "number_of_bedrooms"],
            10,
        ),
    }
    for name, table in summaries.items():
        table.to_csv(OUT_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")

    drivers, model_diag = run_ols_driver_model(latest)
    drivers.to_csv(OUT_DIR / "driver_model.csv", index=False, encoding="utf-8-sig")

    candidates, peer_segments, investment_segments = build_investment_candidates(sales, latest)
    compact_test, compact_comparison = test_compact_centro_thesis(sales, latest)
    candidate_cols = [
        "listing_id",
        "link_url",
        "listing_title",
        "suburb_clean",
        "bedrooms",
        "usable_area",
        "sale_price",
        "price_per_sqm",
        "monthly_condo_fee_used",
        "yearly_iptu_used",
        "n_listings",
        "median_adr",
        "median_occupancy_proxy",
        "median_gross_revenue_proxy_90",
        "annual_gross_low",
        "annual_gross_base",
        "annual_gross_high",
        "annual_noi_low",
        "annual_noi_base",
        "annual_noi_high",
        "total_investment",
        "net_yield_low",
        "net_yield_base",
        "net_yield_high",
        "payback_years_base",
        "ppsqm_pct",
        "is_presale_or_construction",
        "advertiser_name",
    ]
    candidates[candidate_cols].head(200).to_csv(
        OUT_DIR / "investment_candidates.csv", index=False, encoding="utf-8-sig"
    )
    peer_segments.to_csv(OUT_DIR / "investment_peer_segments.csv", index=False, encoding="utf-8-sig")
    investment_segments.to_csv(
        OUT_DIR / "investment_segment_returns.csv", index=False, encoding="utf-8-sig"
    )
    compact_test.to_csv(
        OUT_DIR / "compact_thesis_test.csv", index=False, encoding="utf-8-sig"
    )
    (OUT_DIR / "compact_thesis_test.json").write_text(
        json.dumps(compact_comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    stability = capture_stability(all_listings)
    stability.to_csv(OUT_DIR / "capture_stability.csv", index=False, encoding="utf-8-sig")
    date_factors.to_csv(OUT_DIR / "seasonal_price_factors.csv", index=False, encoding="utf-8-sig")

    latest_export_cols = [
        "airbnb_listing_id",
        "url",
        "ad_name",
        "suburb_clean",
        "mesh_latitude",
        "mesh_longitude",
        "listing_type",
        "number_of_bedrooms",
        "number_of_bathrooms",
        "number_of_beds",
        "number_of_guests",
        "number_of_reviews",
        "star_rating_clean",
        "cleaning_fee",
        "picture_count",
        "can_instant_book",
        "is_professional",
        "is_guest_favorite",
        "is_superhost",
        "available_nights_90",
        "unavailable_nights_90",
        "occupancy_proxy_90",
        "adr_available_median",
        "gross_revenue_proxy_90",
        "annual_gross_base",
        "strict_calendar_sample",
    ] + [col for col in latest.columns if col.startswith("amenity_")]
    latest[latest_export_cols].to_csv(
        OUT_DIR / "airbnb_analytic_base.csv", index=False, encoding="utf-8-sig"
    )

    best_candidate = candidates.iloc[0][candidate_cols].to_dict() if not candidates.empty else None
    metadata = {
        "as_of_airbnb_details": "2025-01-13",
        "as_of_airbnb_latest_price_capture": str(latest_capture.date()),
        "as_of_sales": "2025-01-11",
        "horizon_days": HORIZON_DAYS,
        "latest_capture_listings": int(len(latest)),
        "strict_calendar_listings": int(latest["strict_calendar_sample"].sum()),
        "assumptions": {
            "seasonality_haircut_base": SEASONALITY_HAIRCUT,
            "unavailable_booking_share_base": UNAVAILABLE_BOOKING_SHARE,
            "variable_cost_rate": VARIABLE_COST_RATE,
            "acquisition_cost_rate": ACQUISITION_COST_RATE,
            "setup_cost_formula": "R$60.000 + R$25.000 por quarto; teto R$175.000",
        },
        "model_diagnostics": model_diag,
        "compact_centro_thesis": compact_comparison,
        "best_candidate": {
            key: (value.item() if hasattr(value, "item") else value)
            for key, value in (best_candidate or {}).items()
        },
    }
    (OUT_DIR / "analysis_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    workbook_data = {
        "metadata": metadata,
        "tables": {
            name: json.loads(table.to_json(orient="records", date_format="iso"))
            for name, table in summaries.items()
        },
        "drivers": json.loads(drivers.to_json(orient="records")),
        "investment_candidates": json.loads(
            candidates[candidate_cols].head(50).to_json(orient="records")
        ),
        "investment_segments": json.loads(investment_segments.to_json(orient="records")),
        "compact_thesis": json.loads(compact_test.to_json(orient="records")),
        "analytic_base": json.loads(latest[latest_export_cols].to_json(orient="records")),
    }
    (OUT_DIR / "workbook_data.json").write_text(
        json.dumps(workbook_data, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    print(json.dumps(metadata, ensure_ascii=False, indent=2, default=str))
    for name, table in summaries.items():
        print(f"\n=== {name} ===")
        print(table.head(12).to_string(index=False))
    print("\n=== top drivers ===")
    print(drivers.loc[drivers["feature"].ne("intercept")].head(20).to_string(index=False))
    print("\n=== top candidates ===")
    print(candidates[candidate_cols].head(20).to_string(index=False))
    print("\n=== segment returns ===")
    print(investment_segments.head(20).to_string(index=False))


if __name__ == "__main__":
    main()

