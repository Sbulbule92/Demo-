"""
OEE Data Access Layer
Ignition Project Library package:  oee.data

Bridges the database (via Named Queries) and the pure calculation engine in
oee.calc. Nothing here invents values: every number traces back to a query
result, and the few interpretation rules (planned/unplanned split, hv winding
hours -> minutes, wip -> completion fraction) are isolated and commented so
they can be audited or changed in one place.

Jython 2.7 (Ignition gateway/Perspective scripting).
"""
from __future__ import division

import system
import oee.calc as calc

# Named Query paths (relative to the project's Named Query root)
NQ_SHIFT_WINDOW = "oee/ShiftWindow"
NQ_DOWNTIME = "oee/Downtime"
NQ_DOWNTIME_PARETO = "oee/DowntimePareto"
NQ_COILS = "oee/Coils"
NQ_CYCLE_COMPARISON = "oee/CycleComparison"
NQ_PROD_STATUS = "oee/ProdStatus"
NQ_MACHINES = "oee/Machines"
NQ_LINES = "oee/Lines"

# --- Planned / Unplanned downtime model (matches existing AllDowntime logic) -
# Planned downtime is a fixed allowance per shift: Break up to 60 min and Lunch
# up to 30 min = 90 min total. Anything beyond those allowances, plus every
# other reason, is UNPLANNED. Classification is by ReasonID (the DB CategoryID
# for Break/Lunch is currently wrong, so it is not used).
BREAK_REASON_ID = 8       # tbl_DowntimeReason: "Break"
LUNCH_REASON_ID = 9       # tbl_DowntimeReason: "Lunch"
BREAK_ALLOWANCE_MIN = 60  # break minutes within this are planned
LUNCH_ALLOWANCE_MIN = 30  # lunch minutes within this are planned
PLANNED_MINUTES_PER_SHIFT = 90  # = BREAK_ALLOWANCE + LUNCH_ALLOWANCE


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _rows(named_query, params):
    """Run a named query and return a PyDataSet (empty-safe)."""
    ds = system.db.runNamedQuery(named_query, params)
    return system.dataset.toPyDataSet(ds)


def _f(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Shift window resolution
# ---------------------------------------------------------------------------

def resolve_shift_window(shift_date, shift_id):
    """
    Resolve a calendar date + shift id into a concrete window.

    Returns a dict {shift_id, shift_name, start, end, duration_min} or None if
    the shift id is unknown. duration_min is derived from the actual start/end
    so the Night shift (which crosses midnight) yields the correct 480 min.
    """
    rows = _rows(NQ_SHIFT_WINDOW, {"shiftDate": shift_date, "shiftId": shift_id})
    if len(rows) == 0:
        return None
    row = rows[0]
    start = row["shift_start"]
    end = row["shift_end"]
    return {
        "shift_id": row["ShiftID"],
        "shift_name": row["shift_name"],
        "start": start,
        "end": end,
        "duration_min": system.date.minutesBetween(start, end),
    }


# Shift ids that make up the "All Shifts" selection.
ALL_SHIFT_IDS = (1, 2, 3)


def _shift_ids_for_selection(shift_selection):
    """
    Normalise a shift selection into a tuple of shift ids.

        "ALL" / None / "" -> (1, 2, 3)
        1 / "1"           -> (1,)
    """
    if shift_selection is None:
        return ALL_SHIFT_IDS
    text = str(shift_selection).strip().upper()
    if text == "" or text == "ALL":
        return ALL_SHIFT_IDS
    return (int(text),)


def resolve_windows(start_date, end_date, shift_selection="ALL"):
    """
    Build the list of concrete shift windows covered by a date RANGE and a
    shift selection. Each calendar day in [start_date, end_date] contributes
    one window per selected shift.

        start_date / end_date : dates (inclusive). Pass the same value twice
                                for a single day.
        shift_selection       : 1, 2, 3, or "ALL"

    Returns a list of window dicts (see resolve_shift_window).
    """
    shift_ids = _shift_ids_for_selection(shift_selection)
    windows = []
    day = system.date.midnight(start_date)
    last = system.date.midnight(end_date)
    # Guard against a reversed range.
    if system.date.isAfter(day, last):
        day, last = last, day
    while not system.date.isAfter(day, last):
        for sid in shift_ids:
            w = resolve_shift_window(day, sid)
            if w is not None:
                windows.append(w)
        day = system.date.addDays(day, 1)
    return windows


# ---------------------------------------------------------------------------
# Build calc-engine inputs from the database
# ---------------------------------------------------------------------------

def get_downtime_inputs(machine_id, start, end, fallback_end):
    """
    Return (planned_items, unplanned_items, raw_rows) for a window.

    Implements the existing dashboard's rule:
      * Planned = fixed PLANNED_MINUTES_PER_SHIFT (90 = 60 break + 30 lunch).
      * Unplanned = every reason except Break(8)/Lunch(9) counted in full,
        PLUS Break minutes over 60 and Lunch minutes over 30.
    `fallback_end` lets the query cap a never-closed downtime at the window end
    (or "now" for a live shift) so an open stop is not reported as 0 minutes.
    raw_rows feeds the downtime detail table (Break/Lunch tagged "Planned").
    """
    rows = _rows(NQ_DOWNTIME,
                 {"machineId": machine_id, "startTime": start, "endTime": end,
                  "fallbackEnd": fallback_end})
    unplanned = []
    raw = []
    break_total = 0.0
    lunch_total = 0.0

    for r in rows:
        rid = r["reason_id"]
        minutes = _f(r["duration_min"])
        if rid == BREAK_REASON_ID:
            break_total += minutes
            is_planned = 1
        elif rid == LUNCH_REASON_ID:
            lunch_total += minutes
            is_planned = 1
        else:
            unplanned.append({"name": r["reason"], "minutes": minutes})
            is_planned = 0
        raw.append({
            "id": r["id"], "start_time": r["start_time"], "end_time": r["end_time"],
            "duration_min": minutes, "reason": r["reason"],
            "remarks": r["remarks"], "user": r["user"], "is_planned": is_planned,
        })

    # Break/Lunch minutes beyond their allowance become unplanned.
    break_excess = break_total - BREAK_ALLOWANCE_MIN
    if break_excess > 0:
        unplanned.append({"name": "Break (over allowance)", "minutes": break_excess})
    lunch_excess = lunch_total - LUNCH_ALLOWANCE_MIN
    if lunch_excess > 0:
        unplanned.append({"name": "Lunch (over allowance)", "minutes": lunch_excess})

    # Planned downtime is the fixed per-shift allowance.
    planned = [{"name": "Scheduled Break & Lunch",
                "minutes": PLANNED_MINUTES_PER_SHIFT}]
    return planned, unplanned, raw


def get_coil_inputs(machine_id, start, end, fallback_end):
    """
    Return (coils, raw_rows) for a window.

    coils is a list of {'serial','planned_ct_min','completion_pct'} ready for
    oee.calc:
        planned_ct_min = ideal_ct_min (hv_winding_time hours * 60)
        completion_pct = completion_percent / 100   (clamped 0..1 in oee.calc)

    completion_percent is derived in the oee/Coils query from work_orders only
    (op_status 16 = 100%, otherwise elapsed/ideal cycle time). For a coil with
    no actual_end, `fallback_end` is used as its end - this is the end of the
    current selection (shift end, or date-range end for All Shifts), so an
    unfinished coil is never credited past the window being viewed.
    """
    rows = _rows(NQ_COILS,
                 {"machineId": machine_id, "startTime": start, "endTime": end,
                  "fallbackEnd": fallback_end})
    coils, raw = [], []
    for r in rows:
        ideal_min = _f(r["ideal_ct_min"])
        completion_percent = _f(r["completion_percent"])   # 0..100 from work_orders
        completion = completion_percent / 100.0
        coils.append({
            "serial": r["serial_number"],
            "planned_ct_min": ideal_min,
            "completion_pct": completion,
        })
        raw.append({
            "serial": r["serial_number"], "op_status": r["op_status"],
            "actual_min": _f(r["actual_min"]), "ideal_ct_min": ideal_min,
            "completion_percent": completion_percent,
        })
    return coils, raw


# ---------------------------------------------------------------------------
# Aux datasets for charts / cards
# ---------------------------------------------------------------------------

def selection_fallback_end(windows):
    """
    The end datetime used for coils that have a start but no end: the latest
    window end across the selection (shift end for a single shift; date-range
    end for All Shifts), capped at the current time so a live shift never
    counts future minutes. Returns None for an empty selection.
    """
    if not windows:
        return None
    latest = windows[0]["end"]
    for w in windows[1:]:
        if system.date.isAfter(w["end"], latest):
            latest = w["end"]
    now = system.date.now()
    return now if system.date.isAfter(latest, now) else latest


def get_cycle_comparison(machine_id, start, end, fallback_end):
    """Return list of {'serial','ideal_time','actual_time'} for the chart.
    Coils with no actual_end are measured to fallback_end (selection end)."""
    rows = _rows(NQ_CYCLE_COMPARISON,
                 {"machineId": machine_id, "startTime": start, "endTime": end,
                  "fallbackEnd": fallback_end})
    out = []
    for r in rows:
        out.append({
            "serial": r["serial_number"],
            "ideal_time": _f(r["ideal_time"]),
            "actual_time": _f(r["actual_time"]),
        })
    return out


def get_pareto(machine_id, start, end, fallback_end):
    """
    Return Pareto rows with a cumulative % column computed here (not trusted
    from SQL). Each row: {'reason','total_min','cumulative_pct'}.
    Open downtime is measured to fallback_end (selection end).
    """
    rows = _rows(NQ_DOWNTIME_PARETO,
                 {"machineId": machine_id, "startTime": start, "endTime": end,
                  "fallbackEnd": fallback_end})
    total = 0.0
    parsed = []
    for r in rows:
        m = _f(r["total_min"])
        total += m
        parsed.append({"reason": r["reason"], "total_min": m})

    running = 0.0
    for p in parsed:
        running += p["total_min"]
        if total > 0.0:
            p["cumulative_pct"] = round(running / total * 100.0, 2)
        else:
            p["cumulative_pct"] = 0.0
    return parsed


def get_prod_status(machine_id, start, end):
    """Return {'started','completed','in_progress'} counts for the card."""
    rows = _rows(NQ_PROD_STATUS,
                 {"machineId": machine_id, "startTime": start, "endTime": end})
    if len(rows) == 0:
        return {"started": 0, "completed": 0, "in_progress": 0}
    r = rows[0]
    return {
        "started": int(_f(r["started"])),
        "completed": int(_f(r["completed"])),
        "in_progress": int(_f(r["in_progress"])),
    }


def get_machines():
    """Return list of {'id','code','name','line_id','section'} for dropdowns."""
    rows = _rows(NQ_MACHINES, {})
    out = []
    for r in rows:
        out.append({
            "id": r["MachineID"], "code": r["MachineCode"],
            "name": r["MachineName"], "line_id": r["LineID"],
            "section": r["Section"],
        })
    return out
    
    
def get_lines():
    """Return list of {'id','code','name','line_id','section'} for dropdowns."""
    rows = _rows(NQ_LINES, {})
    out = []
    for r in rows:
        out.append({
            "label": r["LineName"],
            "value": r["LineID"],
        })
    return out













#====================================================================================NEW OEE SCREEN SCRIPTS from here====================================================



"""
oee.data -- Data access layer.

Every database read in the OEE screen goes through this module, and every
query is an Ignition NAMED QUERY in the project folder "oee/".
Database connection for all of them: Ignition_DEV-WOCL-Ignition

Named queries used (project scope):
    oee/Lines                 -> tbl_Line (active lines)
    oee/MachinesByLine        -> tbl_Machine filtered by LineID
    oee/Shifts                -> tbl_Shift (active shift definitions)
    oee/DowntimeLog           -> tbl_DowntimeLog + reason/category joins
    oee/DowntimePareto        -> downtime minutes grouped by reason
    oee/DowntimeDaily         -> downtime minutes grouped by day + category
    oee/WorkOrders            -> work_orders joined to lspec_metadata

This module only fetches and reshapes rows (dataset -> list of dicts).
All arithmetic lives in oee.calc.
"""

NQ_FOLDER = 'oee_NQ/'


def _rowsToDicts(ds):
    """PyDataset/BasicDataset -> list of dicts keyed by column name."""
    if ds is None:
        return []
    pyds = system.dataset.toPyDataSet(ds)
    cols = list(pyds.getColumnNames())
    out = []
    for row in pyds:
        d = {}
        for i in range(len(cols)):
            d[cols[i]] = row[i]
        out.append(d)
    return out


def _run(name, params=None):
    return _rowsToDicts(system.db.runNamedQuery(NQ_FOLDER + name, params or {}))


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

def getLines():
    """Active lines from tbl_Line."""
    return _run('Lines')


def getMachines(lineId):
    """Active machines for the selected line (cascading filter)."""
    if lineId is None:
        return []
    return _run('MachinesByLine', {'lineId': lineId})


def getShifts():
    """Active shift definitions from tbl_Shift.
    Shift start/end times are ALWAYS read from this table, never hardcoded."""
    return _run('Shifts')


# ---------------------------------------------------------------------------
# Range data
# ---------------------------------------------------------------------------

def getDowntimeRows(machineId, startDate, endDate, shiftId=0):
    """tbl_DowntimeLog rows OVERLAPPING the range (clipped minutes come back
    in ClippedMinutes), with ReasonName / CategoryID / CategoryName joined.
    shiftId 0 = all shifts, otherwise filters on tbl_DowntimeLog.ShiftID."""
    if machineId is None or startDate is None or endDate is None:
        return []
    return _run('DowntimeLog', {
        'machineId': machineId, 'startDate': startDate, 'endDate': endDate,
        'shiftId': shiftId or 0,
    })


def getDowntimePareto(machineId, startDate, endDate, shiftId=0):
    """Range-clipped downtime minutes grouped by reason, largest first."""
    if machineId is None or startDate is None or endDate is None:
        return []
    return _run('DowntimePareto', {
        'machineId': machineId, 'startDate': startDate, 'endDate': endDate,
        'shiftId': shiftId or 0,
    })


def getDowntimeDaily(machineId, startDate, endDate, shiftId=0):
    """Downtime minutes per calendar day and category, split at midnight
    and clipped to the range in SQL (for the daily OEE trend)."""
    if machineId is None or startDate is None or endDate is None:
        return []
    return _run('DowntimeDaily', {
        'machineId': machineId, 'startDate': startDate, 'endDate': endDate,
        'shiftId': shiftId or 0,
    })


def getWorkOrders(machineId, startDate, endDate):
    """work_orders started in the range for the machine, joined to
    lspec_metadata for hv_winding_time (ideal cycle time, hours)."""
    if machineId is None or startDate is None or endDate is None:
        return []
    return _run('WorkOrders', {
        'machineId': machineId, 'startDate': startDate, 'endDate': endDate,
    })