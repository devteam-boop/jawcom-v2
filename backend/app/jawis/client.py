"""JAWIS API client for fetching business data."""

from typing import Optional, Dict, Any, List
import httpx
import logging
from datetime import datetime, timedelta

from ..config.settings import get_settings
from .schemas import (
    LeadSchema,
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
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to JAWIS API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            Response data
            
        Raises:
            JawisApiError: If API request fails
        """
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_data
        
        try:
            client = await self._get_client()
            response = await client.get(endpoint, params=params or {})
            
            if response.status_code == 200:
                data = response.json()
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
    
    async def get_lead(self, lead_id: str) -> Optional[LeadSchema]:
        """
        Get lead information by ID.
        
        Args:
            lead_id: Lead ID from JAWIS
            
        Returns:
            LeadSchema if found, None otherwise
        """
        try:
            data = await self._make_request(f"/api/leads/{lead_id}")
            return LeadSchema(**data["lead"]) if data.get("lead") else None
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
            return CompanySchema(**data["company"]) if data.get("company") else None
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
            return StageSchema(**data["stage"]) if data.get("stage") else None
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
            return UserSchema(**data["user"]) if data.get("user") else None
        except JawisApiError as e:
            if e.status_code == 404:
                return None
            logger.error(f"Error fetching user {user_id}: {str(e)}")
            raise
    
    async def get_lead_context(self, lead_id: str) -> Optional[LeadContextSchema]:
        """
        Get complete lead context including lead, company, stage, and assigned user.
        
        Args:
            lead_id: Lead ID from JAWIS
            
        Returns:
            LeadContextSchema with all related data
        """
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        
        # Fetch related data in parallel
        company = None
        stage = None
        assigned_user = None
        
        try:
            # Get stage (required)
            stage = await self.get_stage(lead.stage_key)
            if not stage:
                logger.warning(f"Stage {lead.stage_key} not found for lead {lead_id}")
                return None
            
            # Get company (optional)
            if lead.company_id:
                company = await self.get_company(lead.company_id)
            
            # Get assigned user (optional)
            if lead.assigned_to:
                assigned_user = await self.get_user(lead.assigned_to)
            
            return LeadContextSchema(
                lead=lead,
                company=company,
                stage=stage,
                assigned_user=assigned_user
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
            return [StageSchema(**stage) for stage in data.get("stages", [])]
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
