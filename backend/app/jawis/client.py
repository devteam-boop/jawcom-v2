"""JAWIS API client for fetching business data."""

from typing import Optional, Dict, Any, List
import httpx
import logging
from datetime import datetime, timedelta

from ..config.settings import get_settings
from .schemas import (
    LeadSummarySchema,
    CompanySchema,
    StageSchema,
    UserSchema,
    LeadContextSchema,
    JawisApiResponse
)

logger = logging.getLogger(__name__)


class JawisApiError(Exception):
    """Exception raised for JAWIS API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class JawisClient:
    """
    Client for interacting with JAWIS (Business OS) APIs.
    
    Provides read-only access to business data:
    - Lead information
    - Company information  
    - Stage definitions
    - User information
    
    Implements caching to reduce API calls and improve performance.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize JAWIS client.
        
        Args:
            base_url: JAWIS API base URL (defaults to settings)
            api_key: JAWIS API key (defaults to settings)
        """
        settings = get_settings()
        self.base_url = base_url or settings.JAWIS_BASE_URL
        self.api_key = api_key or settings.JAWIS_API_KEY
        self.timeout = 30.0
        
        # Simple in-memory cache with TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(minutes=5)  # 5 minute cache
        
        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key for endpoint and parameters."""
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            return f"{endpoint}?{param_str}"
        return endpoint
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        cached_at = cache_entry.get("cached_at")
        if not cached_at:
            return False
        
        return datetime.utcnow() - cached_at < self._cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if valid."""
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry["data"]
            else:
                # Remove expired entry
                del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Set data in cache with timestamp."""
        self._cache[cache_key] = {
            "data": data,
            "cached_at": datetime.utcnow()
        }

    @staticmethod
    def _flatten_lead_data(lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Surface a JAWIS lead's semantic fields regardless of whether they
        arrive at the top level or nested under `custom_fields`/`metadata`.

        Root cause of first_name/building_name/seats/etc. resolving to None
        everywhere downstream (JawisLeadProvider, SendWhatsAppExecutor): the
        previous code passed `lead_data` straight into LeadSummarySchema, so
        it only ever saw whatever was flat at the top level. JAWIS's real
        `lead` object carries the CRM-specific fields (building_name/seats/
        plan_type/agent_name/options_link/tour_datetime/map_link/
        proposal_link/price/move_in_date/first_name/last_name/company) inside
        a nested `custom_fields` (or, on some responses, `metadata`)
        sub-object instead — the exact same "extra data lives in a sibling/
        nested container, not flat" shape already documented for `stage`
        above. Merging the nested dict in FIRST means an explicit top-level
        key (should JAWIS ever start sending one directly) still wins over
        its nested copy, rather than being clobbered by it.
        """
        if not isinstance(lead_data, dict):
            return lead_data
        nested = {}
        for key in ("custom_fields", "metadata"):
            value = lead_data.get(key)
            if isinstance(value, dict):
                nested.update(value)
        return {**nested, **lead_data}

    async def _make_request(
        self, endpoint: str, params: Optional[Dict] = None, force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to JAWIS API.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            force_refresh: Bypass the in-memory cache and hit JAWIS directly
                (the fresh response is still cached afterward for subsequent
                normal calls). Used by the Wait-node event scheduler
                (wait_condition_service.py) when polling for a stage/field
                change — the default 5-minute cache would otherwise delay
                detecting a change by up to 5 minutes. Every other existing
                caller is unaffected (default False, unchanged behavior).

        Returns:
            Response data

        Raises:
            JawisApiError: If API request fails
        """
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params)
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data
        
        try:
            client = await self._get_client()
            response = await client.get(endpoint, params=params or {})

            # TEMP DEBUG (remove after JAWIS lead-lookup investigation)
            logger.info("TEMP DEBUG [2] %s -> HTTP status code: %s", endpoint, response.status_code)
            logger.info("TEMP DEBUG [3] %s -> response headers: %s", endpoint, dict(response.headers))

            if response.status_code == 200:
                data = response.json()
                # TEMP DEBUG (remove after JAWIS lead-lookup investigation)
                logger.info("TEMP DEBUG [1] %s -> full raw JSON: %s", endpoint, data)
                # Cache successful responses
                self._set_cache(cache_key, data)
                logger.debug(f"API call successful: {endpoint}")
                return data
            else:
                error_msg = f"JAWIS API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text}"
                
                raise JawisApiError(error_msg, response.status_code, response.json() if response.text else None)
                
        except httpx.RequestError as e:
            raise JawisApiError(f"Request failed: {str(e)}")
        except Exception as e:
            if isinstance(e, JawisApiError):
                raise
            raise JawisApiError(f"Unexpected error: {str(e)}")
    
    async def get_lead(self, lead_id: str, force_refresh: bool = False) -> Optional[LeadSummarySchema]:
        """
        Get lead information by ID.

        force_refresh: bypass the in-memory cache — see _make_request's
        docstring. Default False, unchanged behavior for every existing
        caller.

        Uses LeadSummarySchema (id/name/email/phone/city/stage/first_name/
        last_name/company/building_name/agent_name/seats/plan_type/
        options_link/tour_datetime/map_link/proposal_link/price/
        move_in_date) — the lightweight lead lookup used for message sending
        and lead context. JAWIS's lead endpoint no longer returns stage_key/
        created_at/updated_at, so LeadSchema (which requires them) is no
        longer usable here. The lead's current stage is returned as a plain
        string alongside (not inside) "lead" in the response body — captured
        onto the returned object's `.stage` below.

        Root cause this docstring used to miss: JAWIS's `lead` object puts
        the semantic fields above (building_name/seats/agent_name/etc.)
        under a nested `custom_fields`/`metadata` sub-object rather than as
        flat top-level keys, the same way `stage` is a sibling of `lead`
        rather than nested inside it. Spreading `lead_data` directly into
        LeadSummarySchema (the previous behavior) only ever saw the flat
        top-level keys (id/name/email/phone/city), so every semantic field
        silently resolved to its Optional[...] default of None — not a
        missing-data problem, a wrong-extraction-path one. `_flatten_lead_data`
        below merges the nested container's keys in first, so top-level keys
        (if JAWIS ever sends one directly) still win over the nested copy.

        Args:
            lead_id: Lead ID from JAWIS

        Returns:
            LeadSummarySchema if found, None otherwise
        """
        try:
            data = await self._make_request(f"/api/leads/{lead_id}", force_refresh=force_refresh)

            # Supports both the legacy unwrapped shape ({"lead": {...}}) and
            # the current {"success": ..., "data": {"lead": {...}}} shape —
            # falls back to the raw response when there's no "data" envelope.
            payload = data.get("data", data) if isinstance(data, dict) else data
            lead_data = payload.get("lead") if isinstance(payload, dict) else None

            if not lead_data:
                return None

            # `stage` is a sibling of `lead` in the response, not a field of
            # `lead` itself — merged in here (not overriding lead_data's own
            # keys, since it has none named "stage") so get_lead_context()
            # can use it without a separate, no-longer-possible stage_key
            # lookup.
            stage_value = payload.get("stage") if isinstance(payload, dict) else None
            flattened_lead_data = self._flatten_lead_data(lead_data)
            result = LeadSummarySchema(**{**flattened_lead_data, "stage": stage_value})
            logger.info(
                "JawisClient.get_lead: lead_id=%s name=%s phone=%s email=%s stage=%s "
                "first_name=%s building_name=%s seats=%s",
                lead_id, result.name, result.phone, result.email, result.stage,
                result.first_name, result.building_name, result.seats,
            )
            return result
        except JawisApiError as e:
            if e.status_code == 404:
                return None
            logger.error(f"Error fetching lead {lead_id}: {str(e)}")
            raise
    
    async def get_company(self, company_id: str) -> Optional[CompanySchema]:
        """
        Get company information by ID.
        
        Args:
            company_id: Company ID from JAWIS
            
        Returns:
            CompanySchema if found, None otherwise
        """
        try:
            data = await self._make_request(f"/api/companies/{company_id}")
            payload = data.get("data", data) if isinstance(data, dict) else data
            company_data = payload.get("company") if isinstance(payload, dict) else None
            return CompanySchema(**company_data) if company_data else None
        except JawisApiError as e:
            if e.status_code == 404:
                return None
            logger.error(f"Error fetching company {company_id}: {str(e)}")
            raise
    
    async def get_stage(self, stage_key: str) -> Optional[StageSchema]:
        """
        Get stage information by key.
        
        Args:
            stage_key: Stage key from JAWIS
            
        Returns:
            StageSchema if found, None otherwise
        """
        try:
            data = await self._make_request(f"/api/stages/{stage_key}")
            payload = data.get("data", data) if isinstance(data, dict) else data
            stage_data = payload.get("stage") if isinstance(payload, dict) else None
            return StageSchema(**stage_data) if stage_data else None
        except JawisApiError as e:
            if e.status_code == 404:
                return None
            logger.error(f"Error fetching stage {stage_key}: {str(e)}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[UserSchema]:
        """
        Get user information by ID.
        
        Args:
            user_id: User ID from JAWIS
            
        Returns:
            UserSchema if found, None otherwise
        """
        try:
            data = await self._make_request(f"/api/users/{user_id}")
            payload = data.get("data", data) if isinstance(data, dict) else data
            user_data = payload.get("user") if isinstance(payload, dict) else None
            return UserSchema(**user_data) if user_data else None
        except JawisApiError as e:
            if e.status_code == 404:
                return None
            logger.error(f"Error fetching user {user_id}: {str(e)}")
            raise
    
    async def get_lead_context(self, lead_id: str, force_refresh: bool = False) -> Optional[LeadContextSchema]:
        """
        Get lead context (lead + current stage) for communication/execution.

        force_refresh: bypass the in-memory cache — see get_lead's docstring.
        Default False, unchanged behavior for every existing caller.

        Previously looked up a full StageSchema via get_stage(lead.stage_key)
        and also fetched company/assigned_user via lead.company_id/
        lead.assigned_to — all of that depended on fields JAWIS's lead
        endpoint no longer returns (LeadSummarySchema has no stage_key/
        company_id/assigned_to/metadata; see that class's docstring), so
        every call here crashed with AttributeError before this fix, was
        caught by the except below, and returned None — the caller
        (JawisLeadProvider.get_lead_context()) then fell back to a fabricated
        "Unknown"/null-phone lead, which is what actually reached the Send
        WhatsApp node.

        Company and assigned-user are no longer fetched (there is no field
        left to fetch them by) — always None now, not a fabricated value.
        Stage is synthesized from the plain string already present in the
        lead response (JAWIS never sends full stage metadata — no
        description/order — from this endpoint), which is sufficient for
        `.key`/`.name` (both set to the same string); `.order` is a
        placeholder 0, not a real pipeline position.

        Args:
            lead_id: Lead ID from JAWIS

        Returns:
            LeadContextSchema, or None only on a genuine failure (lead not
            found, no stage on the lead, or a request error) — never a
            fabricated stand-in.
        """
        lead = await self.get_lead(lead_id, force_refresh=force_refresh)
        if not lead:
            return None

        try:
            if not lead.stage:
                logger.warning(f"No stage returned by JAWIS for lead {lead_id} — cannot build lead context")
                return None
            stage = StageSchema(key=lead.stage, name=lead.stage, order=0)

            return LeadContextSchema(
                lead=lead,
                company=None,
                stage=stage,
                assigned_user=None,
            )

        except Exception as e:
            logger.error(f"Error building lead context for {lead_id}: {str(e)}")
            return None
    
    async def list_stages(self) -> List[StageSchema]:
        """
        Get all available stages.
        
        Returns:
            List of StageSchema objects
        """
        try:
            data = await self._make_request("/api/stages")
            payload = data.get("data", data) if isinstance(data, dict) else data
            stages = payload.get("stages", []) if isinstance(payload, dict) else []
            return [StageSchema(**stage) for stage in stages]
        except JawisApiError as e:
            logger.error(f"Error fetching stages: {str(e)}")
            return []
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("JAWIS client cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        valid_entries = sum(1 for entry in self._cache.values() if self._is_cache_valid(entry))
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "cache_ttl_minutes": self._cache_ttl.total_seconds() / 60
        }


# Global client instance
_global_client: Optional[JawisClient] = None


def get_jawis_client() -> JawisClient:
    """Get the global JAWIS client instance."""
    global _global_client
    if _global_client is None:
        _global_client = JawisClient()
    return _global_client


async def close_jawis_client() -> None:
    """Close the global JAWIS client."""
    global _global_client
    if _global_client:
        await _global_client.close()
        _global_client = None
