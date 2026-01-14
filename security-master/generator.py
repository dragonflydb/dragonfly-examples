from __future__ import annotations

import random
import string
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Dict, Any

from faker import Faker

_faker = Faker()

from model import (
    SecurityMasterRecord, SecurityDescription, InstrumentDetails, PricingValuation,
    CorporateActions, RegulatoryCompliance, OperationalMetadata,
    AssetClass, InstrumentType, Exchange, DividendFrequency, MarketSegment,
    PricingSource, ValuationType, RiskClassification, RecordStatus, DataSource
)


# ---------------------------
# Helpers
# ---------------------------
def rand_numeric(n: int) -> str:
    return "".join(random.choices(string.digits, k=n))


def rand_alphanum(n: int) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=n))


def _rand_ticker(n: int = 3) -> str:
    return "".join(random.choices(string.ascii_uppercase, k=n))


def _country_for_exchange(ex: Exchange) -> str:
    return {
        Exchange.NASDAQ: "US",
        Exchange.NYSE: "US",
        Exchange.LSE: "GB",
        Exchange.HKEX: "HK",
        Exchange.TSE: "JP",
        Exchange.SIX: "CH",
        Exchange.EUREX: "DE",
        Exchange.OTHER: "US",
    }.get(ex, "US")


def _ric_suffix_for_exchange(ex: Exchange) -> str:
    return {
        Exchange.NASDAQ: ".OQ",
        Exchange.NYSE: ".N",
        Exchange.LSE: ".L",
        Exchange.HKEX: ".HK",
        Exchange.TSE: ".T",
        Exchange.SIX: ".S",
        Exchange.EUREX: ".DE",
        Exchange.OTHER: ".US",
    }.get(ex, ".US")


def _currency_for_exchange(ex: Exchange) -> str:
    return {
        Exchange.NASDAQ: "USD",
        Exchange.NYSE: "USD",
        Exchange.LSE: "GBP",
        Exchange.HKEX: "HKD",
        Exchange.TSE: "JPY",
        Exchange.SIX: "CHF",
        Exchange.EUREX: "EUR",
        Exchange.OTHER: "USD",
    }.get(ex, "USD")


def _fake_company() -> str:
    if _faker:
        return _faker.company()
    prefixes = ["Global", "Prime", "Pioneer", "Summit", "Apex", "Vertex"]
    suffixes = ["Technologies", "Holdings", "Industries", "Group", "Corporation"]
    return f"{random.choice(prefixes)} {random.choice(suffixes)}"


def _fake_sector_industry() -> tuple[str, str]:
    sectors = [
        ("Technology", "Consumer Electronics"),
        ("Technology", "Software"),
        ("Financials", "Banks"),
        ("Healthcare", "Pharmaceuticals"),
        ("Consumer Discretionary", "Internet & Direct Marketing Retail"),
        ("Industrials", "Aerospace & Defense"),
        ("Communication Services", "Interactive Media"),
    ]
    return random.choice(sectors)


def _gen_isin(country_code: str) -> str:
    # Pattern-valid (not checksum-validated): CC + 10 alphanum + 2 digits
    return country_code + rand_alphanum(10) + rand_numeric(2)


def _gen_cusip() -> str:
    # 9 characters, not checksum-validated (fine for mocks)
    return rand_alphanum(9)


def _gen_sedol() -> str:
    # 7 characters, not checksum-validated
    return rand_alphanum(7)


def _gen_figi() -> str:
    # Typical-looking FIGI (not validated)
    return "BBG" + rand_alphanum(9)


def _mk_52w_range(last: float, spread_pct: float = 0.25) -> str:
    # ± spread around last; ensure sensible min/max
    low = max(0.01, last * (1 - spread_pct) * random.uniform(0.95, 1.0))
    high = last * (1 + spread_pct) * random.uniform(1.0, 1.05)
    return f"{low:.2f} – {high:.2f}"


def _risk_from_beta(beta: Optional[float]) -> RiskClassification:
    if beta is None:
        return random.choice(list(RiskClassification))
    if beta < 0.9:
        return RiskClassification.LOW
    if beta < 1.2:
        return RiskClassification.MEDIUM
    if beta < 1.6:
        return RiskClassification.HIGH
    return RiskClassification.VERY_HIGH


def _maybe_splits() -> list[str]:
    samples = [
        "2-for-1 (2014-06-09)",
        "3-for-1 (2022-07-25)",
        "4-for-1 (2020-08-31)",
        "5-for-1 (2019-05-15)",
    ]
    k = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
    return random.sample(samples, k=k)


def _recent_quarter_dates() -> tuple[date, date, date]:
    # A simple recent dividend cycle
    today = datetime.now(tz=timezone.utc).date()
    # pick a quarter boundary in the last ~180 days
    decl = today - timedelta(days=random.randint(60, 150))
    ex = decl + timedelta(days=random.randint(5, 15))
    pay = ex + timedelta(days=random.randint(5, 20))
    return decl, ex, pay


def _maybe(value, p: float = 0.5):
    return value if random.random() < p else None


def _generate_description_from_fields(data: Dict) -> str:
    templates = [
        "{security_name} is a {sector} company in {industry_group} industry, listed on {exchange}.",
        "{issuer_name} ({security_name}) operates in {country_of_incorporation}'s {sector} sector, focusing on {industry_group}.",
        "A {currency}-denominated {instrument_type} of {issuer_name} trading on {exchange} in the {sector} sector.",
        "{issuer_name}, incorporated in {country_of_incorporation}, is a {sector} company with {industry_group} operations."
    ]
    template = random.choice(templates)
    description = template.format(
        security_name=data.get('security_name', 'Company'),
        sector=data.get('sector', 'diversified').lower(),
        industry_group=data.get('industry_group', 'various industries').lower(),
        exchange=data.get('exchange', 'major exchange'),
        issuer_name=data.get('issuer_name', 'the company'),
        country_of_incorporation=data.get('country_of_incorporation', 'multiple countries'),
        currency=data.get('currency', 'USD'),
        instrument_type=str(data.get('instrument_type', 'common stock')).lower().replace('_', ' ')
    )
    return description[:200].strip()


# ---------------------------
# Main factory
# ---------------------------

def generate_security_master_record(
        *,
        ticker: Optional[str] = None,
        exchange: Optional[Exchange] = None,
        issuer_name: Optional[str] = None,
        seed: Optional[int] = None,
        overrides: Optional[Dict[str, Any]] = None,
) -> SecurityMasterRecord:
    """
    Create a plausible SecurityMasterRecord (equity) with reasonable defaults.
    - Set `seed` for reproducible output.
    - Use `overrides` to patch any nested field (dot-keys supported for convenience).
      e.g. overrides={"pricing_valuation.last_price": 123.45)}
    """
    if seed is not None:
        random.seed(seed)
        if _faker:
            _faker.seed_instance(seed)

    # Core picks
    ticker = ticker or _rand_ticker(random.choice([3, 4, 5, 6]))
    exchange = exchange or random.choice(list(Exchange))
    issuer_name = issuer_name or _fake_company()
    security_name = issuer_name
    country = _country_for_exchange(exchange)
    currency = _currency_for_exchange(exchange)

    # Descriptive
    sector, industry = _fake_sector_industry()

    # Instrument details
    listing_year = random.randint(1980, datetime.now(tz=timezone.utc).year - 1)
    listing_date = date(listing_year, random.randint(1, 12), random.randint(1, 28))
    shares_outstanding = random.randint(100_000_000, 20_000_000_000)
    par_value = random.choice([0.00001, 0.0001, 0.001, 0.01])
    dividend_frequency = random.choices(
        [DividendFrequency.NONE, DividendFrequency.QUARTERLY, DividendFrequency.ANNUAL, DividendFrequency.SEMIANNUAL],
        weights=[0.25, 0.55, 0.15, 0.05],
        k=1
    )[0]
    dividend_yield = random.uniform(0.0, 0.05) if dividend_frequency != DividendFrequency.NONE else None
    beta = round(random.uniform(0.7, 1.7), 2)
    voting_rights = _maybe("1 vote per share", 0.8)

    # Pricing
    last_price = random.uniform(5, 300)
    price_timestamp = datetime.now(tz=timezone.utc)
    fifty_two_week_range = _mk_52w_range(last_price, spread_pct=random.uniform(0.15, 0.40))

    # IDs
    isin = _gen_isin(country)
    cusip = _gen_cusip() if country == "US" else None
    sedol = _gen_sedol() if country in {"GB", "IE"} else None
    bloomberg_ticker = f"{ticker} {_country_for_exchange(exchange)} Equity"
    reuters_ric = f"{ticker}{_ric_suffix_for_exchange(exchange)}"
    figi = _gen_figi()

    # Corporate actions
    decl, ex, pay = _recent_quarter_dates() if dividend_frequency != DividendFrequency.NONE else (None, None, None)
    splits = _maybe_splits()

    # Compliance
    risk_cls = _risk_from_beta(beta)
    tax_status = random.choice(["Fully Taxable", "Tax-Exempt", "Deferred"])
    esg_rating = _maybe(random.choice(["AAA", "AA", "A", "BBB", "BB"]), 0.7)

    # Operational
    data_source = random.choice(list(DataSource))
    record_status = random.choices(
        [RecordStatus.ACTIVE, RecordStatus.SUSPENDED, RecordStatus.INACTIVE, RecordStatus.TERMINATED],
        weights=[0.92, 0.03, 0.03, 0.02],
        k=1
    )[0]
    created_by = random.choice(["DataFeed_BBG_Equities", "Refinitiv_Ingest", "ICE_Prices", "Manual_Entry"])
    last_updated_by = _maybe(random.choice(["DataOps_User_12", "QA_Batch_01", "ETL_Service"]), 0.75)

    asset_class = random.choice(list(AssetClass))
    instrument_type = random.choice(list(InstrumentType))
    market_segment = random.choice(list(MarketSegment))

    description_data = {
        "security_name": security_name,
        "issuer_name": issuer_name,
        "sector": sector,
        "industry_group": industry,
        "exchange": exchange.value,
        "country_of_incorporation": country,
        "currency": currency,
        "instrument_type": instrument_type.value
    }
    general_description = _generate_description_from_fields(description_data)

    record = SecurityMasterRecord(
        # identifiers
        security_id=rand_alphanum(16),
        ticker=ticker,
        isin=isin,
        cusip=cusip,
        sedol=sedol,
        bloomberg_ticker=bloomberg_ticker,
        figi=figi,
        reuters_ric=reuters_ric,

        # groups
        security_description=SecurityDescription(
            security_name=security_name,
            asset_class=asset_class,
            instrument_type=instrument_type,
            issuer_name=issuer_name,
            country_of_incorporation=country,
            exchange=exchange,
            currency=currency,
            sector=sector,
            industry_group=industry,
            market_segment=market_segment,
            general_description=general_description,
        ),
        instrument_details=InstrumentDetails(
            listing_date=listing_date,
            shares_outstanding=shares_outstanding,
            par_value=par_value,
            dividend_frequency=dividend_frequency,
            dividend_yield=dividend_yield,
            beta=beta,
            voting_rights=voting_rights,
        ),
        pricing_valuation=PricingValuation(
            last_price=last_price,
            pricing_source=PricingSource.EXCHANGE,
            valuation_type=ValuationType.MARK_TO_MARKET,
            price_timestamp=price_timestamp,
            fifty_two_week_range=fifty_two_week_range,
        ),
        corporate_actions=CorporateActions(
            dividend_declaration_date=decl,
            dividend_ex_date=ex,
            dividend_payment_date=pay,
            split_history=splits,
        ),
        regulatory_compliance=RegulatoryCompliance(
            mifid_classification="Equity – Shares",
            risk_classification=risk_cls,
            tax_status=tax_status,
            esg_rating=esg_rating,
        ),
        operational_metadata=OperationalMetadata(
            data_source=data_source,
            load_date=datetime.now(tz=timezone.utc),
            record_status=record_status,
            created_by=created_by,
            last_updated_by=last_updated_by,
        ),
    )

    # ---- Apply overrides (supports dotted keys) ----
    if overrides:
        def set_dotted(obj, dotted_key: str, value: Any):
            parts = dotted_key.split(".")
            target = obj
            for p in parts[:-1]:
                target = getattr(target, p)
            # Pydantic v2 models are mutable by default
            setattr(target, parts[-1], value)

        for k, v in overrides.items():
            set_dotted(record, k, v)

    return record


# ---------------------------
# EXAMPLE
# ---------------------------
if __name__ == "__main__":
    rec = generate_security_master_record(seed=43)  # reproducible
    print(rec.model_dump_json(indent=2))
