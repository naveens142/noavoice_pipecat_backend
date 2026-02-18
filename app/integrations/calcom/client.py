import httpx
import logging
from typing import Any, Dict, Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)

class CalComV2Client:
    """
    Cal.com V2 API Client
    Uses httpx for async HTTP calls
    """
    
    def __init__(self):
        self.base_url = settings.CALCOM_BASE_URL
        self.api_version = settings.CALCOM_API_VERSION
        self.headers = {
            "Authorization": f"Bearer {settings.CALCOM_API_KEY}",
            "Content-Type": "application/json",
            "cal-api-version": self.api_version
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Base method for all API calls"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.info(f"📡 Cal.com V2 {method.upper()} {url}")
                
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"✅ Cal.com V2 response status: {result.get('status')}")
                return result
                
            except httpx.HTTPStatusError as e:
                error_body = e.response.text
                logger.error(f"❌ Cal.com V2 HTTP error {e.response.status_code}: {error_body}")
                raise Exception(f"Cal.com API error {e.response.status_code}: {error_body}")
                
            except httpx.TimeoutException:
                logger.error("❌ Cal.com V2 request timed out")
                raise Exception("Cal.com API request timed out")
                
            except Exception as e:
                logger.error(f"❌ Cal.com V2 unexpected error: {e}")
                raise

    # ─── SLOTS ───────────────────────────────────────────────────

    async def get_available_slots(
        self,
        start_date: str,
        end_date: str,
        timezone: str = "Asia/Kolkata"
    ) -> Dict:
        """
        Get available slots for event type
        
        Cal.com V2 endpoint: GET /v2/slots
        Requires: cal-api-version: 2024-09-04
        
        Args:
            start_date: "2024-08-13" (YYYY-MM-DD)
            end_date:   "2024-08-14" (YYYY-MM-DD)
            timezone:   "Asia/Kolkata"
        """
        params = {
            "eventTypeId": settings.CALCOM_EVENT_TYPE_ID,
            "start": start_date,
            "end": end_date,
            "timeZone": timezone
        }
        
        # Slots endpoint uses different API version
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {**self.headers, "cal-api-version": "2024-09-04"}
            response = await client.get(
                f"{self.base_url}/slots",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    # ─── BOOKINGS ─────────────────────────────────────────────────

    async def create_booking(
        self,
        start: str,
        name: str,
        email: str,
        timezone: str = "Asia/Kolkata",
        phone: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Create a new booking
        
        Cal.com V2 endpoint: POST /v2/bookings
        V2 supports phoneNumber natively!
        
        Args:
            start:    "2024-08-13T09:00:00Z" (ISO 8601 UTC)
            name:     "John Doe"
            email:    "john@example.com"
            timezone: "Asia/Kolkata"
            phone:    "+919876543210" (optional)
            notes:    "First visit" (optional)
        """
        payload = {
            "start": start,
            "eventTypeId": settings.CALCOM_EVENT_TYPE_ID,
            "attendee": {
                "name": name,
                "email": email,
                "timeZone": timezone,
                "language": "en"
            }
        }
        
        # Add phone if provided (V2 supports this natively!)
        if phone:
            payload["attendee"]["phoneNumber"] = phone
        
        # Add notes as booking field response
        if notes:
            payload["bookingFieldsResponses"] = {"notes": notes}
        
        return await self._request("POST", "/bookings", data=payload)

    async def get_booking(self, booking_uid: str) -> Dict:
        """
        Get a single booking by UID
        
        Cal.com V2 endpoint: GET /v2/bookings/{bookingUid}
        """
        return await self._request("GET", f"/bookings/{booking_uid}")

    async def get_bookings_by_email(self, email: str) -> Dict:
        """
        Get all bookings for a patient by email
        
        Cal.com V2 endpoint: GET /v2/bookings
        """
        params = {
            "attendeeEmail": email,
            "eventTypeId": settings.CALCOM_EVENT_TYPE_ID
        }
        return await self._request("GET", "/bookings", params=params)

    async def reschedule_booking(
        self,
        booking_uid: str,
        new_start: str,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Reschedule an existing booking
        
        Cal.com V2 endpoint: POST /v2/bookings/{bookingUid}/reschedule
        
        Args:
            booking_uid: "abc123xyz" (from original booking)
            new_start:   "2024-08-15T10:00:00Z" (new time in UTC)
            reason:      "Patient requested different time" (optional)
        """
        payload = {"start": new_start}
        
        if reason:
            payload["reschedulingReason"] = reason
        
        return await self._request(
            "POST",
            f"/bookings/{booking_uid}/reschedule",
            data=payload
        )

    async def cancel_booking(
        self,
        booking_uid: str,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Cancel an existing booking
        
        Cal.com V2 endpoint: POST /v2/bookings/{bookingUid}/cancel
        
        Args:
            booking_uid: "abc123xyz"
            reason:      "Patient cancelled" (optional)
        """
        payload = {}
        if reason:
            payload["cancellationReason"] = reason
        
        return await self._request(
            "POST",
            f"/bookings/{booking_uid}/cancel",
            data=payload
        )

# Single instance used everywhere
calcom_client = CalComV2Client()