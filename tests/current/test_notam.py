"""
NOTAM Report Tests
"""

# stdlib
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

# library
import pytest
from dateutil.tz import gettz

# module
from avwx import structs
from avwx.current import notam
from avwx.static.core import IN_UNITS

# tests
from tests.util import get_data


QUALIFIERS = [
    structs.Qualifiers(
        repr="ZNY/QPIXX/I/NBO/A/000/999/4038N07346W025",
        fir="ZNY",
        subject=structs.Code("PI", "Instrument approach procedure"),
        condition=structs.Code("XX", "Unknown"),
        traffic=structs.Code("I", "IFR"),
        purpose=[
            structs.Code("N", "Immediate"),
            structs.Code("B", "Briefing"),
            structs.Code("O", "Flight Operations"),
        ],
        scope=[structs.Code("A", "Aerodrome")],
        lower=structs.Number("000", 0, "zero"),
        upper=structs.Number("999", 999, "nine nine nine"),
        coord=structs.Coord(40.38, -73.46, "4038N07346W"),
        radius=structs.Number("025", 25, "two five"),
    ),
    structs.Qualifiers(
        repr="ZJX/undefined/NBO/A/000/999/2825N08118W025",
        fir="ZJX",
        subject=None,
        condition=None,
        traffic=None,
        purpose=[
            structs.Code("N", "Immediate"),
            structs.Code("B", "Briefing"),
            structs.Code("O", "Flight Operations"),
        ],
        scope=[structs.Code("A", "Aerodrome")],
        lower=structs.Number("000", 0, "zero"),
        upper=structs.Number("999", 999, "nine nine nine"),
        coord=structs.Coord(28.25, -81.18, "2825N08118W"),
        radius=structs.Number("025", 25, "two five"),
    ),
    structs.Qualifiers(
        repr="EGTT/QWMLW/IV/BO /AW/000/001/5125N00028W002",
        fir="EGTT",
        subject=structs.Code("WM", "Missile, gun or rocket firing"),
        condition=structs.Code("LW", "Will take place"),
        traffic=structs.Code("IV", "IFR and VFR"),
        purpose=[
            structs.Code("B", "Briefing"),
            structs.Code("O", "Flight Operations"),
        ],
        scope=[
            structs.Code("A", "Aerodrome"),
            structs.Code("W", "Warning"),
        ],
        lower=structs.Number("000", 0, "zero"),
        upper=structs.Number("001", 1, "one"),
        coord=structs.Coord(51.25, -0.28, "5125N00028W"),
        radius=structs.Number("002", 2, "two"),
    ),
    structs.Qualifiers(
        repr="OIIX/QPIXX/A/000/999/",
        fir="OIIX",
        subject=structs.Code("PI", "Instrument approach procedure"),
        condition=structs.Code("XX", "Unknown"),
        traffic=None,
        purpose=[],
        scope=[
            structs.Code("A", "Aerodrome"),
        ],
        lower=structs.Number("000", 0, "zero"),
        upper=structs.Number("999", 999, "nine nine nine"),
        coord=None,
        radius=None,
    ),
]


COPIED_TAG_REPORT = """
A3475/22 NOTAMN
Q) LIMM/QFAXX/IV/NBO/A/000/999/4537N00843E005
A) LIMC B) 2205182200 C) PERM
E) REF AIP AD 2 LIMC 1-12 ITEM 20 'LOCAL TRAFFIC REGULATIONS'
BOX 2 'APRON' PARAGRAPH 2.1 'ORDERLY MOVEMENT OF AIRCRAFT ON
APRONS' INDENT 4 'SERVICES PROVIDED' POINT C) 'FOLLOW-ME ASSISTANCE
PROVIDED ON PILOT'S REQUEST AND MANDATORY IN CASE' ADD THE FOLLOWING
IN CASE:
- GENERAL AVIATION AIRCRAFT UP TO ICAO CODE B (MAXIMUM WINGSPAN 24
METERS) AND HELICOPTERS ARRIVING AND DEPARTING FROM STANDS 301 TO 320
AND FROM 330 TO 336.
ARR TAXI ROUTE: AFTER TWR INSTRUCTIONS VIA APN TAXIWAY P-K TO
INTERMEDIATE HOLDING POSITION (IHP) K9 WHERE FOLLOW-ME CAR WILL
BE WAITING.
DEP TAXI ROUTE: AFTER TWR INSTRUCTIONS AND WITH FOLLOW-ME
ASSISTANCE VIA APN TAXIWAY N-K TO IHP K8
"""


@pytest.mark.parametrize(
    "text,lat,lon",
    (
        ("5126N00036W", 51.26, -0.36),
        ("1234S14321E", -12.34, 143.21),
        ("2413N01234W", 24.13, -12.34),
    ),
)
def test_rear_coord(text: str, lat: float, lon: float):
    """Tests converting rear-loc coord string to Coord struct"""
    coord = structs.Coord(lat, lon, text)
    assert notam._rear_coord(text) == coord


def test_bad_rear_coord():
    assert notam._rear_coord("latNlongE") is None


@pytest.mark.parametrize(
    "text,number,char,rtype,replaces", (("01/113 NOTAMN", "01/113", "N", "New", None),)
)
def test_header(text: str, number: str, char: str, rtype: str, replaces: Optional[str]):
    """Tests parsing NOTAM headers"""
    ret_number, ret_type, ret_replaces = notam._header(text)
    code = structs.Code(f"NOTAM{char}", rtype)
    assert ret_number == number
    assert ret_type == code
    assert ret_replaces == replaces


@pytest.mark.parametrize("qualifier", QUALIFIERS)
def test_qualifiers(qualifier: structs.Qualifiers):
    """Tests Qualifier struct parsing"""
    units = structs.Units(**IN_UNITS)
    assert notam._qualifiers(qualifier.repr, units) == qualifier


@pytest.mark.parametrize(
    "raw,trim,tz,dt",
    (
        (
            "2110121506",
            "2110121506",
            None,
            datetime(2021, 10, 12, 15, 6, tzinfo=timezone.utc),
        ),
        (
            "2205241452EST",
            "2205241452",
            "EST",
            datetime(2022, 5, 24, 14, 52, tzinfo=gettz("EST")),
        ),
        ("PERM", "PERM", None, datetime(2100, 1, 1, tzinfo=timezone.utc)),
    ),
)
def test_make_year_timestamp(raw: str, trim: str, tz: Optional[str], dt: datetime):
    """Tests datetime conversion from year-prefixed strings"""
    timestamp = structs.Timestamp(raw, dt)
    assert notam.make_year_timestamp(trim, raw, tz) == timestamp


def test_bad_year_timestamp():
    assert notam.make_year_timestamp(" ", " ", None) is None


@pytest.mark.parametrize(
    "start,end,start_dt,end_dt",
    (
        (
            "2107221958",
            "2307221957EST",
            datetime(2021, 7, 22, 19, 58, tzinfo=gettz("EST")),
            datetime(2023, 7, 22, 19, 57, tzinfo=gettz("EST")),
        ),
        (
            "2203231000",
            "2303231300",
            datetime(2022, 3, 23, 10, 0, tzinfo=timezone.utc),
            datetime(2023, 3, 23, 13, 0, tzinfo=timezone.utc),
        ),
        (
            "2107221958EST",
            "",
            datetime(2021, 7, 22, 19, 58, tzinfo=gettz("EST")),
            None,
        ),
        (
            "",
            "2107221958",
            None,
            datetime(2021, 7, 22, 19, 58, tzinfo=timezone.utc),
        ),
        ("", "", None, None),
    ),
)
def test_parse_linked_times(
    start: str, end: str, start_dt: Optional[datetime], end_dt: Optional[datetime]
):
    """Tests parsing start and end times with shared timezone"""
    ret_start, ret_end = notam.parse_linked_times(start, end)
    start_comp = structs.Timestamp(start, start_dt) if start_dt else None
    end_comp = structs.Timestamp(end, end_dt) if end_dt else None
    assert ret_start == start_comp
    assert ret_end == end_comp


def test_copied_tag():
    """Tests an instance when the body includes a previously used tag value"""
    data = notam.Notams.from_report(COPIED_TAG_REPORT).data[0]
    assert data.body.startswith("REF AIP") is True
    assert data.end_time.repr == "PERM"
    assert isinstance(data.end_time.dt, datetime)


def test_parse():
    """Tests returned structs from the parse function"""
    report = "01/113 NOTAMN \r\nQ) ZNY/QMXLC/IV/NBO/A/000/999/4038N07346W005 \r\nA) KJFK \r\nB) 2101081328 \r\nC) 2209301100 \r\n\r\nE) TWY TB BTN TERMINAL 8 RAMP AND TWY A CLSD"
    data, _ = notam.parse(report)
    assert isinstance(data, structs.NotamData)
    assert data.raw == report


@pytest.mark.parametrize(
    "line,fixed", (("01/113 NOTAMN \r\nQ) 1234", "01/113 NOTAMN \nQ) 1234"),)
)
def test_sanitize(line: str, fixed: str):
    """Tests report sanitization"""
    assert notam.sanitize(line) == fixed


@pytest.mark.parametrize("ref,icao,_", get_data(__file__, "notam"))
def test_notam_e2e(ref: dict, icao: str, _):
    """Performs an end-to-end test of all NOTAM JSON files"""
    station = notam.Notams(icao)
    assert station.last_updated is None
    reports = [report["data"]["raw"] for report in ref["reports"]]
    assert station.parse(reports) is True
    assert isinstance(station.last_updated, datetime)
    for parsed, report in zip(station.data, ref["reports"]):
        assert asdict(parsed) == report["data"]
