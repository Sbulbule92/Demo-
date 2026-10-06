
# KBS (Kanban)


# CONFIG
THICKNESS_TOL = 0.02
WIDTH_TOL     = 0.02
FORCED_BP_COIL_ID = "10702BMXU0"
FORCED_P1_COIL_ID = "10702TJ011"

# MATERIAL
MATERIAL_THICKNESS = {
    "11": ("Mild Steel", 0.075),
    "12": ("Mild Steel", 0.090),
    "13": ("Mild Steel", 0.105),
    "14": ("Mild Steel", 0.120),
    "15": ("Mild Steel", 0.180),
    "72": ("Mild Steel", 0.090),
    "71": ("Mild Steel", 0.075),
    "Q1": ("304L SST", 0.075),
    "Q2": ("304L SST", 0.090),
    "Q3": ("304L SST", 0.105),
    "Q4": ("304L SST", 0.120),
    "Q5": ("304L SST", 0.180),
    "P1": ("304L SST", 0.075),
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
        return HUNDREDS_PREFIX[c[0]] + int(c[1:])
    if c[:2].isdigit() and c[2].isalpha():
        return int(c[:2]) + DECIMAL_SUFFIX[c[2]]
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
    log = system.util.getLogger("Kanban-Coil-Matcher")

    # 1) Read Kanban 
    kanban_dataset = system.db.runNamedQuery("Kanban")   # Named Query

    # 2) Read coil master dataset 
    coil_dataset = system.tag.readBlocking(["[default]Sec211/Hervoss/DataAutomation/Herr Voss Inputs"])[0].value

    if kanban_dataset is None:
        raise ValueError("Named Query 'Kanban' returned None")
    if coil_dataset is None:
        raise ValueError("Tag [default]Herr Voss Inputs returned None")

    # Resolve column indexes
    po_idx    = kanban_dataset.getColumnIndex("PO Number")
    loc_idx   = kanban_dataset.getColumnIndex("Current_Operation")
    blank_idx = kanban_dataset.getColumnIndex("Blank")
    date_idx  = kanban_dataset.getColumnIndex("Download Date")
    qty_idx   = kanban_dataset.getColumnIndex("Count")

    coil_id_idx  = coil_dataset.getColumnIndex("Part ID")
    material_idx = coil_dataset.getColumnIndex("Material")
    thk_idx      = coil_dataset.getColumnIndex("Thickness (IN)")
    wid_idx      = coil_dataset.getColumnIndex("Width (IN)")

    # PyData
    kanban_rows = list(system.dataset.toPyDataSet(kanban_dataset))
    coil_rows   = list(system.dataset.toPyDataSet(coil_dataset))

    # Normalize coil family
    coil_families = {}
    for coil in coil_rows:
        coil_families[coil[coil_id_idx]] = normalize_family(coil[material_idx])

    output_rows   = []
    handled_parts = set()

    # Forced rules
    for row in kanban_rows:
        part_id = row[blank_idx] or ""
        if part_id.startswith("P1"):
            output_rows.append([row[po_idx], row[loc_idx], part_id, row[date_idx], row[qty_idx],
                                FORCED_P1_COIL_ID, "MATCHED_FORCED", None, None, None])
            handled_parts.add(part_id)
        elif part_id.startswith("BP"):
            output_rows.append([row[po_idx], row[loc_idx], part_id, row[date_idx], row[qty_idx],
                                FORCED_BP_COIL_ID, "MATCHED_FORCED", None, None, None])
            handled_parts.add(part_id)

    # Normal matching
    for row in kanban_rows:
        part_id = row[blank_idx]
        if part_id in handled_parts:
            continue

        parsed = parse_part_id(part_id)
        if not parsed or parsed.get("width_in") is None:
            output_rows.append([row[po_idx], row[loc_idx], part_id, row[date_idx], row[qty_idx],
                                None, "PARSE_FAIL", None, None, None])
            continue

        best_match    = None
        best_score    = None
        best_material = None
        best_thk      = None
        best_wid      = None

        for coil in coil_rows:
            if coil_families.get(coil[coil_id_idx]) == parsed["family"]:
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
        output_rows.append([row[po_idx], row[loc_idx], part_id, row[date_idx], row[qty_idx],
                            best_match, status, best_material, best_thk, best_wid])

    # 3) Build dataset and write 
    cols = ["ProductionOrder", "Location", "Blank", "Date", "Quantity",
            "Matched_Raw_Coil", "Match_Status", "Material", "Coil_Thickness", "Coil_Width"]
    result_dataset = system.dataset.toDataSet(cols, output_rows)
    system.tag.writeBlocking(["[default]Sec211/Hervoss/DataAutomation/Kanban"], [result_dataset])  # <-- WRITE TO TAG

# script calls
if __name__ == "__builtin__":
    main()