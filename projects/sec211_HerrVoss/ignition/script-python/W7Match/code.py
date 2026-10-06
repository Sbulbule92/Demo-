
def run():
    """
    Compares W7P dataset to HVSV2 dataset and updates 'Additional' column
    for rows where Source File = ECS and Part ID matches Material in W7P.
    Shows a popup with the number of rows changed.
    """
    from system.dataset import toDataSet
    from system.gui import messageBox

    # 1. Read datasets
    w7p_ds = system.tag.readBlocking(["[default]Sec211/Hervoss/DataAutomation/W7P"])[0].value
    hvsv2_ds = system.tag.readBlocking(["[default]Sec211/Hervoss/DataAutomation/HVSV2"])[0].value

    # 2. Convert HVSV2 to list for modification
    hvsv2_data = []
    for row in range(hvsv2_ds.getRowCount()):
        hvsv2_data.append([hvsv2_ds.getValueAt(row, col) for col in range(hvsv2_ds.getColumnCount())])

    # Column indexes for HVSV2
    hvsv2_cols = list(hvsv2_ds.getColumnNames())
    part_id_idx = hvsv2_cols.index("Part ID")
    quantity_idx = hvsv2_cols.index("Quantity")
    additional_idx = hvsv2_cols.index("Additional")
    source_idx = hvsv2_cols.index("Source File")

    # 3. Build W7P dictionary: Material -> total_qty
    w7p_dict = {}
    for row in range(w7p_ds.getRowCount()):
        material = str(w7p_ds.getValueAt(row, "Material")).strip().upper()
        qty = w7p_ds.getValueAt(row, "Quantity")
        w7p_dict[material] = w7p_dict.get(material, 0) + qty

    # 4. Update HVSV2 rows where conditions match
    changed_count = 0
    for i, row in enumerate(hvsv2_data):
        source_file = row[source_idx]
        if source_file != "ECS":
            continue  # Skip non-ECS rows

        part_id = str(row[part_id_idx]).strip().upper()
        hvsv2_qty = row[quantity_idx]

        if part_id in w7p_dict and hvsv2_qty <= w7p_dict[part_id]:
            hvsv2_data[i][additional_idx] = "Weid 7"
            changed_count += 1

    # 5. Write updated dataset back to HVSV2
    new_hvsv2_ds = toDataSet(hvsv2_cols, hvsv2_data)
    system.tag.writeBlocking(["[default]Sec211/Hervoss/DataAutomation/HVSV2"], [new_hvsv2_ds])

    # 6. Show popup message with count
    messageBox("W7 routing complete. Rows changed: {}".format(changed_count), "HVSV2 Update")