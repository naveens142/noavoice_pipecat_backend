from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
import pytz
import re
import dateparser

from app.config.logging import app_logger
logger = app_logger

DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_TIME = "09:00"


# ============================================================
# CLEAN INPUT
# ============================================================

def clean(text: str):

    if not text:
        return ""

    text = text.strip().lower()

    # fix ordinal
    text = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', text)

    text = text.replace(",", "")

    return text


# ============================================================
# ISO PARSER
# ============================================================

def parse_iso(text, tz):

    try:

        text = text.upper().replace(".000Z", "Z")

        utc = datetime.fromisoformat(text.replace("Z", "+00:00"))

        local = utc.astimezone(pytz.timezone(tz))

        return (

            local.strftime("%Y-%m-%d"),

            local.strftime("%H:%M"),

            utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        )

    except Exception as e:

        logger.error(f"ISO parse failed: {e}")

        return None, None, None


# ============================================================
# DATE PARSER (LEGACY SUPPORT)
# ============================================================

def parse_date(text, tz):

    now = datetime.now(pytz.timezone(tz))


    if text in ["today"]:
        return now.strftime("%Y-%m-%d")


    if text in ["tomorrow"]:
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")


    if text in ["day after tomorrow"]:
        return (now + timedelta(days=2)).strftime("%Y-%m-%d")


    if text == "next week":
        return (now + timedelta(days=7)).strftime("%Y-%m-%d")


    weekdays = {

        "monday":0,
        "tuesday":1,
        "wednesday":2,
        "thursday":3,
        "friday":4,
        "saturday":5,
        "sunday":6,

    }


    if text in weekdays:

        days = weekdays[text] - now.weekday()

        if days <= 0:
            days += 7

        return (now + timedelta(days=days)).strftime("%Y-%m-%d")


    return None


# ============================================================
# TIME PARSER
# ============================================================

def parse_time(text):

    if not text:
        return DEFAULT_TIME


    natural = {

        "morning":"09:00",
        "afternoon":"14:00",
        "evening":"18:00",
        "night":"20:00",
        "noon":"12:00",
        "midnight":"00:00"

    }


    if text in natural:
        return natural[text]


    text = text.replace(" ", "")


    match = re.match(

        r'(\d{1,2})(?::(\d{2}))?(am|pm)?',

        text

    )


    if not match:
        return None


    hour = int(match.group(1))

    minute = int(match.group(2) or 0)

    ampm = match.group(3)


    if ampm == "pm" and hour != 12:
        hour += 12


    if ampm == "am" and hour == 12:
        hour = 0


    return f"{hour:02d}:{minute:02d}"


# ============================================================
# UTC CONVERTER
# ============================================================

def to_utc(date, time, tz):

    local = pytz.timezone(tz).localize(

        datetime.strptime(

            f"{date} {time}",

            "%Y-%m-%d %H:%M"

        )

    )

    utc = local.astimezone(pytz.UTC)

    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


# ============================================================
# MAIN PARSER (UPGRADED - SUPPORTS 100+ FORMATS)
# ============================================================

def parse_datetime(

    text: str,

    tz: str = DEFAULT_TIMEZONE

) -> Tuple[Optional[str], Optional[str], Optional[str]]:


    if not text:
        return None, None, None


    original = text

    text = clean(text)


    # ISO
    if re.match(r'\d{4}-\d{2}-\d{2}t', text):

        return parse_iso(text, tz)


    # Use dateparser for everything else

    settings = {

        "TIMEZONE": tz,

        "RETURN_AS_TIMEZONE_AWARE": True,

        "PREFER_DATES_FROM": "future",

    }


    dt = dateparser.parse(text, settings=settings)


    if not dt:

        logger.error(f"Failed to parse: {original}")

        return None, None, None


    local = dt.astimezone(pytz.timezone(tz))

    utc = dt.astimezone(pytz.UTC)


    return (

        local.strftime("%Y-%m-%d"),

        local.strftime("%H:%M"),

        utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    )


# ============================================================
# DISPLAY
# ============================================================

def format_datetime_for_display(utc, tz=DEFAULT_TIMEZONE):

    local = datetime.fromisoformat(

        utc.replace("Z","+00:00")

    ).astimezone(pytz.timezone(tz))


    return local.strftime(

        "%B %d, %Y at %I:%M %p %Z"

    )


# backward compatibility
display = format_datetime_for_display


# ============================================================
# NORMALIZE TO UTC (FIXED)
# ============================================================

def normalize_to_utc(dt_str):

    dt = datetime.fromisoformat(

        dt_str.replace("Z", "+00:00")

    )

    return dt.astimezone(timezone.utc).strftime(

        "%Y-%m-%dT%H:%M:%SZ"

    )


# ============================================================
# PAST CHECK
# ============================================================

def is_past(utc_str):

    dt = datetime.fromisoformat(

        utc_str.replace("Z","+00:00")

    )

    return dt < datetime.now(timezone.utc)