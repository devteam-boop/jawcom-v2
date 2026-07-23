"""Pydantic schemas for JAWIS API integration."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class LeadSchema(BaseModel):
    """Schema for lead data from JAWIS."""
    
    id: str = Field(..., description="Lead ID from JAWIS")
    name: str = Field(..., description="Lead name")
    email: Optional[str] = Field(None, description="Lead email address")
    phone: Optional[str] = Field(None, description="Lead phone number")
    stage_key: str = Field(..., description="Current stage key")
    company_id: Optional[str] = Field(None, description="Associated company ID")
    assigned_to: Optional[str] = Field(None, description="Assigned user ID")
    created_at: datetime = Field(..., description="Lead creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional lead metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LeadSummarySchema(BaseModel):
    """Lightweight lead schema for the Communication Engine's lead lookup.

    Matches JAWIS's reduced lead payload (id/name/email/phone/city — no
    stage_key/created_at/updated_at/company_id/assigned_to/metadata; those
    were removed from JAWIS's lead payload). Used by JawisClient.get_lead()
    and, via ``stage``, by get_lead_context() — see that method's docstring
    for why the current lead's stage now comes from this response's
    top-level ``stage`` field (a plain string) rather than a stage_key
    lookup. This is also LeadContextSchema.lead's type now (LeadSchema,
    which required stage_key/created_at/updated_at, is unusable here since
    JAWIS no longer sends those).

    ``first_name``/``building_name``/``agent_name`` (and, for the later-stage
    production journeys' WhatsApp/email templates, ``seats``/``options_link``/
    ``plan_type``/``price``/``tour_datetime``/``map_link``/``proposal_link``/
    ``move_in_date``) are additive, optional fields for the JAWIS variable
    resolver (see ``SendWhatsAppExecutor``) — declared here so they pass
    through if JAWIS's lead payload includes them; if JAWIS omits one, it
    resolves to None rather than being fabricated from ``name``/elsewhere.
    """

    id: str = Field(..., description="Lead ID from JAWIS")
    name: str = Field(..., description="Lead name")
    email: Optional[str] = Field(None, description="Lead email address")
    phone: Optional[str] = Field(None, description="Lead phone number")
    city: Optional[str] = Field(None, description="Lead city")
    first_name: Optional[str] = Field(None, description="Lead first name (JAWIS-provided, never derived from `name`)")
    building_name: Optional[str] = Field(None, description="Building/property name associated with the lead")
    agent_name: Optional[str] = Field(None, description="Name of the agent assigned to the lead")
    seats: Optional[str] = Field(None, description="Seat/unit count of interest (Follow-Up/Qualified stage templates)")
    options_link: Optional[str] = Field(None, description="Link to shared unit/plan options (Qualified stage)")
    tour_datetime: Optional[str] = Field(None, description="Scheduled tour date/time (Tour Scheduled stage)")
    map_link: Optional[str] = Field(None, description="Map/directions link for the scheduled tour")
    plan_type: Optional[str] = Field(None, description="Selected plan/unit type (Proposal/Won stage)")
    proposal_link: Optional[str] = Field(None, description="Link to the sent proposal document")
    price: Optional[str] = Field(None, description="Quoted price (Proposal stage)")
    move_in_date: Optional[str] = Field(None, description="Target/confirmed move-in date (Proposal/Won stage)")
    stage: Optional[str] = Field(
        None, description="Lead's current stage (plain string, e.g. 'qualified') — "
        "from the sibling 'stage' field in JAWIS's /api/leads/{id} response, not part of 'lead' itself",
    )


class CompanySchema(BaseModel):
    """Schema for company data from JAWIS."""
    
    id: str = Field(..., description="Company ID from JAWIS")
    name: str = Field(..., description="Company name")
    industry: Optional[str] = Field(None, description="Company industry")
    size: Optional[str] = Field(None, description="Company size")
    website: Optional[str] = Field(None, description="Company website")
    created_at: datetime = Field(..., description="Company creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional company metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StageSchema(BaseModel):
    """Schema for stage data from JAWIS."""
    
    key: str = Field(..., description="Stage key (unique identifier)")
    name: str = Field(..., description="Stage display name")
    description: Optional[str] = Field(None, description="Stage description")
    order: int = Field(..., description="Stage order in pipeline")
    is_active: bool = Field(True, description="Whether stage is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional stage metadata")


class UserSchema(BaseModel):
    """Schema for user data from JAWIS."""
    
    id: str = Field(..., description="User ID from JAWIS")
    name: str = Field(..., description="User full name")
    email: str = Field(..., description="User email address")
    role: Optional[str] = Field(None, description="User role")
    is_active: bool = Field(True, description="Whether user is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional user metadata")


class WebhookEventSchema(BaseModel):
    """Schema for webhook events from JAWIS."""
    
    event_id: str = Field(..., description="Unique event ID")
    event_type: str = Field(..., description="Type of event (e.g., 'lead.created')")
    timestamp: datetime = Field(..., description="Event timestamp")
    source: str = Field(default="jawis", description="Event source system")
    data: Dict[str, Any] = Field(..., description="Event payload data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookResponseSchema(BaseModel):
    """Schema for webhook response."""
    
    success: bool = Field(..., description="Whether webhook was processed successfully")
    event_id: str = Field(..., description="Event ID that was processed")
    message: Optional[str] = Field(None, description="Response message")
    errors: List[str] = Field(default_factory=list, description="Any processing errors")


class JawisApiResponse(BaseModel):
    """Generic schema for JAWIS API responses."""
    
    success: bool = Field(..., description="Whether API call was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")


class LeadContextSchema(BaseModel):
    """Schema for lead context data used in communication."""

    # LeadSummarySchema, not LeadSchema (see that class's docstring) —
    # JAWIS's actual /api/leads/{id} response no longer carries the fields
    # LeadSchema requires (stage_key/created_at/updated_at), so LeadSchema
    # can never be constructed from a real API response.
    lead: LeadSummarySchema = Field(..., description="Lead information")
    company: Optional[CompanySchema] = Field(None, description="Associated company information")
    stage: StageSchema = Field(..., description="Current stage information")
    assigned_user: Optional[UserSchema] = Field(None, description="Assigned user information")
    
    @property
    def lead_id(self) -> str:
        """Get lead ID."""
        return self.lead.id
    
    @property
    def lead_name(self) -> str:
        """Get lead name."""
        return self.lead.name
    
    @property
    def lead_email(self) -> Optional[str]:
        """Get lead email."""
        return self.lead.email
    
    @property
    def lead_phone(self) -> Optional[str]:
        """Get lead phone."""
        return self.lead.phone
    
    @property
    def stage_key(self) -> str:
        """Get current stage key."""
        return self.stage.key
    
    @property
    def stage_name(self) -> str:
        """Get current stage name."""
        return self.stage.name
    
    @property
    def company_name(self) -> Optional[str]:
        """Get company name if available."""
        return self.company.name if self.company else None
    
    @property
    def assigned_user_name(self) -> Optional[str]:
        """Get assigned user name if available."""
        return self.assigned_user.name if self.assigned_user else None
