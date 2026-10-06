
# SINGLEPH 
# stored proc for 1PH tank blanks needed at herr voss per SAP start, no need to reinvent the wheel here 


# CONFIG
THICKNESS_TOL = 0.02
WIDTH_TOL     = 0.02

FORCED_BP_COIL_ID  = "10702BMXU0"
PREFER_B2_COIL_ID  = "10702BMY24"
PREFER_12H_COIL_ID = "10101CKY72"

# MATERIAL MAP
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

def decode_dim_chunk(chunk):
    c = (chunk or "").strip().upper()
    if len(c) != 3:
        return None
    if c[0].isalpha() and c[1].isdigit() and c[2].isalpha():
        return HUNDREDS_PREFIX[c[0]] + int(c[1]) + DECIMAL_SUFFIX[c[2]]
    if c[0].isalpha() and c[1:].isdigit():
        return HUNDREDS_PREFIX[c[0]] + (int(c[1:]) / 10.0)
    if c[:2].isdigit() and c[2].isalpha():
        return (int(c[:2]) / 10.0) + DECIMAL_SUFFIX[c[2]]
    if c.isdigit():
        return int(c) / 10.0
    return None

def parse_part_id(pid):
    pid = (pid or "").strip().upper()
    if len(pid) < 8 or "H" not in pid:
        return None
    prefix = pid[:2]
    if prefix not in MATERIAL_THICKNESS:
        return None
    family, nominal_thk = MATERIAL_THICKNESS[prefix]
    try:
        chunks = pid.split("H")
        len_chunk = chunks[1][:3]
        wid_chunk = pid.split("A")[1][:3]
        length_in = decode_dim_chunk(len_chunk)
        width_in  = decode_dim_chunk(wid_chunk)
    except:
        length_in = None
        width_in  = None
    return {"family": family, "nominal_thk": nominal_thk, "length_in": length_in, "width_in": width_in}

def normalize_family(material):
    s = (material or "").upper()
    if "304L" in s:
        return "304L SST"
    if "409HP" in s or "400HP" in s or "400 HP" in s:
        return "400 HP Stainless"
    if s.startswith("10101CK") or "CARB" in s:
        return "Mild Steel"
    return material

def main():
    # Named Query and paths
    namedQueryPath = "1PH Steel"                       # NQ to read
    coil_tag_path  = "[default]Sec211/Hervoss/DataAutomation/Herr Voss Inputs"       # coil master
    out_tag_path   = "[default]Sec211/Hervoss/DataAutomation/1PH Steel"              # output

    # Read 
    st_dataset  = system.db.runNamedQuery(namedQueryPath, {})
    coil_dataset = system.tag.readBlocking([coil_tag_path])[0].value

    if st_dataset is None:
        raise ValueError("Named Query '%s' returned None" % namedQueryPath)
    if coil_dataset is None:
        raise ValueError("Tag %s returned None" % coil_tag_path)

    # Column indexes (source)
    section_idx = st_dataset.getColumnIndex("Section")
    blank_idx   = st_dataset.getColumnIndex("Blank")
    count_idx   = st_dataset.getColumnIndex("Count")

    # Column indexes (coil master)
    coil_id_idx  = coil_dataset.getColumnIndex("Part ID")
    material_idx = coil_dataset.getColumnIndex("Material")
    thk_idx      = coil_dataset.getColumnIndex("Thickness (IN)")
    wid_idx      = coil_dataset.getColumnIndex("Width (IN)")

    # Convert to PyDataSet
    st_rows   = list(system.dataset.toPyDataSet(st_dataset))
    coil_rows = list(system.dataset.toPyDataSet(coil_dataset))

    # Normalize coil 
    coil_families = {}
    for coil in coil_rows:
        coil_families[coil[coil_id_idx]] = normalize_family(coil[material_idx])

    output_rows   = []
    handled_parts = set()

    # Forced BP
    for row in st_rows:
        part_id = row[blank_idx]
        if part_id.startswith("BP"):
            output_rows.append([row[section_idx], part_id, row[count_idx],
                                FORCED_BP_COIL_ID, "MATCHED_FORCED", None, None, None])
            handled_parts.add(part_id)

    # Preferences
    def find_coil_by_id(coil_id):
        for coil in coil_rows:
            if coil[coil_id_idx] == coil_id:
                return coil
        return None

    for row in st_rows:
        part_id = row[blank_idx]
        if part_id in handled_parts:
            continue

        # B2 preference
        if part_id.startswith("B2"):
            coil = find_coil_by_id(PREFER_B2_COIL_ID)
            if coil:
                output_rows.append([row[section_idx], part_id, row[count_idx],
                                    coil[coil_id_idx], "MATCHED_PREFERRED",
                                    coil[material_idx], coil[thk_idx], coil[wid_idx]])
                handled_parts.add(part_id)

        # 12H preference
        if part_id.startswith("12H"):
            coil = find_coil_by_id(PREFER_12H_COIL_ID)
            if coil:
                output_rows.append([row[section_idx], part_id, row[count_idx],
                                    coil[coil_id_idx], "MATCHED_PREFERRED",
                                    coil[material_idx], coil[thk_idx], coil[wid_idx]])
                handled_parts.add(part_id)

    # Normal matching
    for row in st_rows:
        part_id = row[blank_idx]
        if part_id in handled_parts:
            continue

        parsed = parse_part_id(part_id)
        if not parsed:
            output_rows.append([row[section_idx], part_id, row[count_idx],
                                None, "PARSE_FAIL", None, None, None])
            continue

        best_match    = None
        best_score    = None
        best_material = None
        best_thk      = None
        best_wid      = None

        for coil in coil_rows:
            if coil_families[coil[coil_id_idx]] == parsed["family"]:
                thk_diff   = abs(float(coil[thk_idx]) - float(parsed["nominal_thk"]))
                width_diff = abs(float(coil[wid_idx]) - float(parsed["width_in"]))
                if thk_diff <= THICKNESS_TOL and float(coil[wid_idx]) >= (float(parsed["width_in"]) - WIDTH_TOL):
                    score = thk_diff + width_diff
                    if best_score is None or score < best_score:
                        best_score    = score
                        best_match    = coil[coil_id_idx]
                        best_material = coil[material_idx]
                        best_thk      = coil[thk_idx]
                        best_wid      = coil[wid_idx]

        status = "MATCHED" if best_match else "NO_MATCH"
        output_rows.append([row[section_idx], part_id, row[count_idx],
                            best_match, status, best_material, best_thk, best_wid])

    # Build dataset and write
    cols = ["Section", "Blank", "Count",
            "Matched_Raw_Coil", "Match_Status", "Material", "Coil_Thickness", "Coil_Width"]
    result_dataset = system.dataset.toDataSet(cols, output_rows)
    system.tag.writeBlocking([out_tag_path], [result_dataset])

#calls
if __name__ == "__builtin__":
    main()
