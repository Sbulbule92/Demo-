
PHTT_NQ_PATH   = "3PHTT"                          # Named Query 
COIL_TAG_PATH  = "[default]Sec211/Hervoss/DataAutomation/Herr Voss Inputs"      # Dataset tag with coil master
OUT_TAG_PATH   = "[default]Sec211/Hervoss/DataAutomation/3PHTT"                 # Dataset tag to write 


FIELD_TO_LETTER = {
    "ScheduleDate": "A",
    "workcenter":   "B",
    "BlankId":      "C",   # functional part for parsing/matching
    "Quantity":     "D",
    "Cover":        "E",
    "HH_Qnty":      "F",   # summed when combining 
    "WC_Clip":      "G",
    "Cover_ASM":    "H",
      
}
#create a trailing I column
APPEND_EMPTY_I = True

# Combine duplicates, Group rows by (B, C) and sum F (HH_Qnty)
ENABLE_COMBINE = True
GROUP_BY_LETTERS = ("B", "C")    # workcenter + BlankId
SUM_LETTER       = "F"           # sum HH_Qnty

# Matching tolerances and forced rules 
THICKNESS_TOL        = 0.02
WIDTH_TOL            = 0.02
REQUIRE_LENGTH_CHECK = False
FORCED_BP_COIL_ID    = "10702BMXU0"

# maps 
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

def _decode_dim_chunk(chunk):
    c = (chunk or "").strip().upper()
    if len(c) != 3:
        raise ValueError("Chunk must be 3 characters: '%s'" % c)
    if c[0].isalpha() and c[1].isdigit() and c[2].isalpha():   # LDL
        return HUNDREDS_PREFIX[c[0]] + int(c[1]) + DECIMAL_SUFFIX[c[2]]
    if c[0].isalpha() and c[1:].isdigit():                     # LDD
        return HUNDREDS_PREFIX[c[0]] + (int(c[1:]) / 10.0)
    if c[:2].isdigit() and c[2].isalpha():                     # DDL
        return (int(c[:2]) / 10.0) + DECIMAL_SUFFIX[c[2]]
    if c.isdigit():                                            # DDD
        return int(c) / 10.0
    raise ValueError("Invalid chunk pattern: '%s'" % c)

def parse_functional_part_id(pid):
    """
    Expected format: 2-char prefix + 'H' + 3-char len + 'A' + 3-char width.
    """
    s = (pid or "").strip().upper()
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

def normalize_coil_family(material):
    s = (material or "").strip().upper()
    if "304L" in s:
        return "304L SST"
    if "409HP" in s or "400HP" in s or "400 HP" in s:
        return "400 HP Stainless"
    if s.startswith("10101CK") or "CARB" in s:
        return "Mild Steel"
    return material

def build_dataset(headers, rows):
    return system.dataset.toDataSet(headers, rows)

def map_query_to_letters(nq_ds):
    """
    Convert the named query dataset to A..I (letters) using FIELD_TO_LETTER.
    Serial_Number is omitted (None) to match your output.
    Optionally appends an empty 'I' column so A..I exist in order.
    """
    src_cols = list(nq_ds.getColumnNames())
    src_rows = [ [r[i] for i in range(len(src_cols))] for r in system.dataset.toPyDataSet(nq_ds) ]

    # Build letter 4 value mapping per row
    used_letters = set([L for L in FIELD_TO_LETTER.values() if L])
    letters = sorted(used_letters, key=lambda c: ord(c))
    # Ensure we have a continuous run starting from 'A'
    if APPEND_EMPTY_I and "I" not in letters:
        letters.append("I")  # create blank I to mimic initial data structure 

    # srce index
    src_idx = {}
    for name, L in FIELD_TO_LETTER.items():
        if not L:
            continue
        try:
            src_idx[L] = src_cols.index(name)
        except ValueError:
            raise ValueError("Named Query missing required column '%s'. Found: %r" % (name, src_cols))

    out_headers = letters[:]  # A..I
    out_rows = []
    for row in src_rows:
        new_row = []
        for L in letters:
            if L in src_idx:
                new_row.append(row[src_idx[L]])
            else:
                
                new_row.append("")
        out_rows.append(new_row)
    return out_headers, out_rows

def combine_rows(headers, rows, group_by_letters, sum_letter):
    """Group by the given letters and sum the sum_letter."""
    letter_to_pos = { L:i for i,L in enumerate(headers) }
    for L in list(group_by_letters) + [sum_letter]:
        if L not in letter_to_pos:
            raise ValueError("Combine requires the letter column '%s', but headers are %r" % (L, headers))

    gb_idx = tuple(letter_to_pos[L] for L in group_by_letters)
    sum_idx = letter_to_pos[sum_letter]

    combined = {}
    order = {}
    for r in rows:
        key = tuple(r[i] for i in gb_idx)
        try:
            sval = r[sum_idx]
            val = float(sval) if sval not in (None, "") else 0.0
        except:
            val = 0.0
        if key not in combined:
            combined[key] = list(r)
            combined[key][sum_idx] = val
            order[key] = len(order)
        else:
            combined[key][sum_idx] = float(combined[key][sum_idx]) + val

    out = [combined[k] for k in sorted(order.keys(), key=lambda k: order[k])]
    return headers, out

def main():
    log = system.util.getLogger("3PHTT-Coil-Matcher")

    # 1) raw 3PHTT 
    phtt_ds = system.db.runNamedQuery(PHTT_NQ_PATH)
    try:
        phtt_ds = system.dataset.toDataSet(phtt_ds)  # normalize to Dataset
    except:
        pass

    # 2) Map 
    headers, rows = map_query_to_letters(phtt_ds)
    log.info("3PHTT mapped to letters: headers=%r, rows=%d" % (headers, len(rows)))

    # 3) Combine duplicates
    if ENABLE_COMBINE:
        before = len(rows)
        headers, rows = combine_rows(headers, rows, GROUP_BY_LETTERS, SUM_LETTER)
        log.info("3PHTT combine %s by %s: %d -> %d rows" % (SUM_LETTER, GROUP_BY_LETTERS, before, len(rows)))

    # 4) Load coil master 
    coil_ds = system.tag.readBlocking([COIL_TAG_PATH])[0].value
    if coil_ds is None:
        raise ValueError("Coil master tag %s returned None" % COIL_TAG_PATH)

    # Build coil list 
    c_headers = list(coil_ds.getColumnNames())
    required = ["Part ID", "Thickness (IN)", "Width (IN)", "Material"]
    for req in required:
        if req not in c_headers:
            raise ValueError("Coil master missing required column '%s'. Found: %r" % (req, c_headers))

    coil_rows = [ {h:r[i] for i,h in enumerate(c_headers)} for r in system.dataset.toPyDataSet(coil_ds) ]
    coil_list = []
    for d in coil_rows:
        coil_list.append({
            "Coil_ID": d["Part ID"],
            "Family":  normalize_coil_family(d["Material"]),
            "Thk":     float(d["Thickness (IN)"]) if d["Thickness (IN)"] is not None else None,
            "Wid":     float(d["Width (IN)"]) if d["Width (IN)"] is not None else None,
        })

    # 5) Match coils 
    # Append Matched_Raw_Coil 
    if "Matched_Raw_Coil" not in headers:
        headers = headers + ["Matched_Raw_Coil"]

    idx_C = headers.index("C") if "C" in headers else None
    idx_M = headers.index("Matched_Raw_Coil")

    if idx_C is None:
        raise ValueError("Output headers missing 'C' (BlankId). headers=%r" % headers)

    out_rows = []
    for row in rows:
        
        if len(row) < len(headers):
            row = row + [None] * (len(headers) - len(row))

        part_id = row[idx_C] or ""
        fam, nominal_t, lw_tuple, status = parse_functional_part_id(part_id)

        matched = None
        if status == "OK" and lw_tuple is not None:
            length_in, width_in = lw_tuple
            best_score = None
            best_choice = None

            if part_id.startswith("BP"):
                for c in coil_list:
                    if c["Coil_ID"] == FORCED_BP_COIL_ID:
                        best_choice = c
                        break
            else:
                for c in coil_list:
                    if c["Family"] == fam and c["Thk"] is not None and c["Wid"] is not None:
                        thk_diff = abs(c["Thk"] - float(nominal_t))
                        wid_diff = abs(c["Wid"] - float(width_in))
                        if thk_diff <= THICKNESS_TOL and c["Wid"] >= (float(width_in) - WIDTH_TOL):
                            score = thk_diff + wid_diff
                            if best_score is None or score < best_score:
                                best_score = score
                                best_choice = c
            if best_choice is not None:
                matched = best_choice["Coil_ID"]

        row[idx_M] = matched
        out_rows.append(row)

    # 6) Write to the output 
    result_ds = build_dataset(headers, out_rows)
    system.tag.writeBlocking([OUT_TAG_PATH], [result_ds])
    log.info("Wrote %d rows to %s" % (len(out_rows), OUT_TAG_PATH))

# Execute
main()