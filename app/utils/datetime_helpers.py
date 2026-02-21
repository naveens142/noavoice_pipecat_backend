from datetime import datetime, timedelta,timezone
from typing import Optional, Tuple
import pytz
import re
import logging


logger = logging.getLogger(__name__)


DEFAULT_TIMEZONE = "Asia/Kolkata"

DEFAULT_TIME = "09:00"


# ============================================================
# CLEAN INPUT
# ============================================================

def clean(text: str):

    text = text.strip().lower()

    text = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', text)

    text = text.replace(",", "")

    return text


# ============================================================
# ISO PARSER
# ============================================================

def parse_iso(text, tz):

    try:

        text = text.upper()

        text = text.replace(".000Z", "Z")

        utc = datetime.fromisoformat(text.replace("Z", "+00:00"))

        local = utc.astimezone(pytz.timezone(tz))

        return (

            local.strftime("%Y-%m-%d"),

            local.strftime("%H:%M"),

            utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        )

    except:

        return None, None, None


# ============================================================
# DATE PARSER
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


    if text == "next month":

        return (now + timedelta(days=30)).strftime("%Y-%m-%d")


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


    formats = [

        "%d %b",
        "%d %B",
        "%b %d",
        "%B %d",
        "%Y-%m-%d"

    ]


    for fmt in formats:

        try:

            dt = datetime.strptime(text, fmt)

            dt = dt.replace(year=now.year)

            return dt.strftime("%Y-%m-%d")

        except:

            pass


    return None


# ============================================================
# TIME PARSER
# ============================================================

def parse_time(text):

    if text is None:

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
# UTC
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
# MAIN
# ============================================================

def parse_datetime(

    text: str,

    tz: str = DEFAULT_TIMEZONE

) -> Tuple:


    text = clean(text)


    if re.match(r'\d{4}-\d{2}-\d{2}t', text):

        return parse_iso(text, tz)


    date = text

    time = None


    if " at " in text:

        date, time = text.split(" at ")


    elif " " in text:

        parts = text.split()

        date = " ".join(parts[:-1])

        time = parts[-1]


    date = parse_date(date, tz)

    time = parse_time(time)


    if not date:

        return None, None, None


    utc = to_utc(date, time, tz)


    return date, time, utc


# ============================================================
# DISPLAY
# ============================================================

def display(utc, tz=DEFAULT_TIMEZONE):

    local = datetime.fromisoformat(

        utc.replace("Z","+00:00")

    ).astimezone(pytz.timezone(tz))


    return local.strftime(

        "%B %d, %Y at %I:%M %p %Z"

    )


def normalize_to_utc(dt_str):

    return datetime.fromisoformat(
        dt_str.replace("Z", "+00:00")
    ).astimezone(timezone.utc)
