
# TOP FRAMES (3PHTFR)


# CONFIG

TOPFRAMES_NQ_PATH   = "Top Frames"               # Named Query for Top Frames
PIRMADA_TAG_PATH    = "[default]Sec211/Hervoss/DataAutomation/Pirmada Inputs"  # Coil master dataset tag
PRIOR_TFR_TAG_PATH  = "[default]Sec211/Hervoss/DataAutomation/TFR"             # Yesterday's output (for slack calc)
OUT_TAG_PATH        = "[default]Sec211/Hervoss/DataAutomation/TFR"             # Today's output

# Tolerances & matching behavior
THICKNESS_TOL        = 0.02
WIDTH_TOL            = 0.02
REQUIRE_LENGTH_CHECK = False

FORCED_BP_COIL_ID    = "10702BMXU0"

OPTIMIZE_WIDTH_NESTING        = True
EDGE_TRIM_IN                  = 0.00
SLIT_KERF_IN                  = 0.00
ALLOW_DOWNGAUGE_WITHIN_TOL    = True

APPLY_PRIOR_DAY_ADJUSTMENT    = True

DEFAULT_CURRENT_OPERATION     = "Herr Voss"  # per your TOPFRAME mapping

# Final column order
TARGET_OUTPUT_COLUMNS = [
    "Current Operation","Order","Left","Make","Cogi","Item","Priority",
    "Level","Status","Materials","Routing","Child","All Triggers",
    "First Operation","Feedback on First Operation pct","Last Feedback",
    "ExpeditedBy",
    "Materials_Clean","Matched_Raw_Coil","Matched_Lanes_Across",
    "Matched_Width_Waste_in","Matched_Width_Utilization","Match_Why",
    "Match_Status",
]


# ALIASES

ALIASES_TFR = {
    "Child":           ["Child"],
    "Make":            ["Make"],
    "Routing":         ["Routing"],
    "FirstOperation":  ["First Operation","FirstOperation","First_Operation"],
    "Item":            ["Item","BlankId","Blank ID","Part"],
    "Left":            ["Left","Qty","Quantity","Count","HH_Qnty"],
}

# Pirmada Inputs tag
ALIASES_COILS = {
    "CoilID":   ["Part ID","Coil ID","CoilID","Item"],
    "Material": ["Material"],
    "Thk":      ["Thickness (IN)","Thickness in","Thickness"],
    "Wid":      ["Width (IN)","Width in","Width"],
    "AvailLen": ["Available Length at Maximum (IN)","Avail Length (IN)","Coil Available Length (IN)"], # optional
}


# MATERIAL MAPS 

MATERIAL_THICKNESS = {
    "11": ("Mild Steel", 0.075), "12": ("Mild Steel", 0.090),
    "13": ("Mild Steel", 0.105), "14": ("Mild Steel", 0.120),
    "15": ("Mild Steel", 0.180), "72": ("Mild Steel", 0.090),
    "Q1": ("304L SST", 0.075),   "Q2": ("304L SST", 0.090),
    "Q3": ("304L SST", 0.105),   "Q4": ("304L SST", 0.120),
    "Q5": ("304L SST", 0.180),
    "B2": ("400 HP Stainless", 0.090), "B3": ("400 HP Stainless", 0.105),
    "B4": ("400 HP Stainless", 0.120), "BP": ("400 HP Stainless", 0.135),
}
DECIMAL_SUFFIX  = {"A":0.05,"B":0.15,"C":0.25,"D":0.35,"G":0.45,"H":0.55,"J":0.65,"P":0.75,"T":0.85,"R":0.95}
HUNDREDS_PREFIX = {"A":100.0,"B":110.0,"C":120.0,"D":130.0,"G":140.0}


# UTILITIES

def _norm(s):
    return ("" if s is None else str(s)).strip()

def _key_upper(s):
    return _norm(s).upper()

def _resolve_col(existing, aliases):
    lower = {n.lower().strip(): n for n in existing}
    for a in aliases:
        hit = lower.get(a.lower().strip())
        if hit:
            return hit
    return None

def _ds_to_rows(ds):
    headers = list(ds.getColumnNames())
    pds = system.dataset.toPyDataSet(ds)
    rows = []
    for r in pds:
        d = {}
        for i,h in enumerate(headers):
            d[h] = r[i]
        rows.append(d)
    return headers, rows

def _to_dataset(headers, rows_list):
    return system.dataset.toDataSet(headers, rows_list)

# parsing 
def _decode_dim_chunk(chunk):
    c = _key_upper(chunk)
    if len(c) != 3: raise ValueError("Chunk must be 3 chars: '%s'"%c)
    if c[0].isalpha() and c[1].isdigit() and c[2].isalpha():
        return HUNDREDS_PREFIX[c[0]] + int(c[1]) + DECIMAL_SUFFIX[c[2]]
    if c[0].isalpha() and c[1:].isdigit():
        return HUNDREDS_PREFIX[c[0]] + (int(c[1:]) / 10.0)
    if c[:2].isdigit() and c[2].isalpha():
        return (int(c[:2]) / 10.0) + DECIMAL_SUFFIX[c[2]]
    if c.isdigit():
        return int(c) / 10.0
    raise ValueError("Invalid chunk: %s"%c)

def parse_functional_part_id(pid):
    s = _key_upper(pid)
    if len(s) < 8 or "H" not in s or "A" not in s:
        return None,None,None,"FORMAT_NOT_MATCHED"
    prefix = s[:2]
    if prefix not in MATERIAL_THICKNESS:
        return None,None,None,"UNKNOWN_PREFIX:%s"%prefix
    family, nominal_t = MATERIAL_THICKNESS[prefix]
    try:
        h = s.find("H"); a = s.find("A", h+1)
        len_chunk = s[h+1:h+4]; wid_chunk = s[a+1:a+4]
        length_in = _decode_dim_chunk(len_chunk)
        width_in  = _decode_dim_chunk(wid_chunk)
    except Exception, ex:
        return family, nominal_t, None, "DIM_PARSE_ERROR:%s"%ex
    return family, nominal_t, (length_in, width_in), "OK"

def normalize_family(material):
    s = _key_upper(material)
    if "304L" in s: return "304L SST"
    if "409HP" in s or "400HP" in s or "400 HP" in s: return "400 HP Stainless"
    if s.startswith("10101CK") or "CARB" in s: return "Mild Steel"
    return material

# pack multiple by suffix -- this is built to mimic SAP lot sizing and yields. This needs work. 
def _pack_multiple_from_suffix(mc):
    # ...073 → 9 ; ...292 → 4 ; else 1
    s = _key_upper(mc)
    if s.endswith("073"): return 9
    if s.endswith("292"): return 4
    return 1

def _round_up_to_multiple(qty, multiple):
    try:
        q = float(qty)
    except:
        return 0.0
    if multiple <= 1: return float(q)
    return float(int((q + multiple - 1) // multiple) * multiple)

# prior-day slack -- schedule is doing what SAP should be doing, verifying prior production in order to gen orders correctly. 
def _apply_prior_day_adjustment(today_rows, prior_rows):
    """
    For each Materials_Clean, get its pack multiple (by suffix),
    subtract yesterday's slack, then round remainder to pack.
    If no prior slack exists, use rounded(today) - prior made.
    """
    if not today_rows: return []

    # Sum prior "made" and "slack" from Materials_Clean
    prior_made, prior_slack = {}, {}
    for d in prior_rows or []:
        key = _norm(d.get("Materials_Clean"))
        if not key: continue
        try: prior_made[key] = prior_made.get(key,0.0) + float(d.get("Left") or 0)
        except: pass
        try: prior_slack[key] = prior_slack.get(key,0.0) + float(d.get("Trace_Slack_EndOfDay") or 0)
        except: pass

    out = []
    had_slack = bool(prior_slack)
    for r in today_rows:
        raw_today = float(r.get("Left") or 0.0)
        key = _norm(r.get("Materials_Clean"))
        m = int(_pack_multiple_from_suffix(key))  # per-item pack multiple by size
        prev_made = float(prior_made.get(key, 0.0))
        prev_sl   = float(prior_slack.get(key, 0.0))

        if had_slack:
            remainder = max(raw_today - prev_sl, 0.0)
            inc_make  = _round_up_to_multiple(remainder, m)
        else:
            inc_make  = max(_round_up_to_multiple(raw_today, m) - prev_made, 0.0)

        slack_end = max(prev_sl + inc_make - raw_today, 0.0)
        slack_keep = (slack_end % m) if m > 1 else 0.0

        nr = dict(r)
        nr["Trace_Today_Raw"]        = raw_today
        nr["Trace_Pack_Multiple"]    = m
        nr["Trace_Prior_Made"]       = prev_made
        nr["Trace_Prev_Slack"]       = prev_sl
        nr["Trace_Incremental_Make"] = inc_make
        nr["Trace_Slack_EndOfDay"]   = slack_keep
        nr["Left"]                   = inc_make
        out.append(nr)

    # keep only rows with make > 0 elim not needed items 
    out = [r for r in out if float(r.get("Left") or 0) > 0]
    # ensure traces exist
    traces = ["Trace_Today_Raw","Trace_Pack_Multiple","Trace_Prior_Made",
              "Trace_Prev_Slack","Trace_Incremental_Make","Trace_Slack_EndOfDay"]
    for r in out:
        for t in traces:
            if t not in r: r[t] = 0.0
    return out

#  matching helpers 
def _thickness_ok(coil_thk, t_nom, tol):
    if coil_thk is None or t_nom is None: return False
    diff = abs(coil_thk - t_nom)
    if ALLOW_DOWNGAUGE_WITHIN_TOL:
        return diff <= tol
    return (coil_thk >= t_nom) and (diff <= tol)

def _compute_nesting(part_wid, coil_wid):
    try:
        pw = float(part_wid); cw = float(coil_wid)
    except:
        return 0, 0.0, 0.0, 0.0
    net = cw - 2.0*EDGE_TRIM_IN
    if net <= 0 or pw <= 0: return 0, max(net,0), 0.0, 0.0
    step = pw + SLIT_KERF_IN
    if step <= 0: return 0, net, 0.0, 0.0
    pieces = int((net + 1e-9) // step)
    used   = pieces*pw + max(pieces-1,0)*SLIT_KERF_IN
    waste  = max(net - used, 0.0)
    util   = (used/net) if net > 0 else 0.0
    return pieces, net, waste, util


# MAIN

def main():
    log = system.util.getLogger("3PHTFR")

    # 1) Read "Top Frames" Named Query 
    tfr_ds = system.db.runNamedQuery(TOPFRAMES_NQ_PATH)   # NQ call
    try: tfr_ds = system.dataset.toDataSet(tfr_ds)        # normalize
    except: pass
    t_headers, t_rows = _ds_to_rows(tfr_ds)               # dataset
    

    # Resolve columns 
    colChild  = _resolve_col(t_headers, ALIASES_TFR["Child"])          or (t_headers[1] if len(t_headers)>1 else None)
    colMake   = _resolve_col(t_headers, ALIASES_TFR["Make"])           or (t_headers[2] if len(t_headers)>2 else None)
    colRoute  = _resolve_col(t_headers, ALIASES_TFR["Routing"])        or (t_headers[3] if len(t_headers)>3 else None)
    colFirst  = _resolve_col(t_headers, ALIASES_TFR["FirstOperation"]) or (t_headers[4] if len(t_headers)>4 else None)
    colItem   = _resolve_col(t_headers, ALIASES_TFR["Item"])           or (t_headers[5] if len(t_headers)>5 else None)
    colLeft   = _resolve_col(t_headers, ALIASES_TFR["Left"])           or (t_headers[7] if len(t_headers)>7 else None)

    if any(c is None for c in [colChild,colMake,colRoute,colFirst,colItem,colLeft]):
        raise ValueError("Top Frames NQ missing required columns (Child/Make/Routing/First/Item/Left). Found: %r" % (t_headers,))

    # 2) Map to base rows 
    base = []
    for d in t_rows:
        try: left_val = float(d.get(colLeft) or 0)
        except: left_val = 0.0
        r = {
            "Current Operation": DEFAULT_CURRENT_OPERATION,  # "Herr Voss"
            "Order": "", "Left": left_val, "Make": _norm(d.get(colMake)),
            "Cogi": "", "Item": _norm(d.get(colItem)), "Priority": "",
            "Level": "", "Status": "", "Materials": "", "Routing": _norm(d.get(colRoute)),
            "Child": _norm(d.get(colChild)), "All Triggers": "",
            "First Operation": _norm(d.get(colFirst)),
            "Feedback on First Operation pct": "", "Last Feedback": "",
            "ExpeditedBy": "",
        }
        base.append(r)

    # 3) Group by Item; sum Left
    grouped, seq = {}, []
    for r in base:
        k = r["Item"]
        if k not in grouped:
            grouped[k] = dict(r); seq.append(k)
        else:
            grouped[k]["Left"] = float(grouped[k]["Left"]) + float(r["Left"])
    rows = [grouped[k] for k in seq]

    # 4) Materials_Clean from Item
    for r in rows:
        r["Materials_Clean"] = _key_upper(r["Item"])[:10]

    # 5) Prior-day slack
    if APPLY_PRIOR_DAY_ADJUSTMENT:
        prior_val = system.tag.readBlocking([PRIOR_TFR_TAG_PATH])[0].value
        prior_headers, prior_rows = ([], [])
        if prior_val:
            prior_headers, prior_rows = _ds_to_rows(prior_val)
        rows = _apply_prior_day_adjustment(rows, prior_rows)

    if not rows:
        empty_cols = TARGET_OUTPUT_COLUMNS + [
            "Trace_Today_Raw","Trace_Pack_Multiple","Trace_Prior_Made",
            "Trace_Prev_Slack","Trace_Incremental_Make","Trace_Slack_EndOfDay"
        ]
        system.tag.writeBlocking([OUT_TAG_PATH], [_to_dataset(empty_cols, [])])
        log.info("3PHTFR: No incremental demand. Wrote empty dataset.")
        return

    # 6) Load Pirmada Inputs 
    coils_ds = system.tag.readBlocking([PIRMADA_TAG_PATH])[0].value
    if coils_ds is None:
        raise ValueError("Pirmada Inputs tag returned None")
    c_headers, c_rows = _ds_to_rows(coils_ds)

    c_id  = _resolve_col(c_headers, ALIASES_COILS["CoilID"])
    c_mat = _resolve_col(c_headers, ALIASES_COILS["Material"])
    c_thk = _resolve_col(c_headers, ALIASES_COILS["Thk"])
    c_wid = _resolve_col(c_headers, ALIASES_COILS["Wid"])
    c_len = _resolve_col(c_headers, ALIASES_COILS["AvailLen"])  # optional

    if not (c_id and c_mat and c_thk and c_wid):
        raise ValueError("Pirmada Inputs missing CoilID/Material/Thickness/Width. Found: %r" % c_headers)

    coil_list = []
    for d in c_rows:
        try: thk = float(d.get(c_thk)) if d.get(c_thk) is not None else None
        except: thk = None
        try: wid = float(d.get(c_wid)) if d.get(c_wid) is not None else None
        except: wid = None
        coil_list.append({
            "Coil_ID": _norm(d.get(c_id)),
            "Family":  normalize_family(d.get(c_mat)),
            "Thk":     thk,
            "Wid":     wid,
            "AvailLen": d.get(c_len) if c_len else None
        })

    # 7) Coil matching BP forced + nesting 
    for r in rows:
        func = r["Materials_Clean"]
        fam, tnom, lw, status = parse_functional_part_id(func)
        r["Match_Status"] = status if status != "OK" else "NO_MATCH"
        r["Matched_Raw_Coil"] = None
        r["Matched_Lanes_Across"] = None
        r["Matched_Width_Waste_in"] = None
        r["Matched_Width_Utilization"] = None
        r["Match_Why"] = None

        if status != "OK" or lw is None:
            continue

        part_len, part_wid = lw

        # Forced BP
        if func.startswith("BP"):
            for c in coil_list:
                if c["Coil_ID"] == FORCED_BP_COIL_ID:
                    r["Matched_Raw_Coil"] = c["Coil_ID"]
                    pcs, net, waste, util = _compute_nesting(part_wid, c["Wid"])
                    r["Matched_Lanes_Across"]      = pcs
                    r["Matched_Width_Waste_in"]    = waste
                    r["Matched_Width_Utilization"] = util
                    r["Match_Why"] = "FORCED_BP_OVERRIDE"
                    r["Match_Status"] = "MATCHED_FORCED"
                    break
            if r["Matched_Raw_Coil"]:
                continue

        # Build list
        candidates = []
        for c in coil_list:
            if c["Family"] != fam or c["Thk"] is None or c["Wid"] is None:
                continue
            if not _thickness_ok(c["Thk"], float(tnom), THICKNESS_TOL):
                continue
            if c["Wid"] < (float(part_wid) - WIDTH_TOL):
                continue
            if REQUIRE_LENGTH_CHECK and c["AvailLen"] is not None and part_len is not None:
                try:
                    if float(c["AvailLen"]) < float(part_len): continue
                except: pass

            pcs, net, waste, util = _compute_nesting(part_wid, c["Wid"])
            if OPTIMIZE_WIDTH_NESTING and pcs < 1: 
                continue
            thk_diff = abs(c["Thk"] - float(tnom))
            wid_diff = abs(c["Wid"] - float(part_wid))
            score = (-pcs, waste, thk_diff, wid_diff) if OPTIMIZE_WIDTH_NESTING else (thk_diff, wid_diff)
            candidates.append((score, c, pcs, waste, util))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            _, c, pcs, waste, util = candidates[0]
            r["Matched_Raw_Coil"]         = c["Coil_ID"]
            r["Matched_Lanes_Across"]     = pcs
            r["Matched_Width_Waste_in"]   = waste
            r["Matched_Width_Utilization"]= util
            r["Match_Why"]                = ("OPTIMIZED_BY_LANES>WASTE>THKDIFF>WIDTHDIFF"
                                             if OPTIMIZE_WIDTH_NESTING else
                                             "LEGACY_MIN_THKDIFF_THEN_MIN_WIDTHDIFF")
            r["Match_Status"]             = "MATCHED"
        else:
            r["Match_Status"]             = "NO_MATCH"

    # 8) Build final 
    for col in TARGET_OUTPUT_COLUMNS:
        for r in rows:
            if col not in r: r[col] = ""

    trace_cols = ["Trace_Today_Raw","Trace_Pack_Multiple","Trace_Prior_Made",
                  "Trace_Prev_Slack","Trace_Incremental_Make","Trace_Slack_EndOfDay"]
    all_keys = set()
    for r in rows: all_keys.update(r.keys())
    trailing = [c for c in list(all_keys) if c not in TARGET_OUTPUT_COLUMNS]
    trailing_ordered = [c for c in trace_cols if c in trailing] + [c for c in trailing if c not in trace_cols]

    headers = TARGET_OUTPUT_COLUMNS + trailing_ordered
    out_rows = [[r.get(h,"") for h in headers] for r in rows]

    out_ds = _to_dataset(headers, out_rows)
    system.tag.writeBlocking([OUT_TAG_PATH], [out_ds])
    log.info("3PHTFR: wrote %d rows to %s" % (len(rows), OUT_TAG_PATH))

# Execute
main()