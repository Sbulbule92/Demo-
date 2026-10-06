"""
OEE Dashboard Assembly
Ignition Project Library package:  oee.dashboard

Top-level functions the Perspective view calls. Every value is built only from
query results run through the validated oee.calc engine.

Primary entry point (supports a DATE RANGE and an "All Shifts" selection):

    payload = oee.dashboard.build_payload(fromDate, toDate, shiftSel, machineId)
        fromDate / toDate : dates (inclusive); pass the same value for one day
        shiftSel          : 1, 2, 3, or "ALL"
        machineId         : tbl_Machine.MachineID

Thin wrappers kept for convenience / backward compatibility:

    build_shift_payload(date, shiftId, machineId)   -> one date, one shift
    build_daily_payload(date, machineId)            -> one date, all shifts

Jython 2.7 (Ignition).
"""
from __future__ import division

import system
import oee.calc as calc
import oee.data as data


# ---------------------------------------------------------------------------
# Shaping helpers
# ---------------------------------------------------------------------------

def _kpi_block(result):
    """Shape the calc result into the card values the view binds to."""
    return {
        "oee_pct": result["oee_pct"],
        "availability_pct": result["availability_pct"],
        "performance_pct": result["performance_pct"],
        "quality_pct": result["quality_pct"],
        "production_time": calc.minutes_to_hhmmss(
            result["planned_production_time_min"]),     # "Without planned DT"
        "total_dt": calc.minutes_to_hhmmss(
            result["unplanned_downtime_min"]),          # "Only unplanned DT"
        "planned_production_time_min": result["planned_production_time_min"],
        "operating_time_min": result["operating_time_min"],
        "planned_downtime_min": result["planned_downtime_min"],
        "unplanned_downtime_min": result["unplanned_downtime_min"],
        "earned_minutes": result["earned_minutes"],
    }


def _downtime_dataset(raw_downtime):
    headers = ["id", "start_time", "end_time", "duration_min",
               "reason", "remarks", "user"]
    rows = []
    for d in raw_downtime:
        rows.append([d["id"], d["start_time"], d["end_time"], d["duration_min"],
                     d["reason"], d["remarks"], d["user"]])
    return system.dataset.toDataSet(headers, rows)


def _pareto_dataset(pareto):
    headers = ["reason", "total_min", "cumulative_pct"]
    rows = [[p["reason"], p["total_min"], p["cumulative_pct"]] for p in pareto]
    return system.dataset.toDataSet(headers, rows)


def _cycle_dataset(cycle):
    headers = ["serial", "ideal_time", "actual_time"]
    rows = [[c["serial"], c["ideal_time"], c["actual_time"]] for c in cycle]
    return system.dataset.toDataSet(headers, rows)


def _merge_pareto(accumulator):
    """
    Turn a {reason: minutes} accumulator into a sorted Pareto list with a
    cumulative % computed AFTER merging across all windows (never trusted from
    a single window).
    """
    parsed = [{"reason": k, "total_min": v} for k, v in accumulator.items()]
    parsed.sort(key=lambda p: p["total_min"], reverse=True)
    total = 0.0
    for p in parsed:
        total += p["total_min"]
    running = 0.0
    for p in parsed:
        running += p["total_min"]
        p["cumulative_pct"] = round(running / total * 100.0, 2) if total > 0 else 0.0
    return parsed


# ---------------------------------------------------------------------------
# Generalized payload builder (date range + shift selection)
# ---------------------------------------------------------------------------

def build_payload(from_date, to_date, shift_selection, machine_id):
    """
    Assemble the complete dashboard payload for a machine over a date range and
    a shift selection. Downtime and coils are gathered from every window in the
    range, accumulated, and OEE is computed ONCE on the combined data so the
    headline number is internally consistent (not an average of averages).
    """
    windows = data.resolve_windows(from_date, to_date, shift_selection)
    if not windows:
        return _empty_payload()

    fallback_end = data.selection_fallback_end(windows)
    total_duration = 0.0
    planned_all, unplanned_all, coils_all = [], [], []
    raw_dt_all, cycle_all = [], []
    pareto_accum = {}
    prod = {"started": 0, "completed": 0, "in_progress": 0}

    for w in windows:
        start, end = w["start"], w["end"]
        total_duration += w["duration_min"]

        planned, unplanned, raw_dt = data.get_downtime_inputs(machine_id, start, end, fallback_end)
        planned_all.extend(planned)
        unplanned_all.extend(unplanned)
        raw_dt_all.extend(raw_dt)

        coils, _raw = data.get_coil_inputs(machine_id, start, end, fallback_end)
        coils_all.extend(coils)

        for p in data.get_pareto(machine_id, start, end, fallback_end):
            pareto_accum[p["reason"]] = pareto_accum.get(p["reason"], 0.0) + p["total_min"]

        cycle_all.extend(data.get_cycle_comparison(machine_id, start, end, fallback_end))

        ps = data.get_prod_status(machine_id, start, end)
        prod["started"] += ps["started"]
        prod["completed"] += ps["completed"]
        prod["in_progress"] += ps["in_progress"]

    result = calc.compute_oee(total_duration, planned_all, unplanned_all, coils_all)

    payload = _kpi_block(result)
    payload["window_count"] = len(windows)
    payload["prod_status"] = prod
    payload["downtime_table"] = _downtime_dataset(raw_dt_all)
    payload["pareto_chart"] = _pareto_dataset(_merge_pareto(pareto_accum))
    payload["cycle_chart"] = _cycle_dataset(cycle_all)
    return payload


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def build_shift_payload(shift_date, shift_id, machine_id):
    """One date, one shift."""
    return build_payload(shift_date, shift_date, shift_id, machine_id)


def build_daily_payload(shift_date, machine_id):
    """One date, all shifts."""
    return build_payload(shift_date, shift_date, "ALL", machine_id)


# ---------------------------------------------------------------------------
# Empty / zeroed payload
# ---------------------------------------------------------------------------

def _empty_payload():
    zero = calc.compute_oee(0.0, [], [], [])
    payload = _kpi_block(zero)
    payload["window_count"] = 0
    payload["prod_status"] = {"started": 0, "completed": 0, "in_progress": 0}
    payload["downtime_table"] = _downtime_dataset([])
    payload["pareto_chart"] = _pareto_dataset([])
    payload["cycle_chart"] = _cycle_dataset([])
    return payload


# ---------------------------------------------------------------------------
# Perspective view payload (JSON-safe: plain dicts/lists, no Dataset objects)
# ---------------------------------------------------------------------------

def _empty_view_payload():
    zero = calc.compute_oee(0.0, [], [], [])
    return {
        "oee_pct": zero["oee_pct"], "availability_pct": zero["availability_pct"],
        "performance_pct": zero["performance_pct"], "quality_pct": zero["quality_pct"],
        "production_time": "00:00:00", "total_dt": "00:00:00",
        "planned_dt": "00:00:00", "operating_time": "00:00:00",
        "total_downtime": "00:00:00",
        "prod_status": {"started": 0, "completed": 0, "in_progress": 0},
        "downtime_table": [], "pareto_chart": [], "cycle_chart": [],
        "window_count": 0,
    }


def build_view_payload(from_date, to_date, shift_selection, machine_id):
    """
    JSON-safe payload for a Perspective view. Bind a custom view property to:
 
        runScript('oee.dashboard.build_view_payload', 0,
                  {view.params.fromDate}, {view.params.toDate},
                  {view.params.shiftSel}, {view.params.machineId})
 
    Returns plain dicts/lists so Perspective stores it cleanly and Table/Chart
    components can bind straight to the sub-keys.
    """
    windows = data.resolve_windows(from_date, to_date, shift_selection)
    if not windows:
        return _empty_view_payload()
 
    fallback_end = data.selection_fallback_end(windows)
    total_duration = 0.0
    planned, unplanned, coils, raw_dt, cycle = [], [], [], [], []
    pareto_accum = {}
    prod = {"started": 0, "completed": 0, "in_progress": 0}
 
    for w in windows:
        s, e = w["start"], w["end"]
        total_duration += w["duration_min"]
        p, u, rd = data.get_downtime_inputs(machine_id, s, e, fallback_end)
        planned.extend(p); unplanned.extend(u); raw_dt.extend(rd)
        c, _r = data.get_coil_inputs(machine_id, s, e, fallback_end)
        coils.extend(c)
        for pp in data.get_pareto(machine_id, s, e, fallback_end):
            pareto_accum[pp["reason"]] = pareto_accum.get(pp["reason"], 0.0) + pp["total_min"]
        cycle.extend(data.get_cycle_comparison(machine_id, s, e, fallback_end))
        ps = data.get_prod_status(machine_id, s, e)
        prod["started"] += ps["started"]
        prod["completed"] += ps["completed"]
        prod["in_progress"] += ps["in_progress"]
 
    r = calc.compute_oee(total_duration, planned, unplanned, coils)
 
    dt_rows = []
    for d in raw_dt:
        dt_rows.append({
            "id": d["id"],
            "start_time": system.date.format(d["start_time"], "MM/dd/yyyy hh:mm a") if d["start_time"] else "",
            "end_time": system.date.format(d["end_time"], "MM/dd/yyyy hh:mm a") if d["end_time"] else "",
            "duration_min": d["duration_min"],
            "reason": d["reason"],
            "type": "Planned" if d["is_planned"] == 1 else "Unplanned",
            "user": d["user"],
        })
 
    pareto = _merge_pareto(pareto_accum)
    cycle_rows = []
    idx = 0
    for c in cycle:
        idx += 1
        cycle_rows.append({"id": idx, "coil": "C%03d" % idx,
                           "serial": c["serial"], "ideal_time": c["ideal_time"],
                           "actual_time": c["actual_time"]})
    return {
        "oee_pct": r["oee_pct"], "availability_pct": r["availability_pct"],
        "performance_pct": r["performance_pct"], "quality_pct": r["quality_pct"],
        "production_time": calc.minutes_to_hhmmss(r["planned_production_time_min"]),
        "total_dt": calc.minutes_to_hhmmss(r["unplanned_downtime_min"]),
        "planned_dt": calc.minutes_to_hhmmss(r["planned_downtime_min"]),
        "operating_time": calc.minutes_to_hhmmss(r["operating_time_min"]),
        "total_downtime": calc.minutes_to_hhmmss(
            r["planned_downtime_min"] + r["unplanned_downtime_min"]),
        "prod_status": prod,
        "downtime_table": dt_rows,
        "pareto_chart": [{"reason": p["reason"], "total_min": p["total_min"],
                          "cumulative_pct": p["cumulative_pct"]} for p in pareto],
        "cycle_chart": cycle_rows,
        "window_count": len(windows),
    }
    


#====================================================================================NEW OEE SCREEN SCRIPTS from here====================================================

"""
oee.dashboard -- Binding-ready payload builders for the OEE Analysis view.

Every visible number on the screen comes from one of these functions;
each function fetches through oee.data and computes through oee.calc.
Nothing on the screen is hardcoded or invented.

Typical Perspective bindings (expression / runScript):

    view.custom.kpis
        runScript('oee.dashboard.getKPIs', 60000,
                  {view.custom.machineId},
                  {view.custom.startDate}, {view.custom.endDate},
                  {view.custom.refreshToken})

    view.custom.trend    -> oee.dashboard.getOeeTrend(...)
    view.custom.pareto   -> oee.dashboard.getDowntimePareto(...)
    view.custom.cycles   -> oee.dashboard.getCycleComparison(...)
    view.custom.downtime -> oee.dashboard.getDowntimeTable(...)
    view.custom.coils    -> oee.dashboard.getCoilTable(...)

The trailing 'token' argument exists only so the Refresh button can force
re-evaluation; it is never read.
"""


def _now():
    return system.date.now()


def _nowMs():
    return oee.calc.toMillis(_now())


# ---------------------------------------------------------------------------
# Filter options (cascading Line -> Machine)
# ---------------------------------------------------------------------------

def getLineOptions(token=None):
    """[{label, value}] for the Line dropdown."""
    out = []
    for row in oee.data.getLines():
        out.append({'label': u'%s' % (row.get('LineName') or row.get('LineCode')),
                    'value': row.get('LineID')})
    return out


def getMachineOptions(lineId, token=None):
    """[{label, value}] for the Machine dropdown - varies with the line."""
    out = []
    for row in oee.data.getMachines(lineId):
        out.append({'label': u'%s' % (row.get('MachineCode') or row.get('MachineName')),
                    'value': row.get('MachineID')})
    return out


def getShiftOptions(token=None):
    """[{label, value}] for the Shift dropdown. value 0 = All Shifts;
    others come straight from tbl_Shift (never hardcoded)."""
    out = [{'label': u'All Shifts', 'value': 0}]
    try:
        for row in oee.data.getShifts():
            out.append({'label': u'%s' % (row.get('ShiftName') or row.get('ShiftCode')),
                        'value': row.get('ShiftID')})
    except Exception, e:
        system.util.getLogger('oee.dashboard').error('getShiftOptions failed: %s' % e)
    return out


def _shiftBoundsFor(shifts, shiftId):
    """[(startMin, endMin)] for the selected shift, or None for All Shifts."""
    if not shiftId:
        return None
    out = []
    for row in shifts or []:
        if row.get('ShiftID') == shiftId:
            b = oee.calc.shiftBoundsMinutes(row)
            if b is not None:
                out.append(b)
    return out


def _coilInShift(row, shiftBounds):
    """A coil belongs to the selected shift when its actual_start
    time-of-day falls inside the shift window (overnight-safe)."""
    if shiftBounds is None:
        return True
    st = row.get('actual_start')
    if st is None:
        return False
    tod = (system.date.getHour24(st) * 60.0
           + system.date.getMinute(st)
           + system.date.getSecond(st) / 60.0)
    for bounds in shiftBounds:
        if oee.calc.timeOfDayInShift(tod, bounds[0], bounds[1]):
            return True
    return False


def _applyShiftClip(rows, startDate, endDate, bounds):
    """When a single shift is selected, tighten each coil's
    ClippedMinutes to the shift windows so earned credit is bounded by
    the same windows as operating time (fixes Performance > 100%%
    caused by coil work running past the shift end)."""
    if bounds is None:
        return rows
    rs = oee.calc.toMillis(startDate)
    reMs = oee.calc.toMillis(endDate)
    mids = _dayMidnightsMs(startDate, endDate)
    nowMs = _nowMs()
    for r in rows:
        sMs = oee.calc.toMillis(r.get('actual_start'))
        eMs = oee.calc.toMillis(r.get('actual_end'))
        if eMs is None:
            eMs = nowMs
        r['ClippedMinutes'] = oee.calc.shiftWindowOverlapMinutes(
            sMs, eMs, rs, reMs, mids, bounds)
        if r.get('ActualMinutes') is None and sMs is not None and eMs > sMs:
            r['ActualMinutes'] = (eMs - sMs) / 60000.0
    return rows


def _dayMidnightsMs(startDate, endDate):
    """Epoch-ms midnights for every day the range touches, INCLUDING the
    day before the start so overnight shifts spill in correctly."""
    out = []
    d = system.date.addDays(system.date.midnight(startDate), -1)
    endMid = system.date.midnight(endDate)
    guard = 0
    while not system.date.isAfter(d, endMid) and guard < 1200:
        guard += 1
        out.append(oee.calc.toMillis(d))
        d = system.date.addDays(d, 1)
    return out


def getDefaultSelection():
    """First active line and its first machine - used by the view onStartup
    script so the screen opens showing real data instead of blanks."""
    lines = getLineOptions()
    lineId = lines[0]['value'] if lines else None
    machines = getMachineOptions(lineId) if lineId is not None else []
    machineId = machines[0]['value'] if machines else None
    return {'lineId': lineId, 'machineId': machineId}


# ---------------------------------------------------------------------------
# Core aggregation shared by KPIs and trend
# ---------------------------------------------------------------------------

def _gather(machineId, startDate, endDate, shiftId=0):
    """Fetch everything once and compute the range-level numbers.
    shiftId 0 = all shifts; otherwise every element (scheduled time,
    downtime, coils) is restricted to the selected shift."""
    nowMs = _nowMs()
    startMs = oee.calc.toMillis(startDate)
    endMs = oee.calc.toMillis(endDate)

    shifts = oee.data.getShifts()
    bounds = _shiftBoundsFor(shifts, shiftId)

    downtimeRows = oee.data.getDowntimeRows(machineId, startDate, endDate, shiftId)
    woRows = [r for r in oee.data.getWorkOrders(machineId, startDate, endDate)
              if _coilInShift(r, bounds)]
    woRows = _applyShiftClip(woRows, startDate, endDate, bounds)

    totalMin = oee.calc.scheduledShiftMinutes(
        _dayMidnightsMs(startDate, endDate), startMs, endMs, nowMs, shifts, shiftId)
    dt = oee.calc.splitDowntime(downtimeRows)
    coils = oee.calc.coilMetrics(woRows, nowMs)

    kpis = oee.calc.computeKPIs(totalMin,
                                dt['plannedMinutes'],
                                dt['unplannedMinutes'],
                                coils['earnedMinutes'])
    return kpis, dt, coils, downtimeRows


# ---------------------------------------------------------------------------
# KPI payload
# ---------------------------------------------------------------------------

def getKPIs(machineId, startDate, endDate, shiftId=0, token=None):
    """Single dict feeding every KPI card on the screen."""
    empty = {
        'oee': 0.0, 'availability': 0.0, 'performance': 0.0, 'quality': 0.0,
        'productionTime': '00:00:00', 'plannedDt': '00:00:00',
        'unplannedDt': '00:00:00', 'earnedTime': '00:00:00',
        'coilsStarted': 0, 'coilsCompleted': 0, 'coilsInProgress': 0,
        'downtimeEvents': 0, 'mttr': 0.0, 'mtbf': 0.0,
        'topReason': '--', 'topReasonMinutes': 0,
        'hasData': False, 'message': 'Select a line, machine and date range.',
    }
    if machineId is None or startDate is None or endDate is None:
        return empty

    try:
        kpis, dt, coils, downtimeRows = _gather(machineId, startDate, endDate, shiftId)
    except Exception, e:
        empty['message'] = 'Data error: %s' % e
        system.util.getLogger('oee.dashboard').error('getKPIs failed: %s' % e)
        return empty

    # MTTR / MTBF on unplanned events only
    nUnplanned = dt['eventCountUnplanned']
    mttr = oee.calc.safeDiv(kpis['unplannedDtMinutes'], nUnplanned)
    mtbf = oee.calc.safeDiv(kpis['operatingMinutes'], nUnplanned)

    # Top unplanned downtime reason
    topReason, topMinutes = '--', 0.0
    byReason = {}
    for row in downtimeRows:
        if row.get('CategoryID') == oee.calc.UNPLANNED_CATEGORY_ID:
            r = row.get('ReasonName') or 'Unknown'
            clipped = row.get('ClippedMinutes')
            if clipped is None:
                clipped = row.get('DurationMinutes')
            byReason[r] = byReason.get(r, 0.0) + float(clipped or 0)
    for r in byReason:
        if byReason[r] > topMinutes:
            topReason, topMinutes = r, byReason[r]

    msgParts = []
    if not coils['cycles'] and kpis['totalMinutes'] > 0:
        msgParts.append('No coils started in this range.')
    if coils['skippedNoIdeal']:
        msgParts.append('%d coil(s) skipped - no ideal cycle time in lspec_metadata: %s'
                        % (len(coils['skippedNoIdeal']),
                           ', '.join([str(s) for s in coils['skippedNoIdeal'][:5]])))

    return {
        'oee': kpis['oee'],
        'availability': kpis['availability'],
        'performance': kpis['performance'],
        'quality': kpis['quality'],
        'productionTime': oee.calc.minutesToHMS(kpis['operatingMinutes']),
        'plannedDt': oee.calc.minutesToHMS(kpis['plannedDtMinutes']),
        'unplannedDt': oee.calc.minutesToHMS(kpis['unplannedDtMinutes']),
        'earnedTime': oee.calc.minutesToHMS(kpis['earnedMinutes']),
        'coilsStarted': coils['coilsStarted'],
        'coilsCompleted': coils['coilsCompleted'],
        'coilsInProgress': coils['coilsInProgress'],
        'downtimeEvents': dt['eventCountPlanned'] + dt['eventCountUnplanned'],
        'mttr': round(mttr, 1),
        'mtbf': round(mtbf, 1),
        'topReason': topReason,
        'topReasonMinutes': round(topMinutes, 0),
        'hasData': True,
        'message': ' '.join(msgParts),
    }


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def getOeeTrend(machineId, startDate, endDate, shiftId=0, token=None):
    """Per-day OEE/Availability/Performance for the XY trend chart.
    Returns list of {day, oee, availability, performance}."""
    if machineId is None or startDate is None or endDate is None:
        return []
    try:
        nowMs = _nowMs()
        shifts = oee.data.getShifts()
        bounds = _shiftBoundsFor(shifts, shiftId)

        dtDaily = oee.data.getDowntimeDaily(machineId, startDate, endDate, shiftId)
        woRows = [r for r in oee.data.getWorkOrders(machineId, startDate, endDate)
                  if _coilInShift(r, bounds)]
        woRows = _applyShiftClip(woRows, startDate, endDate, bounds)

        # downtime per day/category
        dtMap = {}
        for row in dtDaily:
            day = str(row.get('Day'))[:10]
            entry = dtMap.setdefault(day, {'planned': 0.0, 'unplanned': 0.0})
            dur = float(row.get('TotalMinutes') or 0)
            if row.get('CategoryID') == oee.calc.PLANNED_CATEGORY_ID:
                entry['planned'] += dur
            elif row.get('CategoryID') == oee.calc.UNPLANNED_CATEGORY_ID:
                entry['unplanned'] += dur

        # earned minutes per day (coil attributed to its start date)
        woMap = {}
        for row in woRows:
            startMs = oee.calc.toMillis(row.get('actual_start'))
            if startMs is None:
                continue
            day = system.date.format(row.get('actual_start'), 'yyyy-MM-dd')
            woMap.setdefault(day, []).append(row)

        # build day list
        out = []
        d = system.date.midnight(startDate)
        endMidnight = system.date.midnight(endDate)
        guard = 0
        while not system.date.isAfter(d, endMidnight) and guard < 400:
            guard += 1
            day = system.date.format(d, 'yyyy-MM-dd')
            dayStartMs = oee.calc.toMillis(d)
            dayEndMs = oee.calc.toMillis(system.date.addDays(d, 1))
            prevMs = oee.calc.toMillis(system.date.addDays(d, -1))
            totalMin = oee.calc.scheduledShiftMinutes(
                [prevMs, dayStartMs], dayStartMs, dayEndMs, nowMs, shifts, shiftId)
            if totalMin > 0:
                dtE = dtMap.get(day, {'planned': 0.0, 'unplanned': 0.0})
                coils = oee.calc.coilMetrics(woMap.get(day, []), nowMs)
                k = oee.calc.computeKPIs(totalMin, dtE['planned'], dtE['unplanned'],
                                         coils['earnedMinutes'])
                out.append({'day': day, 'oee': k['oee'],
                            'availability': k['availability'],
                            'performance': k['performance']})
            d = system.date.addDays(d, 1)
        return out
    except Exception, e:
        system.util.getLogger('oee.dashboard').error('getOeeTrend failed: %s' % e)
        return []


def getDowntimePareto(machineId, startDate, endDate, shiftId=0, token=None):
    """[{reason, minutes, cumulativePct}] largest first, for the Pareto chart."""
    if machineId is None or startDate is None or endDate is None:
        return []
    try:
        rows = oee.data.getDowntimePareto(machineId, startDate, endDate, shiftId)
        total = 0.0
        for r in rows:
            total += float(r.get('TotalMinutes') or 0)
        out = []
        running = 0.0
        for r in rows:
            minutes = float(r.get('TotalMinutes') or 0)
            running += minutes
            out.append({
                'reason': r.get('ReasonName') or 'Unknown',
                'minutes': round(minutes, 1),
                'cumulativePct': round(oee.calc.safeDiv(running, total) * 100.0, 1),
            })
        return out
    except Exception, e:
        system.util.getLogger('oee.dashboard').error('getDowntimePareto failed: %s' % e)
        return []


def getCycleComparison(machineId, startDate, endDate, shiftId=0, token=None):
    """[{serial, idealMin, actualMin, completionPct, status}] per coil
    for the Ideal vs Actual chart (serial shortened for the axis)."""
    if machineId is None or startDate is None or endDate is None:
        return []
    try:
        bounds = _shiftBoundsFor(oee.data.getShifts(), shiftId)
        woRows = [r for r in oee.data.getWorkOrders(machineId, startDate, endDate)
                  if _coilInShift(r, bounds)]
        woRows = _applyShiftClip(woRows, startDate, endDate, bounds)
        coils = oee.calc.coilMetrics(woRows, _nowMs())
        out = []
        for c in coils['cycles']:
            serial = c['serial'] or ''
            # '1LUJJC319030037_CoilWind_1' -> '...037_CW1' style short label
            short = serial
            if len(serial) > 14:
                short = serial[-14:]
            # Boundary rule 2026-07-03: the chart compares the coil's time
            # INSIDE the selected range against the ideal CT. A work order
            # spanning weeks (paused / stale) would otherwise dwarf the
            # axis and hide the ideal bar. Full life stays available in
            # the coil table.
            actual = c.get('clippedMin')
            if actual is None:
                actual = c['actualMin'] if c['actualMin'] is not None else 0
            out.append({
                'serial': short,
                'serialFull': serial,
                'idealMin': c['idealMin'],
                'actualMin': round(actual, 2),
                'fullLifeMin': c['actualMin'],
                'completionPct': c['completionPct'],
                'status': c['status'],
            })
        return out
    except Exception, e:
        system.util.getLogger('oee.dashboard').error('getCycleComparison failed: %s' % e)
        return []


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def getDowntimeTable(machineId, startDate, endDate, shiftId=0, token=None):
    """Rows for the downtime log table."""
    if machineId is None or startDate is None or endDate is None:
        return []
    try:
        rows = oee.data.getDowntimeRows(machineId, startDate, endDate, shiftId)
        out = []
        for r in rows:
            out.append({
                'logId': r.get('LogID'),
                'startTime': system.date.format(r.get('StartTime'), 'MM/dd HH:mm:ss') if r.get('StartTime') else '',
                'endTime': system.date.format(r.get('EndTime'), 'MM/dd HH:mm:ss') if r.get('EndTime') else '',
                'durationMin': round(float((r.get('ClippedMinutes') if r.get('ClippedMinutes') is not None else r.get('DurationMinutes')) or 0), 1),
                'rawMin': round(float(r.get('DurationMinutes') or 0), 1),
                'category': r.get('CategoryName') or '',
                'type': 'Planned' if r.get('CategoryID') == oee.calc.PLANNED_CATEGORY_ID else 'Unplanned',
                'reason': r.get('ReasonName') or '',
                'remarks': r.get('Remarks') or '',
                'user': r.get('UserName') or '',
            })
        return out
    except Exception, e:
        system.util.getLogger('oee.dashboard').error('getDowntimeTable failed: %s' % e)
        return []


def getCoilTable(machineId, startDate, endDate, shiftId=0, token=None):
    """Rows for the coils / work-order table."""
    if machineId is None or startDate is None or endDate is None:
        return []
    try:
        bounds = _shiftBoundsFor(oee.data.getShifts(), shiftId)
        woRows = [r for r in oee.data.getWorkOrders(machineId, startDate, endDate)
                  if _coilInShift(r, bounds)]
        woRows = _applyShiftClip(woRows, startDate, endDate, bounds)
        nowMs = _nowMs()
        out = []
        for r in woRows:
            startMs = oee.calc.toMillis(r.get('actual_start'))
            endMs = oee.calc.toMillis(r.get('actual_end'))
            idealHours = r.get('hv_winding_time')
            idealMin = float(idealHours) * 60.0 if idealHours is not None else None
            pct = oee.calc.completionPct(r.get('op_status'), startMs, endMs,
                                         idealMin, nowMs) * 100.0
            actualMin = None
            effEnd = endMs if endMs is not None else nowMs
            if startMs is not None and effEnd is not None and effEnd > startMs:
                actualMin = (effEnd - startMs) / oee.calc.MS_PER_MIN
            out.append({
                'poNumber': r.get('po_number'),
                'serial': r.get('serial_number'),
                'lspec': r.get('lspec_id'),
                'start': system.date.format(r.get('actual_start'), 'MM/dd HH:mm') if r.get('actual_start') else '',
                'end': system.date.format(r.get('actual_end'), 'MM/dd HH:mm') if r.get('actual_end') else '',
                'idealMin': round(idealMin, 1) if idealMin is not None else None,
                'actualMin': round(actualMin, 1) if actualMin is not None else None,
                'completionPct': round(pct, 1),
                'status': 'Completed' if r.get('op_status') == oee.calc.COMPLETE_OP_STATUS
                          else ('In Progress' if endMs is None and startMs is not None else 'Stopped'),
            })
        return out
    except Exception, e:
        system.util.getLogger('oee.dashboard').error('getCoilTable failed: %s' % e)
        return []


# ---------------------------------------------------------------------------
# Excel export - "Download" button on the OEE screen
# ---------------------------------------------------------------------------

def _cell(row, key):
    """Read one value from a Perspective ObjectWrapper / dict row.
    Missing values stay None (never '') so numeric columns keep a
    single type - system.dataset.toDataSet refuses mixed columns."""
    try:
        v = row[key]
    except Exception:
        try:
            v = row.get(key)
        except Exception:
            v = None
    return v


def _toText(v):
    """None-safe text coercion (Jython 2 unicode aware)."""
    if v is None:
        return u''
    try:
        return unicode(v)          # Jython 2 / Ignition
    except NameError:
        return str(v)              # local Python 3 test runs


def _isText(v):
    try:
        return isinstance(v, basestring)
    except NameError:
        return isinstance(v, str)


def _sheet(rows, cols, headers):
    """list-of-dicts -> Dataset with a fixed column order.

    toDataSet types each column from its first value and will not
    convert between numbers and strings, so any column that ends up
    with BOTH is normalised to text before the dataset is built."""
    data = []
    for r in (rows or []):
        data.append([_cell(r, c) for c in cols])
    for j in range(len(cols)):
        vals = [row[j] for row in data if row[j] is not None]
        hasText = any(_isText(v) for v in vals)
        hasOther = any(not _isText(v) for v in vals)
        if hasText and hasOther:
            for row in data:
                if row[j] is not None:
                    row[j] = _toText(row[j])
    return system.dataset.toDataSet(list(headers), data)


def _optionLabel(options, value):
    for o in (options or []):
        if _cell(o, 'value') == value:
            return _cell(o, 'label')
    return str(value)


def exportExcel(kpis, trend, pareto, cycles, downtimeRows, coilRows,
                lineOptions, machineOptions, shiftOptions,
                lineId, machineId, shiftId, startDate, endDate):
    """Download everything currently shown on the OEE screen as one
    multi-sheet Excel file. Wire the Download button as:

        c = self.view.custom
        oee.dashboard.exportExcel(
            c.kpis, c.trend, c.pareto, c.cycles,
            c.downtimeRows, c.coilRows,
            c.lineOptions, c.machineOptions, c.shiftOptions,
            c.lineId, c.machineId, c.shiftId,
            c.startDate, c.endDate)

    Every argument is one view.custom property; the function exports the
    EXACT data the bindings already loaded (no re-query), so the file
    always matches the screen.
    """
    try:
        k = kpis or {}
        summary = [
            ('Line',                _optionLabel(lineOptions, lineId)),
            ('Machine',             _optionLabel(machineOptions, machineId)),
            ('Shift',               _optionLabel(shiftOptions, shiftId)),
            ('From',                system.date.format(startDate, 'yyyy-MM-dd HH:mm') if startDate else ''),
            ('To',                  system.date.format(endDate, 'yyyy-MM-dd HH:mm') if endDate else ''),
            ('Generated',           system.date.format(system.date.now(), 'yyyy-MM-dd HH:mm:ss')),
            ('', ''),
            ('OEE %',               _cell(k, 'oee')),
            ('Availability %',      _cell(k, 'availability')),
            ('Performance %',       _cell(k, 'performance')),
            ('Quality %',           _cell(k, 'quality')),
            ('Production Time',     _cell(k, 'productionTime')),
            ('Earned Time',         _cell(k, 'earnedTime')),
            ('Planned Downtime',    _cell(k, 'plannedDt')),
            ('Unplanned Downtime',  _cell(k, 'unplannedDt')),
            ('Downtime Events',     _cell(k, 'downtimeEvents')),
            ('MTTR (min)',          _cell(k, 'mttr')),
            ('MTBF (min)',          _cell(k, 'mtbf')),
            ('Top Downtime Reason', _cell(k, 'topReason')),
            ('Top Reason (min)',    _cell(k, 'topReasonMinutes')),
            ('Coils Started',       _cell(k, 'coilsStarted')),
            ('Coils Completed',     _cell(k, 'coilsCompleted')),
            ('Coils In Progress',   _cell(k, 'coilsInProgress')),
            ('Note',                _cell(k, 'message')),
        ]
        dsSummary = system.dataset.toDataSet(['Metric', 'Value'],
                                             [[a, _toText(b)] for a, b in summary])

        dsTrend = _sheet(trend,
                         ['day', 'oee', 'availability', 'performance'],
                         ['Day', 'OEE %', 'Availability %', 'Performance %'])

        dsPareto = _sheet(pareto,
                          ['reason', 'minutes', 'cumulativePct'],
                          ['Reason', 'Unplanned Minutes', 'Cumulative %'])

        dsCycles = _sheet(cycles,
                          ['serialFull', 'idealMin', 'actualMin',
                           'fullLifeMin', 'completionPct', 'status'],
                          ['Serial', 'Ideal (min)', 'Actual in range (min)',
                           'Full life (min)', 'Completion %', 'Status'])

        dsDowntime = _sheet(downtimeRows,
                            ['logId', 'startTime', 'endTime', 'durationMin',
                             'rawMin', 'type', 'category', 'reason',
                             'remarks', 'user'],
                            ['Log ID', 'Start', 'End', 'Minutes (in range)',
                             'Minutes (full)', 'Type', 'Category', 'Reason',
                             'Remarks', 'User'])

        dsCoils = _sheet(coilRows,
                         ['poNumber', 'serial', 'lspec', 'start', 'end',
                          'idealMin', 'actualMin', 'completionPct', 'status'],
                         ['PO Number', 'Serial', 'LSpec', 'Start', 'End',
                          'Ideal (min)', 'Actual (min)', 'Completion %',
                          'Status'])

        datasets = [dsSummary, dsTrend, dsPareto, dsCycles, dsDowntime, dsCoils]
        names = ['Summary', 'Daily Trend', 'Downtime Pareto',
                 'Cycle Times', 'Downtime Log', 'Coils']
        try:
            xls = system.dataset.toExcel(True, datasets, False, names)
        except Exception:
            # older signature without sheet names
            xls = system.dataset.toExcel(True, datasets)

        fname = 'OEE_%s_%s_to_%s.xlsx' % (
            _optionLabel(machineOptions, machineId),
            system.date.format(startDate, 'yyyyMMdd') if startDate else 'x',
            system.date.format(endDate, 'yyyyMMdd') if endDate else 'x')
        system.perspective.download(fname.replace(' ', '_'), xls)
    except Exception, e:
        system.util.getLogger('oee.dashboard').error('exportExcel failed: %s' % e)


# ---------------------------------------------------------------------------
# Styled Excel dashboard export (Apache POI, bundled with the gateway)
# ---------------------------------------------------------------------------

# KPI colour bands for the dashboard tiles - adjust to plant targets
KPI_GOOD = 85.0   # >= green
KPI_OK = 60.0     # >= amber, below red


def exportExcelDashboard(kpis, trend, pareto, cycles, downtimeRows, coilRows,
                         lineOptions, machineOptions, shiftOptions,
                         lineId, machineId, shiftId, startDate, endDate):
    """Styled multi-sheet Excel: a formatted Dashboard sheet (KPI tiles,
    top-downtime table, native trend + pareto charts) followed by the raw
    data sheets. Same signature and wiring as exportExcel:

        c = self.view.custom
        oee.dashboard.exportExcelDashboard(
            c.kpis, c.trend, c.pareto, c.cycles,
            c.downtimeRows, c.coilRows,
            c.lineOptions, c.machineOptions, c.shiftOptions,
            c.lineId, c.machineId, c.shiftId,
            c.startDate, c.endDate)
    """
    try:
        from org.apache.poi.xssf.usermodel import XSSFWorkbook
        from org.apache.poi.ss.usermodel import (FillPatternType, IndexedColors,
                                                 HorizontalAlignment,
                                                 VerticalAlignment, BorderStyle)
        from org.apache.poi.ss.util import CellRangeAddress
        from java.io import ByteArrayOutputStream

        k = kpis or {}
        wb = XSSFWorkbook()

        # ------------------------------------------------------------ styles
        def style(bold=False, size=11, color=None, fill=None, fmt=None,
                  center=False, border=False):
            st = wb.createCellStyle()
            f = wb.createFont()
            f.setBold(bold)
            f.setFontHeightInPoints(size)
            if color is not None:
                f.setColor(color.getIndex())
            st.setFont(f)
            if fill is not None:
                st.setFillForegroundColor(fill.getIndex())
                st.setFillPattern(FillPatternType.SOLID_FOREGROUND)
            if fmt is not None:
                st.setDataFormat(wb.createDataFormat().getFormat(fmt))
            if center:
                st.setAlignment(HorizontalAlignment.CENTER)
                st.setVerticalAlignment(VerticalAlignment.CENTER)
            if border:
                for side in ('Top', 'Bottom', 'Left', 'Right'):
                    getattr(st, 'setBorder' + side)(BorderStyle.THIN)
            return st

        IC = IndexedColors
        stTitle = style(bold=True, size=18, color=IC.WHITE, fill=IC.DARK_BLUE, center=True)
        stSub = style(size=10, color=IC.WHITE, fill=IC.DARK_BLUE, center=True)
        stKpiLbl = style(bold=True, size=10, fill=IC.GREY_25_PERCENT, center=True, border=True)
        stKpiG = style(bold=True, size=22, color=IC.WHITE, fill=IC.GREEN, fmt='0.0"%"', center=True, border=True)
        stKpiA = style(bold=True, size=22, color=IC.WHITE, fill=IC.GOLD, fmt='0.0"%"', center=True, border=True)
        stKpiR = style(bold=True, size=22, color=IC.WHITE, fill=IC.RED, fmt='0.0"%"', center=True, border=True)
        stStatV = style(bold=True, size=12, center=True, border=True)
        stHead = style(bold=True, size=10, color=IC.WHITE, fill=IC.DARK_BLUE, border=True)
        stNum = style(fmt='#,##0.0', border=True)
        stTxt = style(border=True)

        def kpiStyle(v):
            try:
                v = float(v)
            except (TypeError, ValueError):
                return stKpiR
            if v >= KPI_GOOD:
                return stKpiG
            if v >= KPI_OK:
                return stKpiA
            return stKpiR

        # ------------------------------------------------- data sheets first
        def dataSheet(name, headers, rows, cols, numericCols):
            sh = wb.createSheet(name)
            hr = sh.createRow(0)
            for j, h in enumerate(headers):
                c = hr.createCell(j)
                c.setCellValue(h)
                c.setCellStyle(stHead)
            for i, r in enumerate(rows or []):
                rr = sh.createRow(i + 1)
                for j, colKey in enumerate(cols):
                    c = rr.createCell(j)
                    v = _cell(r, colKey)
                    if v is None:
                        c.setCellStyle(stTxt)
                        continue
                    if j in numericCols:
                        try:
                            c.setCellValue(float(v))
                            c.setCellStyle(stNum)
                            continue
                        except (TypeError, ValueError):
                            pass
                    c.setCellValue(_toText(v))
                    c.setCellStyle(stTxt)
            for j in range(len(headers)):
                sh.autoSizeColumn(j)
            sh.createFreezePane(0, 1)
            return sh

        shTrend = dataSheet('Daily Trend',
                            ['Day', 'OEE %', 'Availability %', 'Performance %'],
                            trend, ['day', 'oee', 'availability', 'performance'],
                            set([1, 2, 3]))
        shPareto = dataSheet('Downtime Pareto',
                             ['Reason', 'Unplanned Minutes', 'Cumulative %'],
                             pareto, ['reason', 'minutes', 'cumulativePct'],
                             set([1, 2]))
        dataSheet('Cycle Times',
                  ['Serial', 'Ideal (min)', 'Actual in range (min)',
                   'Full life (min)', 'Completion %', 'Status'],
                  cycles, ['serialFull', 'idealMin', 'actualMin',
                           'fullLifeMin', 'completionPct', 'status'],
                  set([1, 2, 3, 4]))
        dataSheet('Downtime Log',
                  ['Log ID', 'Start', 'End', 'Minutes (in range)',
                   'Minutes (full)', 'Type', 'Category', 'Reason',
                   'Remarks', 'User'],
                  downtimeRows, ['logId', 'startTime', 'endTime', 'durationMin',
                                 'rawMin', 'type', 'category', 'reason',
                                 'remarks', 'user'],
                  set([0, 3, 4]))
        dataSheet('Coils',
                  ['PO Number', 'Serial', 'LSpec', 'Start', 'End',
                   'Ideal (min)', 'Actual (min)', 'Completion %', 'Status'],
                  coilRows, ['poNumber', 'serial', 'lspec', 'start', 'end',
                             'idealMin', 'actualMin', 'completionPct', 'status'],
                  set([5, 6, 7]))

        # ------------------------------------------------- dashboard sheet
        dash = wb.createSheet('Dashboard')
        wb.setSheetOrder('Dashboard', 0)
        wb.setActiveSheet(0)
        wb.setSelectedTab(0)
        for j in range(14):
            dash.setColumnWidth(j, 256 * 13)

        def put(r, c, v, st):
            row = dash.getRow(r)
            if row is None:
                row = dash.createRow(r)
            cell = row.createCell(c)
            if v is not None:
                try:
                    cell.setCellValue(float(v))
                except (TypeError, ValueError):
                    cell.setCellValue(_toText(v))
            cell.setCellStyle(st)
            return cell

        def merge(r1, r2, c1, c2, st):
            dash.addMergedRegion(CellRangeAddress(r1, r2, c1, c2))
            for r in range(r1, r2 + 1):
                for c in range(c1, c2 + 1):
                    put(r, c, None, st)

        machineLbl = _optionLabel(machineOptions, machineId)
        merge(0, 0, 0, 13, stTitle)
        put(0, 0, 'OEE DASHBOARD - %s' % machineLbl, stTitle)
        sub = 'Line: %s   Shift: %s   From: %s   To: %s   Generated: %s' % (
            _optionLabel(lineOptions, lineId),
            _optionLabel(shiftOptions, shiftId),
            system.date.format(startDate, 'yyyy-MM-dd HH:mm') if startDate else '',
            system.date.format(endDate, 'yyyy-MM-dd HH:mm') if endDate else '',
            system.date.format(system.date.now(), 'yyyy-MM-dd HH:mm'))
        merge(1, 1, 0, 13, stSub)
        put(1, 0, sub, stSub)

        tiles = [('OEE', _cell(k, 'oee')), ('AVAILABILITY', _cell(k, 'availability')),
                 ('PERFORMANCE', _cell(k, 'performance')), ('QUALITY', _cell(k, 'quality'))]
        for i, (lbl, val) in enumerate(tiles):
            c1 = i * 3
            merge(3, 3, c1, c1 + 2, stKpiLbl)
            put(3, c1, lbl, stKpiLbl)
            vs = kpiStyle(val)
            merge(4, 5, c1, c1 + 2, vs)
            put(4, c1, val, vs)

        stats = [('Production Time', _cell(k, 'productionTime')),
                 ('Earned Time', _cell(k, 'earnedTime')),
                 ('Planned DT', _cell(k, 'plannedDt')),
                 ('Unplanned DT', _cell(k, 'unplannedDt')),
                 ('MTTR (min)', _cell(k, 'mttr')),
                 ('MTBF (min)', _cell(k, 'mtbf')),
                 ('Coils Done', _cell(k, 'coilsCompleted'))]
        for i, (lbl, val) in enumerate(stats):
            c1 = i * 2
            put(7, c1, lbl, stKpiLbl)
            put(7, c1 + 1, None, stKpiLbl)
            dash.addMergedRegion(CellRangeAddress(7, 7, c1, c1 + 1))
            put(8, c1, val, stStatV)
            put(8, c1 + 1, None, stStatV)
            dash.addMergedRegion(CellRangeAddress(8, 8, c1, c1 + 1))

        put(10, 0, 'TOP DOWNTIME REASONS', stHead)
        put(10, 1, 'Minutes', stHead)
        put(10, 2, 'Cum %', stHead)
        top = list(pareto or [])[:5]
        for i, p in enumerate(top):
            put(11 + i, 0, _toText(_cell(p, 'reason')), stTxt)
            put(11 + i, 1, _cell(p, 'minutes'), stNum)
            put(11 + i, 2, _cell(p, 'cumulativePct'), stNum)

        # ------------------------------------------------- native charts
        try:
            from org.apache.poi.xddf.usermodel.chart import (
                ChartTypes, AxisPosition, LegendPosition,
                XDDFDataSourcesFactory, BarDirection)
            drawing = dash.createDrawingPatriarch()

            nT = len(trend or [])
            if nT > 0:
                anchor = drawing.createAnchor(0, 0, 0, 0, 4, 10, 9, 26)
                chart = drawing.createChart(anchor)
                chart.setTitleText('Daily OEE Trend')
                chart.setTitleOverlay(False)
                chart.getOrAddLegend().setPosition(LegendPosition.TOP)
                bottom = chart.createCategoryAxis(AxisPosition.BOTTOM)
                left = chart.createValueAxis(AxisPosition.LEFT)
                cats = XDDFDataSourcesFactory.fromStringCellRange(
                    shTrend, CellRangeAddress(1, nT, 0, 0))
                data = chart.createData(ChartTypes.LINE, bottom, left)
                for col, name in ((1, 'OEE %'), (2, 'Availability %'), (3, 'Performance %')):
                    vals = XDDFDataSourcesFactory.fromNumericCellRange(
                        shTrend, CellRangeAddress(1, nT, col, col))
                    s = data.addSeries(cats, vals)
                    s.setTitle(name, None)
                chart.plot(data)

            nP = len(pareto or [])
            if nP > 0:
                anchor2 = drawing.createAnchor(0, 0, 0, 0, 9, 10, 14, 26)
                chart2 = drawing.createChart(anchor2)
                chart2.setTitleText('Downtime Pareto (min)')
                chart2.setTitleOverlay(False)
                bottom2 = chart2.createCategoryAxis(AxisPosition.BOTTOM)
                left2 = chart2.createValueAxis(AxisPosition.LEFT)
                cats2 = XDDFDataSourcesFactory.fromStringCellRange(
                    shPareto, CellRangeAddress(1, nP, 0, 0))
                vals2 = XDDFDataSourcesFactory.fromNumericCellRange(
                    shPareto, CellRangeAddress(1, nP, 1, 1))
                data2 = chart2.createData(ChartTypes.BAR, bottom2, left2)
                data2.setBarDirection(BarDirection.COL)
                s2 = data2.addSeries(cats2, vals2)
                s2.setTitle('Unplanned minutes', None)
                chart2.plot(data2)
        except Exception, ce:
            system.util.getLogger('oee.dashboard').warn(
                'exportExcelDashboard: charts skipped: %s' % ce)

        bos = ByteArrayOutputStream()
        wb.write(bos)
        wb.close()
        fname = 'OEE_Dashboard_%s_%s_to_%s.xlsx' % (
            machineLbl,
            system.date.format(startDate, 'yyyyMMdd') if startDate else 'x',
            system.date.format(endDate, 'yyyyMMdd') if endDate else 'x')
        system.perspective.download(fname.replace(' ', '_'), bos.toByteArray())
    except Exception, e:
        system.util.getLogger('oee.dashboard').error('exportExcelDashboard failed: %s' % e)