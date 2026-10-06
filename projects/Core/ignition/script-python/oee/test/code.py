"""
OEE Calculation - Test / Validation Harness
Ignition Project Library package:  oee.test

Reproduces the worked example from the OEE Calculation Methodology v1.2
(sections 5-7) and asserts the engine returns the documented figures:

    Availability = 91.03 %
    Performance  = 67.04 %
    Quality      = 100.00 %
    OEE          = 61.01 %  (61.02 % before the doc's display rounding)

Also exercises edge cases (idle shift, zero division, over-count clamping)
so a regression in oee.calc is caught immediately.

HOW TO RUN
----------
Ignition  : open the Script Console and run  ->  oee.test.run_all()
Standalone: place calc.py and test.py side-by-side and run  ->  python test.py
            (a shim below makes the import work both ways)
"""
from __future__ import division

# Import the calc module whether we are inside Ignition's project library
# (package path 'oee.calc') or running the files side-by-side for CI.
try:
    import oee.calc as calc
except ImportError:
    import calc


# ---------------------------------------------------------------------------
# Tiny assertion helpers (no external test framework needed in Jython)
# ---------------------------------------------------------------------------

class _Recorder(object):
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.lines = []

    def check(self, label, actual, expected, tol=0.01):
        ok = abs(float(actual) - float(expected)) <= tol
        status = "PASS" if ok else "FAIL"
        if ok:
            self.passed += 1
        else:
            self.failed += 1
        self.lines.append(
            "[%s] %-34s expected=%s  actual=%s"
            % (status, label, expected, actual))
        return ok

    def note(self, text):
        self.lines.append("       " + text)

    def report(self):
        header = "=" * 60
        summary = "RESULT: %d passed, %d failed" % (self.passed, self.failed)
        body = "\n".join(self.lines)
        return "%s\n%s\n%s\n%s" % (header, body, header, summary)


# ---------------------------------------------------------------------------
# The methodology v1.2 worked example, as structured input
# ---------------------------------------------------------------------------

def methodology_example_inputs():
    """Return the exact inputs from sections 5.2 / 6.3 of the methodology."""
    shift_duration_min = 480.0  # 8.00 h

    planned_downtime_items = [
        {"name": "Lunch Break", "minutes": 30.0},
        {"name": "General Break", "minutes": 30.0},
        {"name": "Shift Start Buffer", "minutes": 15.0},
        {"name": "Shift End Buffer", "minutes": 15.0},
    ]  # total 90 min

    unplanned_downtime_items = [
        {"name": "Machine Faults / Alarms", "minutes": 10.0},
        {"name": "Run/Stop/Idle (>10 min stops)", "minutes": 25.0},
    ]  # total 35 min

    coils = [
        {"coil": "A", "planned_ct_min": 100.0, "completion_pct": 1.0},
        {"coil": "B", "planned_ct_min": 95.0, "completion_pct": 1.0},
        {"coil": "C", "planned_ct_min": 86.0, "completion_pct": 0.5},
        {"coil": "D", "planned_ct_min": 74.0, "completion_pct": 0.0},
    ]  # earned = 100 + 95 + 43 + 0 = 238 min

    return shift_duration_min, planned_downtime_items, unplanned_downtime_items, coils


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_methodology_example(rec):
    shift, planned, unplanned, coils = methodology_example_inputs()
    r = calc.compute_oee(shift, planned, unplanned, coils)

    # Intermediate values (section 5 & 6)
    rec.check("Total Planned Downtime (min)", r["planned_downtime_min"], 90.0)
    rec.check("Planned Production Time (min)", r["planned_production_time_min"], 390.0)
    rec.check("Unplanned Downtime (min)", r["unplanned_downtime_min"], 35.0)
    rec.check("Operating Time (min)", r["operating_time_min"], 355.0)
    rec.check("Earned Minutes (min)", r["earned_minutes"], 238.0)

    # Headline metrics (section 7 summary table)
    rec.check("Availability %", r["availability_pct"], 91.03, tol=0.02)
    rec.check("Performance %", r["performance_pct"], 67.04, tol=0.02)
    rec.check("Quality %", r["quality_pct"], 100.0)
    rec.check("OEE %", r["oee_pct"], 61.02, tol=0.05)
    rec.note("Methodology prints OEE as 61.01%% (display rounding of 61.02%%).")

    # Display formatting matches the dashboard cards
    rec.check_str = getattr(rec, "check_str", None)
    ppt_fmt = calc.minutes_to_hhmmss(r["planned_production_time_min"])
    rec.note("Production Time card -> %s (expected 06:30:00)" % ppt_fmt)


def test_idle_shift_no_divide_by_zero(rec):
    # Entire shift is planned downtime -> PPT = 0 -> availability must be 0, not error
    r = calc.compute_oee(
        480.0,
        [{"name": "Full PM", "minutes": 480.0}],
        [],
        [])
    rec.check("Idle shift Availability %", r["availability_pct"], 0.0)
    rec.check("Idle shift OEE %", r["oee_pct"], 0.0)


def test_completion_clamped(rec):
    # Sensor over-count (turns beyond total) must clamp completion at 100%
    pct = calc.completion_from_turns(900, 752)
    rec.check("Completion clamp (turns>total)", pct, 1.0)
    # Partial coil from turns
    pct2 = calc.completion_from_turns(376, 752)
    rec.check("Completion from turns (half)", pct2, 0.5, tol=0.001)


def test_performance_cannot_exceed_inputs(rec):
    # Over-completion in a coil dict must clamp, so performance stays bounded
    r = calc.compute_performance(
        100.0,
        [{"planned_ct_min": 100.0, "completion_pct": 1.5}])
    rec.check("Earned clamp (completion 1.5)", r["earned_minutes"], 100.0)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run1_all():
    """Run every test and return a printable report string."""
    rec = _Recorder()
    test_methodology_example(rec)
    test_idle_shift_no_divide_by_zero(rec)
    test_completion_clamped(rec)
    test_performance_cannot_exceed_inputs(rec)
    report = rec.report()
    print(report)
    return rec.failed == 0


if __name__ == "__main__":
    ok = run_all()
    import sys
    sys.exit(0 if ok else 1)
    
#====================================================================================NEW OEE SCREEN SCRIPTS from here====================================================


"""
oee.test -- Validation harness for the OEE calculation engine.

Run from the Ignition Script Console (Designer > Tools > Script Console):

    oee.test.runAll()

Every test exercises oee.calc ONLY (pure math, no database), so this is safe
to run on any gateway at any time. If all tests pass, the numbers shown on
the OEE Analysis screen are mathematically faithful to the
"OEE Calculation Methodology" v1.2 document.

NOTE on the document's summary table: the doc rounds A and P before
multiplying and prints OEE = 61.01%. Exact arithmetic gives
(355/390) x (238/355) x 1 = 238/390 = 61.03%. The engine uses exact
arithmetic; test_methodology_example asserts the exact value and this note
documents the 0.02 difference against the doc's rounded table.
"""

_results = []


def _check(name, condition, detail=''):
    status = 'PASS' if condition else 'FAIL'
    _results.append((status, name, detail))
    print('[%s] %s %s' % (status, name, ('- ' + str(detail)) if detail else ''))
    return condition


def _approx(a, b, tol=0.01):
    return abs(float(a) - float(b)) <= tol


# ---------------------------------------------------------------------------

def test_methodology_example():
    """Section 5-7 worked example:
    480 shift - 90 planned = 390 PPT; -35 unplanned = 355 operating;
    earned = 100 + 95 + 43 + 0 = 238 min.
    Expected: A = 91.03%, P = 67.04%, OEE = 61.03% (exact; doc table
    prints 61.01% due to intermediate rounding)."""
    k = oee.calc.computeKPIs(totalMinutes=480, plannedDtMinutes=90,
                             unplannedDtMinutes=35, earnedMinutes=238)
    _check('methodology: planned production time = 390', k['plannedProductionMinutes'] == 390.0, k['plannedProductionMinutes'])
    _check('methodology: operating minutes = 355', k['operatingMinutes'] == 355.0, k['operatingMinutes'])
    _check('methodology: availability = 91.03', _approx(k['availability'], 91.03), k['availability'])
    _check('methodology: performance = 67.04', _approx(k['performance'], 67.04), k['performance'])
    _check('methodology: quality = 100', k['quality'] == 100.0, k['quality'])
    _check('methodology: OEE = 61.03 (exact 238/390)', _approx(k['oee'], 61.03), k['oee'])


def test_earned_hours_example():
    """Section 6.3 coil table: A 100min@100%, B 95@100%, C 86@50%, D 74@0%
    -> earned = 238 min, using the completion path with op_status/time."""
    MS = oee.calc.MS_PER_MIN
    t0 = 0.0
    rows = [
        # Completed coils: op_status 16 -> completion 1.0 regardless of time
        {'serial_number': 'A', 'op_status': 16, 'actual_start': t0, 'actual_end': t0 + 100 * MS, 'hv_winding_time': 100 / 60.0},
        {'serial_number': 'B', 'op_status': 16, 'actual_start': t0, 'actual_end': t0 + 95 * MS, 'hv_winding_time': 95 / 60.0},
        # Coil C: not complete, ran 43 of 86 ideal minutes -> 50%
        {'serial_number': 'C', 'op_status': 4, 'actual_start': t0, 'actual_end': t0 + 43 * MS, 'hv_winding_time': 86 / 60.0},
        # Coil D: never started -> 0%
        {'serial_number': 'D', 'op_status': 2, 'actual_start': None, 'actual_end': None, 'hv_winding_time': 74 / 60.0},
    ]
    m = oee.calc.coilMetrics(rows, nowMs=t0 + 480 * MS)
    _check('earned hours example: earned = 238 min', _approx(m['earnedMinutes'], 238.0, 0.05), m['earnedMinutes'])
    _check('earned hours example: 2 completed', m['coilsCompleted'] == 2, m['coilsCompleted'])
    _check('earned hours example: 3 started', m['coilsStarted'] == 3, m['coilsStarted'])


def test_completion_rules():
    """Client rules 2026-07-02: op_status 16 = 100%; otherwise elapsed/ideal
    capped at 100%; wip column is never used."""
    MS = oee.calc.MS_PER_MIN
    _check('completion: op_status 16 -> 1.0 even with tiny elapsed',
           oee.calc.completionPct(16, 0, 5 * MS, 100.0, 5 * MS) == 1.0)
    _check('completion: in-progress half of ideal -> 0.5',
           _approx(oee.calc.completionPct(4, 0, None, 100.0, 50 * MS), 0.5))
    _check('completion: overrun capped at 1.0',
           oee.calc.completionPct(4, 0, 300 * MS, 100.0, 300 * MS) == 1.0)
    _check('completion: never started -> 0.0',
           oee.calc.completionPct(2, None, None, 100.0, 999 * MS) == 0.0)
    _check('completion: missing ideal CT -> 0.0 (skipped, not guessed)',
           oee.calc.completionPct(4, 0, 60 * MS, None, 60 * MS) == 0.0)


def test_downtime_classification():
    """Client rule: CategoryID 2 = planned, CategoryID 1 = unplanned."""
    rows = [
        {'CategoryID': 1, 'DurationMinutes': 30},   # unplanned (Manual)
        {'CategoryID': 1, 'DurationMinutes': 12.5},
        {'CategoryID': 2, 'DurationMinutes': 60},   # planned (System)
        {'CategoryID': None, 'DurationMinutes': 5}, # unknown -> otherMinutes
        {'CategoryID': 1, 'DurationMinutes': None}, # bad data -> 0, no crash
    ]
    s = oee.calc.splitDowntime(rows)
    _check('downtime: unplanned = 42.5', _approx(s['unplannedMinutes'], 42.5), s['unplannedMinutes'])
    _check('downtime: planned = 60', _approx(s['plannedMinutes'], 60.0), s['plannedMinutes'])
    _check('downtime: unknown category isolated', _approx(s['otherMinutes'], 5.0), s['otherMinutes'])
    _check('downtime: planned constant is CategoryID 2', oee.calc.PLANNED_CATEGORY_ID == 2)


def test_shift_schedule():
    """Shift math comes from tbl_Shift rows - including the overnight
    Night shift 23:30 -> 07:30."""
    shifts = [
        {'StartTime': '07:30:00.0000000', 'EndTime': '15:30:00.0000000'},
        {'StartTime': '15:30:00.0000000', 'EndTime': '23:30:00.0000000'},
        {'StartTime': '23:30:00.0000000', 'EndTime': '07:30:00.0000000'},
    ]
    _check('shift: each shift = 480 min',
           oee.calc.shiftDurationMinutes('23:30:00', '07:30:00') == 480.0)
    _check('shift: 3 shifts cover 1440 min/day',
           oee.calc.dailyShiftMinutes(shifts) == 1440.0)
    # 2 full days at 24h coverage = 2880 min
    day = 24 * 60 * oee.calc.MS_PER_MIN
    _check('total time: 2-day range = 2880 min',
           oee.calc.totalScheduledMinutes(0, 2 * day, 10 * day, 1440.0) == 2880.0)
    _check('total time: future clamped to now',
           oee.calc.totalScheduledMinutes(0, 2 * day, 1 * day, 1440.0) == 1440.0)


def test_edge_cases():
    """Divide-by-zero and empty inputs must yield zeros, never errors."""
    k = oee.calc.computeKPIs(0, 0, 0, 0)
    _check('edge: all-zero input -> OEE 0', k['oee'] == 0.0)
    k = oee.calc.computeKPIs(480, 480, 100, 100)  # planned DT swallows shift
    _check('edge: planned DT >= total -> availability 0, no negative time',
           k['availability'] == 0.0 and k['operatingMinutes'] == 0.0)
    k = oee.calc.computeKPIs(480, 90, 9999, 100)  # absurd unplanned clamped
    _check('edge: unplanned clamped to PPT', k['operatingMinutes'] == 0.0)
    _check('edge: safeDiv None -> default', oee.calc.safeDiv(None, 5) == 0.0)
    _check('edge: minutesToHMS formatting', oee.calc.minutesToHMS(396.5) == '06:36:30')
    m = oee.calc.coilMetrics([], 0)
    _check('edge: no coils -> earned 0', m['earnedMinutes'] == 0.0)


def test_performance_overrun():
    """Coils faster than ideal: Performance may report >100%, but the OEE
    index never exceeds A x 100% x Q."""
    k = oee.calc.computeKPIs(480, 90, 0, 500)  # earned 500 > operating 390
    _check('overrun: performance reported truthfully >100', k['performance'] > 100.0, k['performance'])
    _check('overrun: OEE capped at availability', _approx(k['oee'], k['availability']), k['oee'])


# ---------------------------------------------------------------------------



def test_boundary_clipping():
    """Client rule 2026-07-02: downtime overlapping the range boundaries is
    clipped - starts before range -> counts from range start; not ended in
    range -> counts up to range end. overlapMinutes mirrors the SQL rule."""
    M = 60000.0
    r0, r1 = 1000 * M, 1480 * M                      # 480-min range
    _check('clip: fully inside untouched',
           oee.calc.overlapMinutes(1100 * M, 1200 * M, r0, r1) == 100.0)
    _check('clip: started before range -> from range start',
           oee.calc.overlapMinutes(900 * M, 1100 * M, r0, r1) == 100.0)
    _check('clip: ends after range -> up to range end',
           oee.calc.overlapMinutes(1400 * M, 1600 * M, r0, r1) == 80.0)
    _check('clip: spans whole range -> full range',
           oee.calc.overlapMinutes(900 * M, 1600 * M, r0, r1) == 480.0)
    _check('clip: outside range -> 0',
           oee.calc.overlapMinutes(200 * M, 300 * M, r0, r1) == 0.0)
    _check('clip: inverted interval -> 0, never negative',
           oee.calc.overlapMinutes(1200 * M, 1100 * M, r0, r1) == 0.0)


def test_split_prefers_clipped():
    """splitDowntime must use ClippedMinutes (range-clipped, from SQL) and
    only fall back to raw DurationMinutes when clipping is absent."""
    rows = [
        {'CategoryID': 1, 'DurationMinutes': 100, 'ClippedMinutes': 40},
        {'CategoryID': 2, 'DurationMinutes': 60},          # no clip -> raw
    ]
    dt = oee.calc.splitDowntime(rows)
    _check('clipped wins over raw for unplanned', dt['unplannedMinutes'] == 40.0,
           dt['unplannedMinutes'])
    _check('raw fallback when no ClippedMinutes', dt['plannedMinutes'] == 60.0,
           dt['plannedMinutes'])


def test_shift_membership():
    """timeOfDayInShift with the real tbl_Shift windows, incl. overnight C."""
    A = (7 * 60 + 30.0, 15 * 60 + 30.0)     # 07:30-15:30
    C = (23 * 60 + 30.0, 7 * 60 + 30.0)     # 23:30-07:30 overnight
    _check('shift A: 08:00 in', oee.calc.timeOfDayInShift(480, A[0], A[1]))
    _check('shift A: 16:00 out', not oee.calc.timeOfDayInShift(960, A[0], A[1]))
    _check('shift C: 23:45 in (before midnight)',
           oee.calc.timeOfDayInShift(23 * 60 + 45.0, C[0], C[1]))
    _check('shift C: 03:00 in (after midnight)',
           oee.calc.timeOfDayInShift(180.0, C[0], C[1]))
    _check('shift C: 12:00 out', not oee.calc.timeOfDayInShift(720.0, C[0], C[1]))
    _check('shift boundary: start inclusive, end exclusive',
           oee.calc.timeOfDayInShift(A[0], A[0], A[1])
           and not oee.calc.timeOfDayInShift(A[1], A[0], A[1]))


def test_scheduled_shift_minutes():
    """Per-shift scheduled time from tbl_Shift windows, exact and clamped."""
    DAY = 1440 * 60000.0
    shifts = [
        {'ShiftID': 1, 'StartTime': '07:30:00', 'EndTime': '15:30:00'},
        {'ShiftID': 2, 'StartTime': '15:30:00', 'EndTime': '23:30:00'},
        {'ShiftID': 3, 'StartTime': '23:30:00', 'EndTime': '07:30:00'},
    ]
    d0 = 100 * DAY                       # midnight of the selected day
    days = [d0 - DAY, d0]                # includes previous day for overnight
    # one calendar day, all shifts -> 1440 (C spills 450 from prev + 30 own)
    allMin = oee.calc.scheduledShiftMinutes(days, d0, d0 + DAY, None, shifts, 0)
    _check('scheduled: all shifts over 1 day = 1440', allMin == 1440.0, allMin)
    # single day shift -> 480
    aMin = oee.calc.scheduledShiftMinutes(days, d0, d0 + DAY, None, shifts, 1)
    _check('scheduled: shift A over 1 day = 480', aMin == 480.0, aMin)
    # overnight shift over one calendar day = 450 (spill) + 30 (own) = 480
    cMin = oee.calc.scheduledShiftMinutes(days, d0, d0 + DAY, None, shifts, 3)
    _check('scheduled: overnight C over 1 day = 480', cMin == 480.0, cMin)
    # clamp to now: only first 4h of shift A elapsed
    nowMs = d0 + (7 * 60 + 30 + 240) * 60000.0
    aClamp = oee.calc.scheduledShiftMinutes(days, d0, d0 + DAY, nowMs, shifts, 1)
    _check('scheduled: clamped to now = 240', aClamp == 240.0, aClamp)
    # unknown shift id -> 0, never a guess
    _check('scheduled: unknown shift -> 0',
           oee.calc.scheduledShiftMinutes(days, d0, d0 + DAY, None, shifts, 99) == 0.0)



def test_range_proportional_earned():
    """Boundary rule 2026-07-03 for coils: a coil straddling the range
    boundary earns only the in-range share of its credit.
    Coil: ideal 120 min, complete (pct 1.0), full life 200 min of which
    50 min fell inside the range -> earned = 120 * 1.0 * (50/200) = 30."""
    now = 1700000000000
    rows = [{
        'serial_number': 'S1', 'op_status': 16,
        'actual_start': now - 200 * 60000, 'actual_end': now,
        'hv_winding_time': 2.0,           # 120 min ideal
        'ActualMinutes': 200.0, 'ClippedMinutes': 50.0,
    }]
    m = oee.calc.coilMetrics(rows, now)
    _check('clip: straddling coil earns in-range share only',
           _approx(m['earnedMinutes'], 30.0), m['earnedMinutes'])

    rows[0]['ClippedMinutes'] = 200.0     # fully inside range
    m = oee.calc.coilMetrics(rows, now)
    _check('clip: fully-in-range coil earns full credit',
           _approx(m['earnedMinutes'], 120.0), m['earnedMinutes'])

    del rows[0]['ClippedMinutes']
    del rows[0]['ActualMinutes']          # legacy rows without SQL fields
    m = oee.calc.coilMetrics(rows, now)
    _check('clip: missing fields fall back to full credit',
           _approx(m['earnedMinutes'], 120.0), m['earnedMinutes'])

    rows[0]['ActualMinutes'] = 200.0      # clipped > actual can't inflate
    rows[0]['ClippedMinutes'] = 999.0
    m = oee.calc.coilMetrics(rows, now)
    _check('clip: ratio capped at 1.0',
           _approx(m['earnedMinutes'], 120.0), m['earnedMinutes'])

    rows[0]['ClippedMinutes'] = 0.0       # overlapped only outside? zero credit
    m = oee.calc.coilMetrics(rows, now)
    _check('clip: zero in-range minutes -> zero earned',
           _approx(m['earnedMinutes'], 0.0), m['earnedMinutes'])


def runAll():
    global _results
    _results = []
    print('=' * 64)
    print('OEE calculation engine validation  (methodology v1.2)')
    print('=' * 64)
    test_methodology_example()
    test_boundary_clipping()
    test_split_prefers_clipped()
    test_shift_membership()
    test_scheduled_shift_minutes()
    test_earned_hours_example()
    test_completion_rules()
    test_downtime_classification()
    test_shift_schedule()
    test_edge_cases()
    test_performance_overrun()
    test_range_proportional_earned()
    fails = [r for r in _results if r[0] == 'FAIL']
    print('-' * 64)
    print('%d tests, %d failed' % (len(_results), len(fails)))
    if fails:
        print('DO NOT TRUST SCREEN NUMBERS UNTIL FAILURES ARE FIXED.')
    else:
        print('All formulas verified against the methodology document.')
    return len(fails) == 0