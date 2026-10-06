
# CONFIG 

BASING_NQ_PATH   = "Basing"                    # bases stored proc 
PIRMADA_TAG_PATH = "[default]Sec211/Hervoss/DataAutomation/Pirmada Inputs"   # Coil master dataset tag (Pirmada)
OUT_TAG_PATH     = "[default]Sec211/Hervoss/DataAutomation/BASING"           # Output dataset tag

# Tolerances & rules (inches)
THICKNESS_TOL        = 0.02
WIDTH_TOL            = 0.02
REQUIRE_LENGTH_CHECK = False

# Forced & preferred coils
FORCED_BP_COIL_ID   = "10702BMXU0"   # forced when part starts with BP
HARD_PREFER_B2_Y24  = True
PREFER_B2_COIL_ID   = "10702BMY24"   # 409HP 0.090", 48" width
HARD_PREFER_11H_Y63 = True
PREFER_11H_COIL_ID  = "10101CKY63"   # Mild Steel 0.075", ~36.6" width

# Yield optimization
SLIT_KERF_IN = 0.00
EDGE_TRIM_IN = 0.00


# Basing NQ: 2 columns Part Quantity
ALIASES_BASING = {
    "Part":     ["Column1", "part", "Part", "Blank", "Blank ID", "BlankId", "Item"],
    "Quantity": ["Column2", "countPnlDistnct", "Quantity", "Qty", "qty", "Count"],
}
# Pirmada Inputs tag fields
ALIASES_COILS = {
    "CoilID":   ["Part ID", "Coil ID", "CoilID", "Item"],
    "Material": ["Material"],
    "Thk":      ["Thickness (IN)", "Thickness in", "Thickness"],
    "Wid":      ["Width (IN)", "Width in", "Width"],
    "AvailLen": ["Available Length at Maximum (IN)", "Avail Length (IN)", "Coil Available Length (IN)"],  # optional
}


# MATERIAL MAPS 
 
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


# UTIL

def _norm(s):
    return ("" if s is None else str(s)).strip()

def _key_upper(s):
    return _norm(s).upper()

def _resolve_col(existing_names, alias_list):
    """Find first alias present (case-insensitive, trimmed); return actual case-sensitive name."""
    lower = {n.lower().strip(): n for n in existing_names}
    for a in alias_list:
        hit = lower.get(a.lower().strip())
        if hit:
            return hit
    return None

def _ds_to_rows(ds):
    """Dataset -> (headers, list_of_row_dicts)."""
    headers = list(ds.getColumnNames())
    pds = system.dataset.toPyDataSet(ds)
    rows = []
    for r in pds:
        d = {}
        for i, h in enumerate(headers):
            d[h] = r[i]
        rows.append(d)
    return headers, rows

def _to_dataset(headers, rows_of_lists):
    return system.dataset.toDataSet(headers, rows_of_lists)

def _decode_dim_chunk(chunk):
    c = _key_upper(chunk)
    if len(c) != 3:
        raise ValueError("Chunk must be 3 characters: '%s'" % c)
    if c[0].isalpha() and c[1].isdigit() and c[2].isalpha():
        return HUNDREDS_PREFIX[c[0]] + int(c[1]) + DECIMAL_SUFFIX[c[2]]
    if c[0].isalpha() and c[1:].isdigit():
        return HUNDREDS_PREFIX[c[0]] + (int(c[1:]) / 10.0)
    if c[:2].isdigit() and c[2].isalpha():
        return int(c[:2]) + DECIMAL_SUFFIX[c[2]]
    if c.isdigit():
        return int(c) / 10.0
    raise ValueError("Invalid chunk: %s" % c)

def parse_functional_part_id(pid):
    """Parse e.g. '15H47PA260' -> (family, nominal_thk, (length_in, width_in), status)."""
    s = _key_upper(pid)
    if len(s) < 8 or "H" not in s or "A" not in s:
        return None, None, None, "FORMAT_NOT_MATCHED"
    prefix = s[:2]
    if prefix not in MATERIAL_THICKNESS:
        return None, None, None, "UNKNOWN_PREFIX:%s" % prefix
    family, nominal_t = MATERIAL_THICKNESS[prefix]
    try:
        h_idx = s.find("H")
        a_idx = s.find("A", h_idx + 1)
        len_chunk = s[h_idx+1:h_idx+4]
        wid_chunk = s[a_idx+1:a_idx+4]
        length_in = _decode_dim_chunk(len_chunk)
        width_in  = _decode_dim_chunk(wid_chunk)
    except Exception, ex:
        return family, nominal_t, None, "DIM_PARSE_ERROR:%s" % ex
    return (family, nominal_t, (length_in, width_in), "OK")

def normalize_family(material):
    s = _key_upper(material)
    if "304L" in s:
        return "304L SST"
    if "409HP" in s or "400HP" in s or "400 HP" in s:
        return "400 HP Stainless"
    if s.startswith("10101CK") or "CARB" in s:
        return "Mild Steel"
    return material

def compute_pieces_across(coil_width, part_width, kerf=SLIT_KERF_IN, edge_trim=EDGE_TRIM_IN):
    """floor((coil_width - 2*edge_trim) / (part_width + kerf))"""
    try:
        cw = float(coil_width)
        pw = float(part_width)
    except:
        return 0
    if pw <= 0:
        return 0
    w_eff = cw - 2.0*edge_trim
    if w_eff <= 0:
        return 0
    pitch = pw + kerf
    if pitch <= 0:
        return 0
    return int((w_eff + 1e-9) // pitch)


# MAIN

def main():
    log = system.util.getLogger("BASING")

    # 1) Read BASES rows from Named Query "Basing"
    nq = system.db.runNamedQuery(BASING_NQ_PATH)
    try:
        nq = system.dataset.toDataSet(nq)
    except:
        pass
    b_headers, b_rows = _ds_to_rows(nq)

    col_part = _resolve_col(b_headers, ALIASES_BASING["Part"])
    col_qty  = _resolve_col(b_headers, ALIASES_BASING["Quantity"])

    # Fallback for generic  (Column1=Part, Column2=Quantity)
    if not (col_part and col_qty):
        if len(b_headers) == 2:
            col_part, col_qty = b_headers[0], b_headers[1]
        else:
            raise ValueError("Basing query must have Part and Quantity. Found: %r" % (b_headers,))

    log.info("Basing headers=%r, resolved Part=%s, Qty=%s" % (b_headers, col_part, col_qty))

    today = system.date.midnight(system.date.now())  # auto-fill today's date in B
    # Build cols: A=Part (upper/trim), B=Date(today), C=Quantity (int)
    bases_rows = []
    for d in b_rows:
        part = _key_upper(d.get(col_part))
        qty  = d.get(col_qty)
        try:
            qty = int(float(qty or 0))
        except:
            qty = 0
        bases_rows.append([part, today, qty])  # [A, B, C]

    # 2) Read Pirmada Inputs
    coils_ds = system.tag.readBlocking([PIRMADA_TAG_PATH])[0].value
    if coils_ds is None:
        raise ValueError("Tag %s returned None" % PIRMADA_TAG_PATH)
    c_headers, c_rows = _ds_to_rows(coils_ds)

    c_id  = _resolve_col(c_headers, ALIASES_COILS["CoilID"])
    c_mat = _resolve_col(c_headers, ALIASES_COILS["Material"])
    c_thk = _resolve_col(c_headers, ALIASES_COILS["Thk"])
    c_wid = _resolve_col(c_headers, ALIASES_COILS["Wid"])
    c_len = _resolve_col(c_headers, ALIASES_COILS["AvailLen"])  # optional

    if not (c_id and c_mat and c_thk and c_wid):
        raise ValueError("Pirmada Inputs missing required columns. Found: %r" % (c_headers,))

    log.info("Pirmada Inputs headers=%r, resolved CoilID=%s, Thk=%s, Wid=%s, Material=%s"
             % (c_headers, c_id, c_thk, c_wid, c_mat))

    # coil 
    coil_list = []
    for d in c_rows:
        try:
            thk = float(d.get(c_thk)) if d.get(c_thk) is not None else None
        except:
            thk = None
        try:
            wid = float(d.get(c_wid)) if d.get(c_wid) is not None else None
        except:
            wid = None
        coil_list.append({
            "Coil_ID": _norm(d.get(c_id)),
            "Family":  normalize_family(d.get(c_mat)),
            "Thk":     thk,
            "Wid":     wid,
            "AvailLen": d.get(c_len) if c_len else None
        })

    # 3) Matching
    out_rows = []
    for A, B, C in bases_rows:
        fam, nominal_t, lw_tuple, status = parse_functional_part_id(A)

        matched = None
        m_fam = m_thk = m_wid = None
        thk_diff = wid_diff = None
        pieces_across = None
        match_status = "PARSE_FAIL"

        if status == "OK" and lw_tuple is not None:
            length_in, width_in = lw_tuple
            match_status = "NO_MATCH"

            # Forced BP
            if A.startswith("BP"):
                for c in coil_list:
                    if c["Coil_ID"] == FORCED_BP_COIL_ID:
                        matched  = c["Coil_ID"]
                        m_fam    = c["Family"]
                        m_thk    = c["Thk"]
                        m_wid    = c["Wid"]
                        thk_diff = abs((m_thk or 0) - float(nominal_t)) if m_thk is not None else None
                        wid_diff = abs((m_wid or 0) - float(width_in)) if m_wid is not None else None
                        pieces_across = compute_pieces_across(m_wid, float(width_in))
                        match_status  = "MATCHED_FORCED"
                        break

            # Hard preference 11H 
            if matched is None and HARD_PREFER_11H_Y63 and A.startswith("11H"):
                pref = [c for c in coil_list if c["Coil_ID"] == PREFER_11H_COIL_ID]
                if pref:
                    c = pref[0]
                    if c["Thk"] is not None and c["Wid"] is not None:
                        tdiff = abs(c["Thk"] - float(nominal_t))
                        w_ok  = c["Wid"] >= (float(width_in) - WIDTH_TOL)
                        if tdiff <= THICKNESS_TOL and w_ok:
                            pa = compute_pieces_across(c["Wid"], float(width_in))
                            if pa >= 1:
                                matched, m_fam, m_thk, m_wid = c["Coil_ID"], c["Family"], c["Thk"], c["Wid"]
                                thk_diff, wid_diff, pieces_across = tdiff, abs(c["Wid"]-float(width_in)), pa
                                match_status = "MATCHED_PREFERRED_11H"

            # Hard preference B2 
            if matched is None and HARD_PREFER_B2_Y24 and A.startswith("B2"):
                pref = [c for c in coil_list if c["Coil_ID"] == PREFER_B2_COIL_ID]
                if pref:
                    c = pref[0]
                    if c["Thk"] is not None and c["Wid"] is not None:
                        tdiff = abs(c["Thk"] - float(nominal_t))
                        w_ok  = c["Wid"] >= (float(width_in) - WIDTH_TOL)
                        if tdiff <= THICKNESS_TOL and w_ok:
                            pa = compute_pieces_across(c["Wid"], float(width_in))
                            if pa >= 1:
                                matched, m_fam, m_thk, m_wid = c["Coil_ID"], c["Family"], c["Thk"], c["Wid"]
                                thk_diff, wid_diff, pieces_across = tdiff, abs(c["Wid"]-float(width_in)), pa
                                match_status = "MATCHED_PREFERRED"

            # Normal selection (best yield, then thickness, wider coil)
            if matched is None:
                candidates = []
                for c in coil_list:
                    if c["Family"] == fam and c["Thk"] is not None and c["Wid"] is not None:
                        tdiff = abs(c["Thk"] - float(nominal_t))
                        if tdiff <= THICKNESS_TOL and c["Wid"] >= (float(width_in) - WIDTH_TOL):
                            pa = compute_pieces_across(c["Wid"], float(width_in))
                            if pa >= 1:
                                candidates.append((pa, tdiff, c["Wid"], c))
                if candidates:
                    candidates.sort(key=lambda x: (-x[0], x[1], -x[2]))
                    pa, tdiff, w, c = candidates[0]
                    matched, m_fam, m_thk, m_wid = c["Coil_ID"], c["Family"], c["Thk"], c["Wid"]
                    thk_diff, wid_diff, pieces_across = tdiff, abs(c["Wid"]-float(width_in)), pa
                    match_status = "MATCHED"

        # Output row 
        out_rows.append([A, B, C, matched, match_status])

    # 4) Build dataset and write 
    out_headers = ["A", "B", "C", "Matched_Raw_Coil", "Match_Status"]
    out_ds = _to_dataset(out_headers, out_rows)
    system.tag.writeBlocking([OUT_TAG_PATH], [out_ds])

    log.info("BASING: wrote %d rows to %s" % (len(out_rows), OUT_TAG_PATH))

# Exe
main()