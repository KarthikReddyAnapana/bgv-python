from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic import Field as PField
from pydantic.alias_generators import to_camel
from sqlmodel import Field, SQLModel


# --- Enums (values mirror the Java enums exactly) ---
class UserRole(str, Enum):
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    CLIENT_USER = "CLIENT_USER"
    VERIFICATION_AGENT = "VERIFICATION_AGENT"
    CANDIDATE = "CANDIDATE"


class EmployeeType(str, Enum):
    LTIM_ASSOCIATES = "LTIM_ASSOCIATES"
    YET_TO_JOIN = "YET_TO_JOIN"


class ResourceType(str, Enum):
    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"


class GeoRegion(str, Enum):
    INDIA = "INDIA"
    LATAM = "LATAM"
    EUROPE = "EUROPE"
    APAC = "APAC"
    AUSTRALIA = "AUSTRALIA"
    USA_AND_CANADA = "USA_AND_CANADA"


class Country(str, Enum):
    INDIA = "INDIA"
    USA = "USA"
    CANADA = "CANADA"
    UK = "UK"
    AUSTRALIA = "AUSTRALIA"
    MEXICO = "MEXICO"
    BRAZIL = "BRAZIL"
    GERMANY = "GERMANY"
    FRANCE = "FRANCE"
    POLAND = "POLAND"
    NETHERLANDS = "NETHERLANDS"
    UNITED_KINGDOM = "UNITED_KINGDOM"
    COSTA_RICA = "COSTA_RICA"
    COLOMBIA = "COLOMBIA"
    BOLIVIA = "BOLIVIA"
    ARGENTINA = "ARGENTINA"
    ECUADOR = "ECUADOR"
    UAE = "UAE"
    MALAYSIA = "MALAYSIA"
    JAPAN = "JAPAN"
    SINGAPORE = "SINGAPORE"


class RequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"


class OnboardingType(str, Enum):
    REGULAR_REQUEST = "REGULAR_REQUEST"
    EXPRESS_REQUEST = "EXPRESS_REQUEST"


class BgvUserRole(str, Enum):
    PM = "PM"
    ADMIN = "ADMIN"


class Priority(str, Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


def _uuid() -> str:
    return str(uuid4())


class CamelModel(SQLModel):
    # Keep Python/database names in snake_case while exposing camelCase API fields.
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# --- Persistence models ---
class Organization(CamelModel, table=True):
    __tablename__ = "organizations"

    id: Optional[str] = Field(default_factory=_uuid, primary_key=True, max_length=36)
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class User(CamelModel, table=True):
    __tablename__ = "users"

    id: Optional[str] = Field(default_factory=_uuid, primary_key=True, max_length=36)
    email: str = Field(unique=True, index=True)
    password_hash: str
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    role: str = Field(max_length=50)
    organization_id: Optional[str] = Field(default=None, max_length=36)
    candidate_id: Optional[str] = Field(default=None, max_length=36)
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class BgvRequest(CamelModel, table=True):
    __tablename__ = "bgv_requests"

    id: Optional[str] = Field(default_factory=_uuid, primary_key=True, max_length=36)
    ps_number: Optional[str] = Field(default=None, max_length=50)
    requested_by_name: Optional[str] = None
    rr_number: Optional[float] = None
    employee_type: Optional[str] = Field(default=None, max_length=50)
    candidate_id: Optional[str] = Field(default=None, max_length=100)
    resource_name: Optional[str] = None
    resource_ps_no: Optional[str] = Field(default=None, max_length=50)
    resource_type: Optional[str] = Field(default=None, max_length=50)
    geo_region: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, max_length=50)
    bgv_initiated_by: Optional[str] = None
    comments_from_pmo: Optional[str] = Field(default=None, max_length=10000)
    bgv_stopped_reason: Optional[str] = Field(default=None, max_length=10000)
    onboarding_type: Optional[str] = Field(default=None, max_length=50)
    priority: Optional[str] = Field(default=None, max_length=20)
    interim_date: Optional[str] = Field(default=None, max_length=10)
    interim_status: Optional[str] = Field(default=None, max_length=100)
    final_bgv_date: Optional[str] = Field(default=None, max_length=10)
    final_bgv_status: Optional[str] = Field(default=None, max_length=100)
    request_submitted_on: Optional[str] = Field(default=None, max_length=10)
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    user_role: Optional[str] = Field(default=None, max_length=20)


class BgvRequestHistory(CamelModel, table=True):
    __tablename__ = "bgv_request_history"

    history_id: Optional[str] = Field(default_factory=_uuid, primary_key=True, max_length=36)
    bgv_request_id: Optional[str] = Field(default=None, max_length=36)
    action: Optional[str] = Field(default=None, max_length=50)
    ps_number: Optional[str] = Field(default=None, max_length=50)
    requested_by_name: Optional[str] = None
    rr_number: Optional[float] = None
    employee_type: Optional[str] = Field(default=None, max_length=50)
    candidate_id: Optional[str] = Field(default=None, max_length=100)
    resource_name: Optional[str] = None
    resource_ps_no: Optional[str] = Field(default=None, max_length=50)
    resource_type: Optional[str] = Field(default=None, max_length=50)
    geo_region: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, max_length=50)
    bgv_initiated_by: Optional[str] = None
    comments_from_pmo: Optional[str] = Field(default=None, max_length=10000)
    bgv_stopped_reason: Optional[str] = Field(default=None, max_length=10000)
    onboarding_type: Optional[str] = Field(default=None, max_length=50)
    priority: Optional[str] = Field(default=None, max_length=20)
    request_submitted_on: Optional[str] = Field(default=None, max_length=10)
    user_role: Optional[str] = Field(default=None, max_length=20)
    created_at: Optional[int] = None
    snapshot_at: Optional[int] = None


# --- API input models ---
class LoginRequest(BaseModel):
    email: str
    password: str


class BgvRequestIn(BaseModel):
    # Validate incoming JSON separately from database rows; store enum values as strings.
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    ps_number: str = PField(pattern=r"^[0-9]+$")
    requested_by_name: str = PField(min_length=1)
    rr_number: float = PField(ge=0)
    employee_type: EmployeeType
    candidate_id: Optional[str] = None
    resource_name: str = PField(min_length=1)
    resource_ps_no: Optional[str] = None
    resource_type: ResourceType
    geo_region: GeoRegion
    country: Country
    status: RequestStatus
    bgv_initiated_by: str = PField(min_length=1)
    comments_from_pmo: Optional[str] = None
    bgv_stopped_reason: Optional[str] = None
    onboarding_type: OnboardingType
    priority: Optional[Priority] = None
    interim_date: Optional[str] = None
    interim_status: Optional[str] = None
    final_bgv_date: Optional[str] = None
    final_bgv_status: Optional[str] = None
    request_submitted_on: date
    user_role: BgvUserRole

    @field_validator("request_submitted_on")
    @classmethod
    def _not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Request submitted date cannot be in future")
        return value
