# 3ph tank logic 
N_OLDEST_SERIALS          = 85
OUTPUT_ONLY_POSITIVE_NEED = True

# Named Queries
BLANKS_NQ_PATH = "3PH Tank Schedule"
TOWER_NQ_PATH  = "Tower"

# Tags
STACK_TAG_PATH = "[default]Sec211/Hervoss/DataAutomation/Piranha Blanks"  # replaces STACK 
OUT_TAG_PATH   = "[default]Sec211/Hervoss/DataAutomation/3PHBLANK"        # output dataset

# column identifier
ALIASES_BLANKS = {
    # Serial
    "Serial":   ["Serial No", "Serial", "Serial_Number", "SerialNo", "SN"],
    # Date
    "Date":     ["Schedule Date", "Date", "SchedDate", "ScheduleDate"],
    # Part ID
    "PartID":   ["Blank ID", "BlankId", "BlankID", "PartID", "Part", "Blank"],
    # Raw Coil / Coil ID
    "RawCoil":  ["Coil ID", "Raw Coil", "RawCoil", "Coil"],
}

# Tower 
ALIASES_TOWER = {
    # Part ID / Blank ID
    "PartID":   ["Blank ID", "BlankId", "BlankID", "PartID", "Part", "Blank"],
    # Quantity
    "Qty":      ["Quantity", "Qty", "QTY", "OnHand", "On Hand"],
    # Location as Pallet/Bin code in Tower to show if there are too many racks already allocated
    "Location": ["Pallet Code", "Location", "Loc", "Bin", "Warehouse", "LOC"],

}

ALIASES_STACK = {
    "BlankID":  ["BlankID", "Blank Id", "Blank ID", "BlankId", "PartID", "Part"],
    "RawCoil":  ["Raw Coil", "RawCoil", "Coil", "Coil ID"],
    "MaxStack": ["MaxStack", "Max Stack", "Stack", "StackQty", "Stack Qty"],
}

# Matching tolerances
THICKNESS_TOL        = 0.02
WIDTH_TOL            = 0.02
REQUIRE_LENGTH_CHECK = False
FORCED_BP_COIL_ID    = "10702BMXU0"

#  maps
MATERIAL_THICKNESS = {
    "11": ("Mild Steel", 0.075),
    "12": ("Mild Steel", 0.090),
    "13": ("Mild Steel", 0.105),
    "14": ("Mild Steel", 0.120),
    "15": ("Mild Steel", 0.180),
    "72": ("Mild Steel", 0.090),
    "Q1": ("304L SST", 0.075),
    "Q2": ("304L SST", 0.090),
    "Q3": ("304L SST", 0.105),
    "Q4": ("304L SST", 0.120),
    "Q5": ("304L SST", 0.180),
    "B2": ("400 HP Stainless", 0.090),
    "B3": ("400 HP Stainless", 0.105),
    "B4": ("400 HP Stainless", 0.120),
    "BP": ("400 HP Stainless", 0.135),
}
DECIMAL_SUFFIX  = {"A": 0.05, "B": 0.15, "C": 0.25, "D": 0.35, "G": 0.45, "H": 0.55, "J": 0.65, "P": 0.75, "T": 0.85, "R": 0.95}
HUNDREDS_PREFIX = {"A": 100.0, "B": 110.0, "C": 120.0, "D": 130.0, "G": 140.0}

# transform
def _norm(s):
    return ("" if s is None else str(s)).strip()

def _key_upper(s):
    return _norm(s).upper()

def _resolve_col(existing_names, alias_list):
    """Return the actual column name matching any alias (case-insensitive, trim)."""
    lower = {n.lower().strip(): n for n in existing_names}
    for a in alias_list:
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
        for i, h in enumerate(headers):
            d[h] = r[i]
        rows.append(d)
    return headers, rows

def _to_dataset(headers, rows):
    return system.dataset.toDataSet(headers, rows)

def _to_epoch_ms(v):
    try:
        return v.getTime()  
    except:
        pass
    s = _norm(v)
    if s:
        try:
            return system.date.parse(s)  
        except:
            return 9e18
    return 9e18

# MAIN 
def main():
    log = system.util.getLogger("3PHBLANK")

    # 1) 3PH Tank Schedule
    blanks_raw = system.db.runNamedQuery(BLANKS_NQ_PATH)
    try:
        blanks_raw = system.dataset.toDataSet(blanks_raw)
    except:
        pass
    b_headers, b_rows = _ds_to_rows(blanks_raw)

    b_serial = _resolve_col(b_headers, ALIASES_BLANKS["Serial"])
    b_date   = _resolve_col(b_headers, ALIASES_BLANKS["Date"])
    b_pid    = _resolve_col(b_headers, ALIASES_BLANKS["PartID"])
    b_coil   = _resolve_col(b_headers, ALIASES_BLANKS["RawCoil"])  # optional for demand, used for Raw Coil list

    if not (b_serial and b_date and b_pid):
        raise ValueError("3PH Tank Schedule query must have Serial/Date/PartID aliases. "
                         "Found: %r" % (b_headers,))

    blanks = []
    for d in b_rows:
        serial = _norm(d.get(b_serial))
        datev  = d.get(b_date)
        partid = _norm(d.get(b_pid))
        rawcl  = _norm(d.get(b_coil)) if b_coil else ""
        blanks.append({
            "Serial": serial,
            "Date":   datev,
            "PartID": partid,
            "PartKey": _key_upper(partid),
            "RawCoil": rawcl
        })

    # 2) Oldest N unique serials by Date
    serial_dates = {}
    for r in blanks:
        s = r["Serial"]
        if not s:
            continue
        t = _to_epoch_ms(r["Date"])
        prev = serial_dates.get(s)
        if prev is None or t < prev:
            serial_dates[s] = t
    serial_sorted = sorted(serial_dates.items(), key=lambda kv: (kv[1], kv[0]))
    selected_serials = set([kv[0] for kv in serial_sorted[:N_OLDEST_SERIALS]])

    blanks_sel = [r for r in blanks if r["Serial"] in selected_serials]

    # 3) demand and Raw Coil list
    demand_map = {}      # PartKey 
    rawcoil_map = {}     # PartKey 
    for r in blanks_sel:
        pk = r["PartKey"]
        demand_map[pk] = demand_map.get(pk, 0) + 1
        if r["RawCoil"]:
            s = rawcoil_map.get(pk)
            if s is None:
                s = set()
                rawcoil_map[pk] = s
            s.add(r["RawCoil"])

    # 4) Tower inventory
    tower_raw = system.db.runNamedQuery(TOWER_NQ_PATH)
    try:
        tower_raw = system.dataset.toDataSet(tower_raw)
    except:
        pass
    t_headers, t_rows = _ds_to_rows(tower_raw)

    t_pid = _resolve_col(t_headers, ALIASES_TOWER["PartID"])
    t_qty = _resolve_col(t_headers, ALIASES_TOWER["Qty"])
    t_loc = _resolve_col(t_headers, ALIASES_TOWER["Location"])
    if not (t_pid and t_qty and t_loc):
        raise ValueError("Tower query must have PartID/Qty/Location aliases. Found: %r" % (t_headers,))

    inv_qty_map = {}   # PartKey 
    locs_map    = {}   # PartKey
    for d in t_rows:
        pk = _key_upper(d.get(t_pid))
        try:
            q = float(d.get(t_qty) or 0)
        except:
            q = 0.0
        inv_qty_map[pk] = inv_qty_map.get(pk, 0.0) + q
        loc = _norm(d.get(t_loc))
        if loc:
            s = locs_map.get(pk)
            if s is None:
                s = set()
                locs_map[pk] = s
            s.add(loc)

    # 5) STACK from tag
    stack_ds = system.tag.readBlocking([STACK_TAG_PATH])[0].value
    if stack_ds is None:
        raise ValueError("Tag %s returned None" % STACK_TAG_PATH)
    s_headers, s_rows = _ds_to_rows(stack_ds)

    s_blank = _resolve_col(s_headers, ALIASES_STACK["BlankID"])
    s_mxstk = _resolve_col(s_headers, ALIASES_STACK["MaxStack"])
    if not (s_blank and s_mxstk):
        raise ValueError("Piranha Blanks tag must have BlankID and MaxStack aliases. Found: %r" % (s_headers,))

    maxstack_map = {}  # MaxStack
    for d in s_rows:
        pk = _key_upper(d.get(s_blank))
        try:
            ms = float(d.get(s_mxstk))
        except:
            ms = None
        if pk and ms is not None and ms > 0:
            prev = maxstack_map.get(pk)
            if prev is None or ms > prev:
                maxstack_map[pk] = ms

    # 6) output rows with stack rounding
    out = []
    for pk, demand in demand_map.items():
        inv = inv_qty_map.get(pk, 0.0)
        need = int(demand - inv)
        if OUTPUT_ONLY_POSITIVE_NEED and need <= 0:
            continue

        ms = maxstack_map.get(pk)
        if ms is not None and ms > 0:
            import math
            need = int(math.ceil(float(need) / float(ms)) * float(ms))

        locs  = ", ".join(sorted(locs_map.get(pk, set())))
        coils = ", ".join(sorted(rawcoil_map.get(pk, set())))
        out.append([pk, need, locs, coils])

    out.sort(key=lambda r: r[0])
    headers = ["Part ID", "Needed Quantity", "Locations", "Raw Coil"]
    result_ds = _to_dataset(headers, out)

    # 7) Write to tag
    system.tag.writeBlocking([OUT_TAG_PATH], [result_ds])

    log.info("3PHBLANK: wrote %d rows to %s; selected %d oldest serials"
             % (len(out), OUT_TAG_PATH, len(selected_serials)))

# Execute
main()