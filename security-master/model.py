from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------
# ENUMS
# ---------------------------
class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    FIXED_INCOME = "FIXED_INCOME"
    DERIVATIVE = "DERIVATIVE"
    FUND = "FUND"
    FX = "FX"
    COMMODITY = "COMMODITY"
    OTHER = "OTHER"


class InstrumentType(str, Enum):
    COMMON_STOCK = "COMMON_STOCK"
    PREFERRED_STOCK = "PREFERRED_STOCK"
    CORPORATE_BOND = "CORPORATE_BOND"
    GOVERNMENT_BOND = "GOVERNMENT_BOND"
    ETF = "ETF"
    OPTION = "OPTION"
    FUTURE = "FUTURE"
    SWAP = "SWAP"
    WARRANT = "WARRANT"
    MUTUAL_FUND = "MUTUAL_FUND"


class Exchange(str, Enum):
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    LSE = "LSE"
    HKEX = "HKEX"
    TSE = "TSE"
    SIX = "SIX"
    EUREX = "EUREX"
    OTHER = "OTHER"


class DividendFrequency(str, Enum):
    NONE = "None"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    SEMIANNUAL = "SemiAnnual"
    ANNUAL = "Annual"


class MarketSegment(str, Enum):
    LARGE_CAP = "Large Cap"
    MID_CAP = "Mid Cap"
    SMALL_CAP = "Small Cap"
    MICRO_CAP = "Micro Cap"


class PricingSource(str, Enum):
    EXCHANGE = "Exchange"
    COMPOSITE = "Composite"
    VENDOR = "Vendor"
    INTERNAL = "Internal"
    OTHER = "Other"


class ValuationType(str, Enum):
    MARK_TO_MARKET = "Mark-to-Market"
    MARK_TO_MODEL = "Mark-to-Model"
    AMORTIZED_COST = "Amortized Cost"


class RiskClassification(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


class RecordStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"


class DataSource(str, Enum):
    BLOOMBERG = "Bloomberg"
    REFINITIV = "Refinitiv"
    ICE = "ICE"
    MORNINGSTAR = "Morningstar"
    INTERNAL = "Internal"
    OTHER = "Other"


# ---------------------------
# GROUPED SUB-MODELS
# ---------------------------
class SecurityDescription(BaseModel):
    security_name: str
    asset_class: AssetClass = AssetClass.EQUITY
    instrument_type: InstrumentType = InstrumentType.COMMON_STOCK
    issuer_name: str
    country_of_incorporation: str = Field(..., description="ISO 3166-1 alpha-2")
    exchange: Exchange = Exchange.NASDAQ
    currency: str = Field("USD", description="ISO 4217")
    sector: str = "Technology"
    industry_group: str = "Consumer Electronics"
    market_segment: MarketSegment = MarketSegment.LARGE_CAP
    general_description: str


class InstrumentDetails(BaseModel):
    listing_date: Optional[date] = None
    shares_outstanding: Optional[int] = None
    par_value: Optional[float] = None
    dividend_frequency: DividendFrequency = DividendFrequency.QUARTERLY
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    voting_rights: Optional[str] = None


class PricingValuation(BaseModel):
    last_price: Optional[float] = None
    pricing_source: PricingSource = PricingSource.EXCHANGE
    valuation_type: ValuationType = ValuationType.MARK_TO_MARKET
    price_timestamp: Optional[datetime] = None
    fifty_two_week_range: Optional[str] = None  # e.g., "160.00 – 240.00"


class CorporateActions(BaseModel):
    dividend_declaration_date: Optional[date] = None
    dividend_ex_date: Optional[date] = None
    dividend_payment_date: Optional[date] = None
    split_history: List[str] = Field(default_factory=list)


class RegulatoryCompliance(BaseModel):
    mifid_classification: Optional[str] = "Equity – Shares"
    risk_classification: RiskClassification = RiskClassification.LOW
    tax_status: Optional[str] = "Fully Taxable"
    esg_rating: Optional[str] = None  # e.g., "AA"


class OperationalMetadata(BaseModel):
    data_source: DataSource = DataSource.BLOOMBERG
    load_date: datetime = Field(default_factory=datetime.utcnow)
    record_status: RecordStatus = RecordStatus.ACTIVE
    created_by: Optional[str] = "DataFeed_BBG_Equities"
    last_updated_by: Optional[str] = None


# ---------------------------
# MAIN MODEL
# ---------------------------
class SecurityMasterRecord(BaseModel):
    # Tell Pydantic to emit enum values in JSON.
    model_config = ConfigDict(use_enum_values=True)

    # Identifiers for a specific security.
    security_id: str
    ticker: str
    isin: str
    cusip: Optional[str] = None
    sedol: Optional[str] = None
    bloomberg_ticker: Optional[str] = None
    figi: Optional[str] = None
    reuters_ric: Optional[str] = None

    security_description: SecurityDescription
    security_general_description_embedding: Optional[list[float]] = None
    instrument_details: InstrumentDetails = Field(default_factory=InstrumentDetails)
    pricing_valuation: PricingValuation = Field(default_factory=PricingValuation)
    corporate_actions: CorporateActions = Field(default_factory=CorporateActions)
    regulatory_compliance: RegulatoryCompliance = Field(default_factory=RegulatoryCompliance)
    operational_metadata: OperationalMetadata = Field(default_factory=OperationalMetadata)


# ---------------------------
# EXAMPLE
# ---------------------------
if __name__ == "__main__":
    apple = SecurityMasterRecord(
        security_id="0001",
        ticker="AAPL",
        isin="US0378331005",
        cusip="037833100",
        sedol="2046251",
        bloomberg_ticker="AAPL US Equity",
        figi="BBG000B9XRY4",
        reuters_ric="AAPL.OQ",

        security_description=SecurityDescription(
            security_name="Apple Inc.",
            asset_class=AssetClass.EQUITY,
            instrument_type=InstrumentType.COMMON_STOCK,
            issuer_name="Apple Inc.",
            country_of_incorporation="US",
            exchange=Exchange.NASDAQ,
            currency="USD",
            sector="Technology",
            industry_group="Consumer Electronics",
            market_segment=MarketSegment.LARGE_CAP,
            general_description="A tech company specializing in consumer electronics with strong growth."
        ),
        instrument_details=InstrumentDetails(
            listing_date=date(1980, 12, 12),
            shares_outstanding=15_589_000_000,
            par_value="0.00001",
            dividend_frequency=DividendFrequency.QUARTERLY,
            dividend_yield="0.0045",
            beta=1.23,
            voting_rights="1 vote per share",
        ),
        pricing_valuation=PricingValuation(
            last_price="230.50",
            pricing_source=PricingSource.EXCHANGE,
            valuation_type=ValuationType.MARK_TO_MARKET,
            price_timestamp=datetime(2025, 10, 28, 16, 0, 0),
            fifty_two_week_range="160.00 – 240.00",
        ),
        corporate_actions=CorporateActions(
            dividend_declaration_date=date(2025, 8, 10),
            dividend_ex_date=date(2025, 8, 17),
            dividend_payment_date=date(2025, 8, 25),
            split_history=["4-for-1 (2020-08-31)"],
        ),
        regulatory_compliance=RegulatoryCompliance(
            mifid_classification="Equity – Shares",
            risk_classification=RiskClassification.LOW,
            tax_status="Fully Taxable",
            esg_rating="AA",
        ),
        operational_metadata=OperationalMetadata(
            data_source=DataSource.BLOOMBERG,
            record_status=RecordStatus.ACTIVE,
            created_by="DataFeed_BBG_Equities",
            last_updated_by="DataOps_User_12",
        ),
    )

    # JSON (prettified)
    print(apple.model_dump_json(indent=2))
