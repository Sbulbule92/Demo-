
# SUBMERSIBLES
# CONFIG
SUBMERSIBLES_NQ_PATH = "Submersibles"  # Named Query that provides the SUB sheet
PIRMADA_TAG_PATH = "[default]Sec211/Hervoss/DataAutomation/Pirmada Inputs"  # Coil master dataset tag
OUT_TAG_PATH = "[default]Sec211/Hervoss/DataAutomation/SUBMERSIBLES"  # Output dataset tag (change if desired)
# Matching tolerances (inches)
THICKNESS_TOL = 0.02
WIDTH_TOL = 0.02
REQUIRE_LENGTH_CHECK = False  # kept for parity with your Py script
# Forced coil for BP prefix
FORCED_BP_COIL_ID = "10702BMXU0"
# aliases because there was a column mismatch between python initial and true sql output with real headers
ALIASES_SUB = {
    "A": ["A"],
    "B": ["B"],
    "G": ["G"],
    "I": ["I"],
    "J": ["J"],
    "K": ["K"],  # Front entries (multiple; "STD-FUNC" or just FUNC)
    "L": ["L"],  # Back entries
    "M": ["M"],  # Console entries
}
# Pirmada Inputs , used instead of herr voss inputs because of UCT tops routing
ALIASES_COILS = {
    "CoilID": ["Part ID", "Coil ID", "CoilID", "Item"],
    "Material": ["Material"],
    "Thk": ["Thickness (IN)", "Thickness in", "Thickness"],
    "Wid": ["Width (IN)", "Width in", "Width"],
    "AvailLen": ["Available Length at Maximum (IN)", "Avail Length (IN)", "Coil Available Length (IN)"],  # optional
}
# MATERIAL MAPS
MATERIAL_THICKNESS = {
    "11": ("Mild Steel", 0.075), "12": ("Mild Steel", 0.090),
    "13": ("Mild Steel", 0.105), "14": ("Mild Steel", 0.120),
    "15": ("Mild Steel", 0.180), "72": ("Mild Steel", 0.090),
    "Q1": ("304L SST", 0.075), "Q2": ("304L SST", 0.090),
    "Q3": ("304L SST", 0.105), "Q4": ("304L SST", 0.120),
    "Q5": ("304L SST", 0.180),
    "B2": ("400 HP Stainless", 0.090), "B3": ("400 HP Stainless", 0.105),
    "B4": ("400 HP Stainless", 0.120), "BP": ("400 HP Stainless", 0.135),
}
DECIMAL_SUFFIX = {"A": 0.05, "B": 0.15, "C": 0.25, "D": 0.35, "G": 0.45, "H": 0.55, "J": 0.65, "P": 0.75, "T": 0.85, "R": 0.95}
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
        return (int(c[:2]) / 10.0) + DECIMAL_SUFFIX[c[2]]
    if c.isdigit():
        return int(c) / 10.0
    raise ValueError("Invalid chunk: %s" % c)
def parse_functional_part_id(pid):
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
        width_in = _decode_dim_chunk(wid_chunk)
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
def split_entries(cell):
    """Split K/L/M cell on ',' or ';' and trim."""
    if cell is None:
        return []
    txt = str(cell)
    parts = []
    cur = ""
    for ch in txt:
        if ch in ",;":
            if cur.strip():
                parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts
def parse_entry(entry):
    """Return (standard_code or None, functional_code). Supports 'STD-FUNC' or just 'FUNC'."""
    if "-" in entry:
        left, right = entry.split("-", 1)
        return left.strip(), right.replace(" ", "").strip()
    return None, entry.replace(" ", "").strip()
def should_ignore_entry(std_code):
    """Ignore if std_code exists and its 3rd character is 'C' (case-insensitive)."""
    if std_code is None:
        return False
    sc = str(std_code).strip()
    return (len(sc) >= 3 and sc[2].upper() == "C")
# MAIN
def main():
    log = system.util.getLogger("SUBMERSIBLES")
    # 1) Read Submersibles Named Query
    sub_ds = system.db.runNamedQuery(SUBMERSIBLES_NQ_PATH)  # NQ call
    try:
        sub_ds = system.dataset.toDataSet(sub_ds)  # normalize
    except:
        pass
    headers, rows = _ds_to_rows(sub_ds)
    # Resolve needed columns
    colA = _resolve_col(headers, ALIASES_SUB["A"]) or (headers[0] if len(headers) > 0 else None)
    colB = _resolve_col(headers, ALIASES_SUB["B"]) or (headers[1] if len(headers) > 1 else None)
    colG = _resolve_col(headers, ALIASES_SUB["G"]) or (headers[6] if len(headers) > 6 else None)
    colI = _resolve_col(headers, ALIASES_SUB["I"]) or (headers[8] if len(headers) > 8 else None)
    colJ = _resolve_col(headers, ALIASES_SUB["J"]) or (headers[9] if len(headers) > 9 else None)
    colK = _resolve_col(headers, ALIASES_SUB["K"]) or (headers[10] if len(headers) > 10 else None)
    colL = _resolve_col(headers, ALIASES_SUB["L"]) or (headers[11] if len(headers) > 11 else None)
    colM = _resolve_col(headers, ALIASES_SUB["M"]) or (headers[12] if len(headers) > 12 else None)
    needed_list = [colA, colB, colI, colG, colJ, colK, colL, colM]
    if any(c is None for c in needed_list):
        raise ValueError("Submersibles query missing required columns A,B,I,G,J,K,L,M (or compatible positions). Found: %r" % headers)
    # 2) Explode K/L/M -- stored format has blanks concatenated, need split into line items
    exploded = []
    for d in rows:
        A = d.get(colA)
        B = d.get(colB)
        C = d.get(colI)  # Functional bundle
        G = d.get(colG)
        J = d.get(colJ)
        # Position columns
        for col, pos in ((colK, "Front"), (colL, "Back"), (colM, "Console")):
            entries = split_entries(d.get(col))
            if not entries:
                continue
            for entry in entries:
                std_code, func_code = parse_entry(entry)
                if should_ignore_entry(std_code):
                    continue
                if not func_code:
                    continue
                # >>> NEW FILTER: Skip Functional_Part_ID starting with "Q4"
                if func_code.upper().startswith("Q4"):
                    continue
                # >>> FILTER: Skip specific excluded part IDs
                if func_code.upper() in ("BP247A185",):
                    continue
                exploded.append({
                    "A": _norm(A),
                    "B": _norm(B),
                    "C": _norm(C),  # from I
                    "G": _norm(G),
                    "J": _norm(J),
                    "Position": pos,
                    "Standard_Code": _norm(std_code) if std_code else "",
                    "Functional_Part_ID": _norm(func_code),
                    "Quantity": 1,
                })
    if not exploded:
        log.info("SUBMERSIBLES: No entries were found to process.")
        final_cols = ["A","B","C","G","J","Position","Standard_Code","Functional_Part_ID","Quantity",
                      "Family","Nominal_Thickness_in","Part_Length_in","Part_Width_in",
                      "Matched_Raw_Coil","Material","Coil_Family","Coil_Thickness_in","Coil_Width_in",
                      "Thk_Diff","Width_Diff","Match_Status","Parse_Status"]
        system.tag.writeBlocking([OUT_TAG_PATH], [_to_dataset(final_cols, [])])
        return
    # 3) Parse parts
    parts_parsed = []
    for r in exploded:
        fam, nominal_t, lw_tuple, status = parse_functional_part_id(r["Functional_Part_ID"])
        length_in = width_in = None
        if lw_tuple is not None:
            length_in, width_in = lw_tuple
        pr = dict(r)
        pr["Parse_Status"] = status
        pr["Family"] = fam
        pr["Nominal_Thickness_in"] = nominal_t
        pr["Part_Length_in"] = length_in
        pr["Part_Width_in"] = width_in
        parts_parsed.append(pr)
    # 4) Load Pirmada Inputs (coil master)
    coils_ds = system.tag.readBlocking([PIRMADA_TAG_PATH])[0].value  # tag read
    if coils_ds is None:
        raise ValueError("Tag %s returned None" % PIRMADA_TAG_PATH)
    c_headers, c_rows = _ds_to_rows(coils_ds)
    c_id = _resolve_col(c_headers, ALIASES_COILS["CoilID"])
    c_mat = _resolve_col(c_headers, ALIASES_COILS["Material"])
    c_thk = _resolve_col(c_headers, ALIASES_COILS["Thk"])
    c_wid = _resolve_col(c_headers, ALIASES_COILS["Wid"])
    c_len = _resolve_col(c_headers, ALIASES_COILS["AvailLen"])  # optional
    for req in (c_id, c_mat, c_thk, c_wid):
        if not req:
            raise ValueError("Pirmada Inputs missing CoilID/Material/Thickness/Width. Found: %r" % c_headers)
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
            "Family": normalize_family(d.get(c_mat)),
            "Thk": thk,
            "Wid": wid,
            "AvailLen": d.get(c_len) if c_len else None
        })
    # 5) Matching
    results = []
    for r in parts_parsed:
        ok = (r["Parse_Status"] == "OK")
        func = r["Functional_Part_ID"]
        fam = r["Family"]
        nominal_t = r["Nominal_Thickness_in"]
        width_in = r["Part_Width_in"]
        length_in = r["Part_Length_in"]
        match_status = r["Parse_Status"] if not ok else "NO_MATCH"
        matched = None
        m_mat = m_fam = None
        m_thk = m_wid = None
        thk_diff = wid_diff = None
        if ok:
            # 5.1 Forced BP
            if func.startswith("BP"):
                for c in coil_list:
                    if c["Coil_ID"] == FORCED_BP_COIL_ID:
                        matched = c["Coil_ID"]
                        m_fam = c["Family"]
                        m_mat = c["Family"]
                        m_thk = c["Thk"]
                        m_wid = c["Wid"]
                        thk_diff = abs((m_thk or 0) - float(nominal_t)) if m_thk is not None else None
                        wid_diff = abs((m_wid or 0) - float(width_in)) if m_wid is not None else None
                        match_status = "MATCHED_FORCED"
                        break
            # 5.2 Normal matching
            if matched is None:
                candidates = []
                for c in coil_list:
                    if c["Family"] == fam and c["Thk"] is not None and c["Wid"] is not None:
                        tdiff = abs(c["Thk"] - float(nominal_t))
                        w_ok = c["Wid"] >= (float(width_in) - WIDTH_TOL)
                        length_ok = True
                        if REQUIRE_LENGTH_CHECK and c["AvailLen"] is not None and length_in is not None:
                            try:
                                length_ok = float(c["AvailLen"]) >= float(length_in)
                            except:
                                length_ok = True
                        if tdiff <= THICKNESS_TOL and w_ok and length_ok:
                            wdiff = abs(c["Wid"] - float(width_in))
                            candidates.append((tdiff, wdiff, c))
                if candidates:
                    candidates.sort(key=lambda x: (x[0], x[1]))
                    tdiff, wdiff, c = candidates[0]
                    matched = c["Coil_ID"]
                    m_fam = c["Family"]
                    m_mat = c["Family"]
                    m_thk = c["Thk"]
                    m_wid = c["Wid"]
                    thk_diff = tdiff
                    wid_diff = wdiff
                    match_status = "MATCHED"
        results.append([
            r.get("A",""), r.get("B",""), r.get("C",""), r.get("G",""), r.get("J",""),
            r.get("Position",""), r.get("Standard_Code",""), r.get("Functional_Part_ID",""), r.get("Quantity",1),
            r.get("Family"), r.get("Nominal_Thickness_in"), r.get("Part_Length_in"), r.get("Part_Width_in"),
            matched, m_mat, m_fam, m_thk, m_wid, thk_diff, wid_diff, match_status, r.get("Parse_Status")
        ])
    # 6) Build dataset and write to tag
    cols_order = [
        "A","B","C","G","J","Position","Standard_Code","Functional_Part_ID","Quantity",
        "Family","Nominal_Thickness_in","Part_Length_in","Part_Width_in",
        "Matched_Raw_Coil","Material","Coil_Family","Coil_Thickness_in","Coil_Width_in",
        "Thk_Diff","Width_Diff","Match_Status","Parse_Status"
    ]
    out_ds = _to_dataset(cols_order, results)
    system.tag.writeBlocking([OUT_TAG_PATH], [out_ds])
    log.info("SUBMERSIBLES: wrote %d rows to %s" % (len(results), OUT_TAG_PATH))
# Execute
main()