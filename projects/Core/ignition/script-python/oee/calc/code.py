"""
OEE Calculation Library
Hitachi Energy - Jefferson City Transformer Facility (WOCL lines)
Ignition Project Library package:  oee.calc

Implements the "OEE Calculation Methodology" v1.2 (08-Dec-2025).
This module is PURE: it contains no database access and no system.* calls,
so every number it produces is deterministic and auditable. All data access
lives in oee.data; this module only does math.

    OEE = Availability x Performance x Quality

    Availability = Operating Time / Planned Production Time
        Planned Production Time = Shift Duration - Planned Downtime
        Operating Time          = Planned Production Time - Unplanned Downtime

    Performance  = Earned Minutes / Operating Time
        Earned Minutes = SUM( Planned Cycle Time(coil) x Completion%(coil) )

    Quality      = 1.0   (Phase 1 assumption - methodology section 9, item 1)

Jython 2.7 compatible. `from __future__ import division` is REQUIRED so that
integer / integer does not silently truncate (a classic source of "false data"
in Ignition scripting).
"""
from __future__ import division

# Default Quality factor for Phase 1. Quality tracking is a future phase.
DEFAULT_QUALITY = 1.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_float(value, default=0.0):
    """Coerce a value to float, returning `default` for None or bad input."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value, low, high):
    """Constrain a numeric value to the inclusive range [low, high]."""
    value = _to_float(value)
    if value < low:
        return low
    if value > high:
        return high
    return value


def _safe_div(numerator, denominator):
    """
    Float division that returns 0.0 when the denominator is 0.

    An idle shift can legitimately produce a zero Planned Production Time or
    zero Operating Time; returning 0.0 (rather than raising) keeps the
    dashboard rendering instead of erroring, while never inventing a value.
    """
    numerator = _to_float(numerator)
    denominator = _to_float(denominator)
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def _round2(value):
    """Round to 2 decimals for display (calculations keep full precision)."""
    return round(_to_float(value), 2)


def _sum_minutes(items):
    """Sum the 'minutes' field across a list of {'minutes': ...} dicts."""
    total = 0.0
    for item in (items or []):
        total += _to_float(item.get("minutes"))
    return total


# ---------------------------------------------------------------------------
# Completion helpers
# ---------------------------------------------------------------------------

def completion_from_turns(actual_turns, total_turns):
    """
    Derive a coil's completion fraction (0.0 .. 1.0) from turn counts.

    Per methodology section 9 item 5, partial completion is determined by the
    percentage of the coil completed (turn count vs total turns, or operator
    input). Result is clamped to [0, 1] so a sensor over-count cannot push
    Performance above 100%.

        actual_turns : turns wound so far (PLC ActualTurnCount)
        total_turns  : total turns for the coil (ECS TotalTurnCount)
    """
    total = _to_float(total_turns)
    if total <= 0.0:
        return 0.0
    return _clamp(_to_float(actual_turns) / total, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

def planned_production_time(shift_duration_min, planned_downtime_items):
    """
    Planned Production Time = Shift Duration - Total Planned Downtime.

        shift_duration_min     : total scheduled shift minutes (e.g. 480)
        planned_downtime_items : list of {'name': str, 'minutes': number}
                                 (lunch, breaks, shift buffers, PM, ...)

    Returns a value floored at 0 (planned downtime cannot exceed the shift).
    """
    shift = _to_float(shift_duration_min)
    planned_dt = _sum_minutes(planned_downtime_items)
    ppt = shift - planned_dt
    if ppt < 0.0:
        return 0.0
    return ppt


def operating_time(ppt_min, unplanned_downtime_items):
    """
    Operating Time = Planned Production Time - Unplanned Downtime.

    Micro-stoppages (< 10 min) are already absorbed into Operating Time per
    section 8, so `unplanned_downtime_items` should contain ONLY the qualifying
    unplanned events (machine faults/alarms and >10 min stops). Floored at 0.
    """
    ppt = _to_float(ppt_min)
    unplanned = _sum_minutes(unplanned_downtime_items)
    op = ppt - unplanned
    if op < 0.0:
        return 0.0
    return op


def compute_availability(shift_duration_min, planned_downtime_items,
                         unplanned_downtime_items):
    """
    Full Availability calculation. Returns a dict with every intermediate
    value so the dashboard cards can bind directly to the breakdown.

        availability        : fraction 0.0 .. 1.0
        availability_pct     : percentage 0 .. 100 (rounded to 2dp)
    """
    shift = _to_float(shift_duration_min)
    planned_dt = _sum_minutes(planned_downtime_items)
    unplanned_dt = _sum_minutes(unplanned_downtime_items)

    ppt = planned_production_time(shift, planned_downtime_items)
    op = operating_time(ppt, unplanned_downtime_items)
    availability = _safe_div(op, ppt)

    return {
        "shift_duration_min": shift,
        "planned_downtime_min": planned_dt,
        "planned_production_time_min": ppt,
        "unplanned_downtime_min": unplanned_dt,
        "operating_time_min": op,
        "availability": availability,
        "availability_pct": _round2(availability * 100.0),
    }


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------

def earned_minutes(coils):
    """
    Earned Minutes = SUM( planned_ct_min x completion_pct ) across coils.

        coils : list of dicts, each with
                  'planned_ct_min' : planned cycle time for the coil (minutes)
                  'completion_pct' : fraction 0.0 .. 1.0 of the coil completed

    'completion_pct' is clamped to [0, 1] defensively.
    """
    total = 0.0
    for coil in (coils or []):
        planned_ct = _to_float(coil.get("planned_ct_min"))
        completion = _clamp(coil.get("completion_pct"), 0.0, 1.0)
        total += planned_ct * completion
    return total


def compute_performance(operating_time_min, coils):
    """
    Performance = Earned Minutes / Operating Time, capped at 100%.

    Operating Time is the SAME value used as the Availability numerator
    (methodology section 6.3 uses 355 min for both), so callers must pass the
    Operating Time produced by compute_availability, not the raw shift length.

    Performance is capped at 1.0: standard OEE never reports performance above
    100%. Values above 100% mean earned standard-time exceeded the operating
    time - typically a coil that spans shifts being credited in full to the
    shift it finishes in, or an ideal cycle time set generously. (The original
    dashboard capped the same way: `val if val <= 100 else 100`.)
    """
    op = _to_float(operating_time_min)
    earned = earned_minutes(coils)
    performance = _safe_div(earned, op)
    if performance > 1.0:
        performance = 1.0

    return {
        "operating_time_min": op,
        "earned_minutes": earned,
        "coil_count": len(coils or []),
        "performance": performance,
        "performance_pct": _round2(performance * 100.0),
    }


# ---------------------------------------------------------------------------
# OEE (top-level)
# ---------------------------------------------------------------------------

def compute_oee(shift_duration_min, planned_downtime_items,
                unplanned_downtime_items, coils, quality=DEFAULT_QUALITY):
    """
    End-to-end OEE for one machine / shift / day.

    Inputs
    ------
    shift_duration_min       : scheduled shift minutes (e.g. 480, or summed
                               across shifts for a daily roll-up)
    planned_downtime_items   : list of {'name','minutes'} planned stops
    unplanned_downtime_items  : list of {'name','minutes'} qualifying unplanned
                               stops (faults/alarms + >10 min stops only)
    coils                    : list of {'planned_ct_min','completion_pct', ...}
    quality                  : fraction 0.0 .. 1.0 (defaults to 1.0, Phase 1)

    Returns
    -------
    A single dict containing the Availability and Performance breakdowns plus
    the combined OEE, ready to bind onto Perspective components.
    """
    avail = compute_availability(
        shift_duration_min, planned_downtime_items, unplanned_downtime_items)
    perf = compute_performance(avail["operating_time_min"], coils)

    quality = _clamp(quality, 0.0, 1.0)
    oee = avail["availability"] * perf["performance"] * quality

    result = {
        # Availability block
        "shift_duration_min": avail["shift_duration_min"],
        "planned_downtime_min": avail["planned_downtime_min"],
        "planned_production_time_min": avail["planned_production_time_min"],
        "unplanned_downtime_min": avail["unplanned_downtime_min"],
        "operating_time_min": avail["operating_time_min"],
        "availability": avail["availability"],
        "availability_pct": avail["availability_pct"],
        # Performance block
        "earned_minutes": perf["earned_minutes"],
        "coil_count": perf["coil_count"],
        "performance": perf["performance"],
        "performance_pct": perf["performance_pct"],
        # Quality block
        "quality": quality,
        "quality_pct": _round2(quality * 100.0),
        # OEE
        "oee": oee,
        "oee_pct": _round2(oee * 100.0),
    }
    return result


# ---------------------------------------------------------------------------
# Display helpers (optional convenience for the views)
# ---------------------------------------------------------------------------

def minutes_to_hhmmss(minutes):
    """
    Format a minute count as HH:MM:SS (matches the dashboard 'Production Time'
    and 'Total DT' cards, e.g. 390 -> '06:30:00').
    """
    total_seconds = int(round(_to_float(minutes) * 60.0))
    if total_seconds < 0:
        total_seconds = 0
    hours = total_seconds // 3600
    rem = total_seconds % 3600
    mins = rem // 60
    secs = rem % 60
    return "%02d:%02d:%02d" % (hours, mins, secs)
    
    
#====================================================================================NEW OEE SCREEN SCRIPTS from here====================================================

"""
oee.calc -- Pure OEE calculation engine.

Hitachi Energy Transformer, Jefferson City - WOCL Coil Winding
Implements "OEE Calculation Methodology" v1.2 (2025-12-08) with the
data-mapping decisions confirmed by the client on 2026-07-02:

  * Ideal Cycle Time  = lspec_metadata.hv_winding_time  (HOURS per coil)
  * Actual coil time  = work_orders.actual_end - work_orders.actual_start
  * Completion %      : op_status = 16  -> 100 %
                        otherwise      -> elapsed time / ideal time (capped at 100 %)
                        (wo_event_history.wip is intentionally NOT used)
  * Planned downtime  = tbl_DowntimeLog rows with CategoryID = 2
  * Unplanned downtime= tbl_DowntimeLog rows with CategoryID = 1
  * Quality           = 100 % (future phase)

This module is PURE PYTHON (Jython 2.7 compatible). It never touches the
database or Ignition system functions, so every formula here is unit-testable
via oee.test.runAll().

DESIGN RULE: no invented numbers. Every function either computes from its
inputs or returns an explicit zero/empty default with a reason.
"""

# ---------------------------------------------------------------------------
# Configuration constants (single source of truth - change here only)
# ---------------------------------------------------------------------------

# tbl_DowntimeCategory: 1 = Manual, 2 = System.
# Client decision 2026-07-02: CategoryID 2 counts as PLANNED downtime,
# CategoryID 1 counts as UNPLANNED downtime.
PLANNED_CATEGORY_ID = 2
UNPLANNED_CATEGORY_ID = 1

# work_orders.op_status value that means the coil is 100% complete.
COMPLETE_OP_STATUS = 16

# Quality is fixed at 100% until the quality phase is implemented
# (OEE Calculation Methodology v1.2, section 2 / assumption #1).
QUALITY_PCT = 100.0

MS_PER_MIN = 60000.0
MIN_PER_DAY = 1440.0


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

try:
    _NUMERIC_TYPES = (int, long, float)  # Jython 2.7  # noqa: F821
except NameError:
    _NUMERIC_TYPES = (int, float)        # Python 3 (local testing)


def toMillis(t):
    """Convert java.util.Date, python datetime, or number to epoch millis.
    Returns None for None."""
    if t is None:
        return None
    if isinstance(t, _NUMERIC_TYPES):
        return float(t)
    # java.util.Date / java.sql.Timestamp expose getTime()
    getTime = getattr(t, 'getTime', None)
    if getTime is not None:
        return float(getTime())
    # python datetime
    import time as _time
    try:
        return float(_time.mktime(t.timetuple()) * 1000.0 + t.microsecond / 1000.0)
    except AttributeError:
        raise TypeError('Unsupported time value: %r' % (t,))


def safeDiv(numerator, denominator, default=0.0):
    """Division that never raises and never invents a value on bad input."""
    try:
        n = float(numerator)
        d = float(denominator)
    except (TypeError, ValueError):
        return default
    if d == 0.0:
        return default
    return n / d


def clamp(value, lo, hi):
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def minutesToHMS(minutes):
    """396.5 -> '06:36:30'. Negative/None -> '00:00:00'."""
    try:
        totalSeconds = int(round(float(minutes) * 60.0))
    except (TypeError, ValueError):
        totalSeconds = 0
    if totalSeconds < 0:
        totalSeconds = 0
    h = totalSeconds // 3600
    m = (totalSeconds % 3600) // 60
    s = totalSeconds % 60
    return '%02d:%02d:%02d' % (h, m, s)


# ---------------------------------------------------------------------------
# Shift schedule (read from tbl_Shift - never hardcoded)
# ---------------------------------------------------------------------------

def _parseTimeOfDayToMinutes(value):
    """Accepts 'HH:MM:SS(.fffffff)' strings or java.sql.Time / python time
    objects and returns minutes past midnight (float)."""
    if value is None:
        return None
    # objects with getHours (java.sql.Time) -- deprecated API but present
    if hasattr(value, 'getHours') and hasattr(value, 'getMinutes'):
        try:
            return value.getHours() * 60.0 + value.getMinutes() + getattr(value, 'getSeconds', lambda: 0)() / 60.0
        except Exception:
            pass
    if hasattr(value, 'hour') and hasattr(value, 'minute'):
        return value.hour * 60.0 + value.minute + getattr(value, 'second', 0) / 60.0
    s = str(value).strip()
    parts = s.split(':')
    if len(parts) < 2:
        raise ValueError('Cannot parse shift time: %r' % (value,))
    h = int(parts[0])
    m = int(parts[1])
    sec = 0.0
    if len(parts) > 2:
        sec = float(parts[2].split('.')[0] or 0)
    return h * 60.0 + m + sec / 60.0


def shiftDurationMinutes(startTime, endTime):
    """Duration of one shift, handling overnight shifts
    (e.g. Night 23:30 -> 07:30 = 480 min)."""
    start = _parseTimeOfDayToMinutes(startTime)
    end = _parseTimeOfDayToMinutes(endTime)
    if start is None or end is None:
        return 0.0
    dur = end - start
    if dur <= 0:
        dur += MIN_PER_DAY
    return dur


def dailyShiftMinutes(shiftRows):
    """Total scheduled minutes per day from tbl_Shift rows.
    shiftRows: list of dicts with 'StartTime' and 'EndTime'.
    For the current 3x8h pattern this returns 1440."""
    total = 0.0
    for row in shiftRows or []:
        total += shiftDurationMinutes(row.get('StartTime'), row.get('EndTime'))
    return total


def totalScheduledMinutes(startMs, endMs, nowMs, dailyMinutes):
    """Total Time for the selected range: the portion of the calendar range
    that is covered by scheduled shifts, clamped so that we never count
    future time (a range ending tomorrow only counts up to 'now').

    dailyMinutes comes from dailyShiftMinutes(); with 3 x 8h shifts the
    coverage factor is 1440/1440 = 1.0 (round-the-clock operation).
    """
    if startMs is None or endMs is None:
        return 0.0
    effectiveEnd = endMs
    if nowMs is not None and nowMs < effectiveEnd:
        effectiveEnd = nowMs
    rangeMinutes = (effectiveEnd - startMs) / MS_PER_MIN
    if rangeMinutes <= 0:
        return 0.0
    coverage = clamp(safeDiv(dailyMinutes, MIN_PER_DAY, 0.0), 0.0, 1.0)
    return rangeMinutes * coverage


def shiftBoundsMinutes(shiftRow):
    """(startMin, endMin) past midnight for one tbl_Shift row, or None."""
    if shiftRow is None:
        return None
    try:
        s = _parseTimeOfDayToMinutes(shiftRow.get('StartTime'))
        e = _parseTimeOfDayToMinutes(shiftRow.get('EndTime'))
    except (ValueError, AttributeError):
        return None
    if s is None or e is None:
        return None
    return (s, e)


def timeOfDayInShift(todMinutes, shiftStartMin, shiftEndMin):
    """True when a time-of-day (minutes past midnight) falls inside the
    shift window. Overnight shifts (end <= start, e.g. C 23:30-07:30)
    wrap across midnight."""
    if todMinutes is None or shiftStartMin is None or shiftEndMin is None:
        return False
    if shiftEndMin <= shiftStartMin:                       # overnight
        return todMinutes >= shiftStartMin or todMinutes < shiftEndMin
    return shiftStartMin <= todMinutes < shiftEndMin


def overlapMinutes(aStartMs, aEndMs, bStartMs, bEndMs):
    """Minutes of overlap between two [start, end) millisecond intervals.
    This is the SAME clipping rule the downtime named queries apply in SQL:
    max(starts) .. min(ends), never negative."""
    if aStartMs is None or aEndMs is None or bStartMs is None or bEndMs is None:
        return 0.0
    s = aStartMs if aStartMs > bStartMs else bStartMs
    e = aEndMs if aEndMs < bEndMs else bEndMs
    if e <= s:
        return 0.0
    return (e - s) / MS_PER_MIN


def scheduledShiftMinutes(dayMidnightsMs, startMs, endMs, nowMs, shiftRows, shiftId):
    """Exact scheduled minutes inside [startMs, endMs) for the selected
    shift (shiftId 0/None = all active shifts), clamped to 'now'.

    dayMidnightsMs must cover every day the range touches INCLUDING the day
    BEFORE the range start, so an overnight shift that began the previous
    evening still contributes its early-morning minutes.
    """
    if startMs is None or endMs is None:
        return 0.0
    effEnd = endMs
    if nowMs is not None and nowMs < effEnd:
        effEnd = nowMs
    if effEnd <= startMs:
        return 0.0
    total = 0.0
    for row in shiftRows or []:
        if shiftId and row.get('ShiftID') != shiftId:
            continue
        bounds = shiftBoundsMinutes(row)
        if bounds is None:
            continue
        sMin, eMin = bounds
        winLen = eMin - sMin
        if winLen <= 0:
            winLen += MIN_PER_DAY                          # overnight
        for dm in dayMidnightsMs or []:
            ws = dm + sMin * MS_PER_MIN
            we = ws + winLen * MS_PER_MIN
            total += overlapMinutes(ws, we, startMs, effEnd)
    return total


# ---------------------------------------------------------------------------
# Downtime classification
# ---------------------------------------------------------------------------

def splitDowntime(downtimeRows):
    """Split tbl_DowntimeLog rows into planned / unplanned minutes.

    downtimeRows: list of dicts with 'CategoryID' and 'ClippedMinutes'
    (portion inside the selected range, from the named query) or, as a
    fallback, raw 'DurationMinutes'. ClippedMinutes always wins when
    present - boundary rule of 2026-07-02.
    Returns dict:
      plannedMinutes, unplannedMinutes, otherMinutes (unknown category),
      eventCountPlanned, eventCountUnplanned
    """
    planned = 0.0
    unplanned = 0.0
    other = 0.0
    nPlanned = 0
    nUnplanned = 0
    for row in downtimeRows or []:
        raw = row.get('ClippedMinutes')
        if raw is None:
            raw = row.get('DurationMinutes')
        try:
            dur = float(raw or 0)
        except (TypeError, ValueError):
            dur = 0.0
        if dur < 0:
            dur = 0.0
        cat = row.get('CategoryID')
        if cat == PLANNED_CATEGORY_ID:
            planned += dur
            nPlanned += 1
        elif cat == UNPLANNED_CATEGORY_ID:
            unplanned += dur
            nUnplanned += 1
        else:
            other += dur
    return {
        'plannedMinutes': planned,
        'unplannedMinutes': unplanned,
        'otherMinutes': other,
        'eventCountPlanned': nPlanned,
        'eventCountUnplanned': nUnplanned,
    }


# ---------------------------------------------------------------------------
# Coil completion & earned time
# ---------------------------------------------------------------------------

def completionPct(opStatus, actualStartMs, actualEndMs, idealMinutes, nowMs):
    """Completion fraction (0.0 - 1.0) for one coil / work order.

    Client rule (2026-07-02):
      op_status == 16                    -> 1.0 (complete)
      otherwise, if the coil was started -> elapsed / ideal, capped at 1.0
      never started (no actual_start)    -> 0.0
    """
    if opStatus == COMPLETE_OP_STATUS:
        return 1.0
    if actualStartMs is None:
        return 0.0
    endMs = actualEndMs if actualEndMs is not None else nowMs
    if endMs is None or idealMinutes is None or idealMinutes <= 0:
        return 0.0
    elapsedMin = (endMs - actualStartMs) / MS_PER_MIN
    if elapsedMin <= 0:
        return 0.0
    return clamp(safeDiv(elapsedMin, idealMinutes, 0.0), 0.0, 1.0)



def shiftWindowOverlapMinutes(startMs, endMs, rangeStartMs, rangeEndMs,
                              dayMidnightsMs, shiftBounds):
    """Minutes of the interval [startMs, endMs] that fall inside BOTH the
    selected range AND the selected shift's daily windows.

    shiftBounds: [(startMinOfDay, endMinOfDay)] from tbl_Shift, or None
    for All Shifts (plain range clipping). Overnight windows
    (end <= start, e.g. Shift C 23:30-07:30) extend into the next day.

    Added for the boundary rule 2026-07-04: earned coil credit must be
    bounded by the same shift windows as operating time, otherwise a
    coil whose work runs past the shift end inflates Performance beyond
    100%% for that shift."""
    if startMs is None or endMs is None:
        return 0.0
    s = max(startMs, rangeStartMs)
    e = min(endMs, rangeEndMs)
    if e <= s:
        return 0.0
    if shiftBounds is None:
        return (e - s) / MS_PER_MIN
    total = 0.0
    for mid in dayMidnightsMs or []:
        for b in shiftBounds:
            wS = mid + b[0] * 60000.0
            wE = mid + b[1] * 60000.0
            if b[1] <= b[0]:
                wE += 86400000.0          # crosses midnight
            oS = s if s > wS else wS
            oE = e if e < wE else wE
            if oE > oS:
                total += (oE - oS) / MS_PER_MIN
    return total

def coilMetrics(workOrderRows, nowMs):
    """Aggregate coil-level production data for the selected range.

    workOrderRows: dicts with keys
      serial_number, op_status, actual_start (ms or Date), actual_end,
      hv_winding_time (HOURS, from lspec_metadata; may be None)
      and, when supplied by oee/WorkOrders (boundary rule 2026-07-03):
      ActualMinutes  - the coil's full life in minutes
      ClippedMinutes - the portion of that life inside the selected range

    Returns dict:
      earnedMinutes      Sum(ideal CT x completion x inRangeRatio) - the
                         "Earned Hours" numerator of the Performance
                         formula, in minutes. inRangeRatio =
                         ClippedMinutes / ActualMinutes attributes only
                         the in-range share of a boundary-straddling coil
                         to this range (1.0 when the SQL fields are
                         absent, preserving the pre-clipping behaviour).
      coilsStarted / coilsCompleted / coilsInProgress
      skippedNoIdeal     serial numbers skipped because lspec had no
                         hv_winding_time (reported, never guessed)
      cycles             per-coil list for the Ideal-vs-Actual chart:
                         {serial, idealMin, actualMin, completionPct, status}
    """
    earned = 0.0
    started = 0
    completed = 0
    inProgress = 0
    skipped = []
    cycles = []

    for row in workOrderRows or []:
        serial = row.get('serial_number')
        opStatus = row.get('op_status')
        startMs = toMillis(row.get('actual_start'))
        endMs = toMillis(row.get('actual_end'))
        idealHours = row.get('hv_winding_time')
        idealMin = None
        if idealHours is not None:
            try:
                idealMin = float(idealHours) * 60.0
            except (TypeError, ValueError):
                idealMin = None

        if startMs is not None:
            started += 1
        isComplete = (opStatus == COMPLETE_OP_STATUS)
        if isComplete:
            completed += 1
        elif startMs is not None and endMs is None:
            inProgress += 1

        if idealMin is None or idealMin <= 0:
            skipped.append(serial)
            continue

        pct = completionPct(opStatus, startMs, endMs, idealMin, nowMs)

        # Boundary rule 2026-07-03: credit this range only with the share
        # of the coil's life that fell inside it. Ratio defaults to 1.0
        # when the query did not supply the clipped fields.
        ratio = 1.0
        clippedMin = row.get('ClippedMinutes')
        fullMin = row.get('ActualMinutes')
        if clippedMin is not None and fullMin is not None:
            try:
                fullMin = float(fullMin)
                clippedMin = float(clippedMin)
                if fullMin > 0:
                    ratio = clamp(safeDiv(clippedMin, fullMin, 1.0), 0.0, 1.0)
            except (TypeError, ValueError):
                ratio = 1.0

        earned += idealMin * pct * ratio

        actualMin = None
        effEnd = endMs if endMs is not None else nowMs
        if startMs is not None and effEnd is not None and effEnd > startMs:
            actualMin = (effEnd - startMs) / MS_PER_MIN

        chartClipped = None
        try:
            if row.get('ClippedMinutes') is not None:
                chartClipped = float(row.get('ClippedMinutes'))
        except (TypeError, ValueError):
            chartClipped = None

        cycles.append({
            'serial': serial,
            'idealMin': round(idealMin, 2),
            'actualMin': round(actualMin, 2) if actualMin is not None else None,
            'clippedMin': round(chartClipped, 2) if chartClipped is not None else None,
            'completionPct': round(pct * 100.0, 1),
            'status': 'Completed' if isComplete else ('In Progress' if endMs is None and startMs is not None else 'Stopped'),
        })

    return {
        'earnedMinutes': earned,
        'coilsStarted': started,
        'coilsCompleted': completed,
        'coilsInProgress': inProgress,
        'skippedNoIdeal': skipped,
        'cycles': cycles,
    }


# ---------------------------------------------------------------------------
# The OEE formulas (Methodology v1.2, sections 5-7)
# ---------------------------------------------------------------------------

def computeKPIs(totalMinutes, plannedDtMinutes, unplannedDtMinutes, earnedMinutes):
    """Master OEE computation.

      Planned Production Time = Total Time      - Planned Downtime
      Operating Time          = Planned Prod.   - Unplanned Downtime
      Availability            = Operating / Planned Production Time
      Performance             = Earned / Operating
      Quality                 = 100 % (fixed, future phase)
      OEE                     = A x P x Q

    All percentages are 0-100 floats rounded to 2 decimals.
    Any division whose denominator is 0 yields 0 - never NaN, never a guess.
    """
    total = max(0.0, float(totalMinutes or 0))
    planned = clamp(float(plannedDtMinutes or 0), 0.0, total)
    ppt = total - planned
    unplanned = clamp(float(unplannedDtMinutes or 0), 0.0, ppt)
    operating = ppt - unplanned
    earned = max(0.0, float(earnedMinutes or 0))

    availability = safeDiv(operating, ppt) * 100.0
    performance = safeDiv(earned, operating) * 100.0
    # Performance can mathematically exceed 100% if coils run faster than
    # ideal; report the true value but cap OEE inputs at 100 for the index.
    perfForOee = clamp(performance, 0.0, 100.0)
    quality = QUALITY_PCT
    oee = (availability / 100.0) * (perfForOee / 100.0) * (quality / 100.0) * 100.0

    return {
        'totalMinutes': round(total, 2),
        'plannedDtMinutes': round(planned, 2),
        'plannedProductionMinutes': round(ppt, 2),
        'unplannedDtMinutes': round(unplanned, 2),
        'operatingMinutes': round(operating, 2),
        'earnedMinutes': round(earned, 2),
        'availability': round(availability, 2),
        'performance': round(performance, 2),
        'quality': round(quality, 2),
        'oee': round(oee, 2),
    }