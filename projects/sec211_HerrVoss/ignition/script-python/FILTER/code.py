
def run():
  
    import system
    from system.dataset import toDataSet

    TAG_PATH = "[default]Sec211/Hervoss/DataAutomation/HVSV2"

    # Read dataset from the memory tag
    qv = system.tag.readBlocking([TAG_PATH])[0]
    ds = qv.value

    # Ensure we have a dataset
    if ds is None or not hasattr(ds, "getRowCount"):
        system.util.getLogger("FILTER.run").warn(
            "HVSV2 tag does not contain a Dataset or is None: {}".format(TAG_PATH)
        )
        return

    # Ensure required columns exist
    columns = [ds.getColumnName(i) for i in range(ds.getColumnCount())]
    if "Source File" not in columns or "Additional" not in columns:
        system.util.getLogger("FILTER.run").warn(
            "Required columns missing: 'Source File' and/or 'Additional'."
        )
        return

    allowed_additional = {"Weid 1", "Weid 7"}
    filtered_rows = []
    col_count = ds.getColumnCount()

    kept = 0
    removed = 0

    for row in range(ds.getRowCount()):
        source_file = ds.getValueAt(row, "Source File")
        additional = ds.getValueAt(row, "Additional")

        # Normalize for safe comparison
        sf = (source_file or "").strip()
        ad = (additional or "").strip() if additional is not None else None

        # Keep logic:
        # - If Source File != "ECS" -> keep
        # - If Source File == "ECS" -> keep only if Additional in {"Weid 1", "Weid 7"}
        keep = (sf != "ECS") or (sf == "ECS" and ad in allowed_additional)

        if keep:
            row_values = [ds.getValueAt(row, i) for i in range(col_count)]
            filtered_rows.append(row_values)
            kept += 1
        else:
            removed += 1

   
    new_ds = toDataSet(columns, filtered_rows)
    system.tag.writeBlocking([TAG_PATH], [new_ds])

    
    system.util.getLogger("FILTER.run").info(
        "Filtered HVSV2: kept {}, removed {}.".format(kept, removed)
    )