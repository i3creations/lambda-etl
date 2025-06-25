#!/usr/bin/env python3
import pytz
import time
from pandas import Timestamp
from datetime import datetime, timedelta, timezone
from typing import Union
from utils.Singleton import Singleton

#
# Convert datetime and Timestamp from UTC to Local Time if and only if the
# input date/time do not have a UTC offset or have a UTC offset of Zero
#
# Convert a date/time string to UTC if and only if the input date/time string
# has a time zone offset, otherwise None is returned.
#
class _CvtDateTime_(Singleton):
    def __init__(self) -> None:
        #
        # Get Local time zone offset indicating a positive or negative time
        # difference from UTC/GMT of the form +HHMM or -HHMM, where H
        # represents decimal hour digits and M represents decimal minute
        # digits [-23:59, +23:59]
        self._local_tzoffset = int(time.strftime("%z", time.localtime()))/100
        self._local_tzdelta = timedelta(hours=self._local_tzoffset)

    @property
    def local_tzdelta(self):
        return self._local_tzdelta

    # Convert an input date time in UTC to local time.
    #
    def utc2local(self, utc_dt: Union[datetime, Timestamp]
                  ) -> Union[datetime, Timestamp]:
        # N.B.    utcoffset() function returns a timedelta object
        #  A timedelta object is considered to be true if and only if it isn’t
        #  equal to timedelta(0)
        #      covers both date time formats with or without tzinfo
        if utc_dt.utcoffset():
            off = utc_dt.utcoffset()
            raise Exception(f"Input time is not UTC!  tzoff= {off}")
        # N.B.
        # Input times with no speified UTC offset specification are considered
        # by this code to be UTC times.    This is the case with dataset time
        # values acquired from ncdc.noaa.gov.
        #
        local_dt = utc_dt + self._local_tzdelta
        local_dt = local_dt.replace(tzinfo=timezone(self._local_tzdelta))
        return local_dt

    # Convert a date/time string in isoformat to a datetime object with
    # timezone infomration.
    #   None is returned if input string does not include timezone information
    #
    # When None is returned, the caller must decide on what the appropriate
    # timezone is for the time string passed to str2utc.
    #
    def str2utc(self, dtstr: str, *, assumeutc=False) -> Union[datetime, None]:
        ds = datetime.fromisoformat(dtstr)
        tzoff = ds.strftime("%z")
        if tzoff:
            tzoffset = int(tzoff)/100  # Float HH.MM
            tzdelta = timedelta(hours=tzoffset)
            # Set time zone info to UTC
            utc = (ds - tzdelta).replace(tzinfo=timezone.utc)
            return utc
        elif assumeutc:
            utc = ds.replace(tzinfo=timezone.utc)
            return utc
        return None


# Instantiated Date Time Conversion Object
Cvdt = _CvtDateTime_()

if __name__ == "__main__":
    # Example usage, local time conversion not validated from test perspective
    utc_now = datetime.now(tz=pytz.utc).replace(microsecond=0)
    ldt = Cvdt.utc2local(utc_now)
    print(f"utc2local({utc_now})\nu2lout {ldt}")

    ins = '2018-01-01T00:36:00'
    ds = datetime.fromisoformat(ins)
    # FIXME..    Hard coded test output value only valid in tzoff=-6
    exo = datetime.fromisoformat('2017-12-31 18:36:00-06:00')
    ldt = Cvdt.utc2local(ds)
    print(f"\nutc2local({ds})\nu2lout {ldt}")
    if ldt != exo:
        print(f"C0 Failed expected local time = {exo}")

    ins = '2023-06-29 17:45:00-06:00'
    ds = datetime.fromisoformat(ins)
    ex = False
    try:
        ldt = Cvdt.utc2local(ds)
    except Exception as e:
        ex = True
        print(f"\nutc2local({ds})\nutc2local Exception! '{e}'")
    if not ex:
        print(f"C1 Failed to Convert {ins} correctly")

    ins = '2023-06-29 18:00:00-06:00'
    exo = datetime.fromisoformat(ins)
    s_utc = Cvdt.str2utc(ins)
    print(f"\nstr2utc({ins})\nreturn {s_utc}")
    if s_utc != exo:
        print(f"C2 Failed str2utc input {s_utc} != {exo}")

    ins = '2023-06-29 18:00:00'
    exo = datetime.fromisoformat(ins)
    exo = exo + Cvdt.local_tzdelta
    s_utc = Cvdt.str2utc(ins)
    print(f"\nstr2utc({ins})\nreturn {s_utc}")
    if s_utc is not None:
        print(f"C3 Failed str2utc input {s_utc} != None")

    ins = '2023-06-29 18:00:00'
    exo = datetime.fromisoformat('2023-06-29 18:00:00+00:00')
    s_utc = Cvdt.str2utc(ins, assumeutc=True)
    print(f"\nstr2utc({ins})\nreturn {s_utc}")
    if s_utc != exo:
        print(f"C4 Failed str2utc input {s_utc} != {exo}")
