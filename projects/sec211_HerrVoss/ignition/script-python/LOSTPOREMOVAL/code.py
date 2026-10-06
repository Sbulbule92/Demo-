
def run():
    """
    Removes rows from HVSV2 where:
    - Source File is '3PHU' or '3PHTFR'
    - Identifier is 'Not Serialized'
    """
    from system.dataset import toDataSet

    # 1. Read HVSV2 dataset
    hvsv2_ds = system.tag.readBlocking(["[default]Sec211/Hervoss/DataAutomation/HVSV2"])[0].value

    # 2. Get column indexes
    hvsv2_cols = list(hvsv2_ds.getColumnNames())
    source_idx = hvsv2_cols.index("Source File")
    identifier_idx = hvsv2_cols.index("Identifier")

    # 3. Filter rows
    filtered_data = []
    for row in range(hvsv2_ds.getRowCount()):
        source_file = hvsv2_ds.getValueAt(row, source_idx)
        identifier = hvsv2_ds.getValueAt(row, identifier_idx)

        # Keep row only if it does NOT match removal criteria
        if not ((source_file in ["3PHU", "3PHTFR"]) and identifier == "Not Serialized"):
            filtered_data.append([hvsv2_ds.getValueAt(row, col) for col in range(hvsv2_ds.getColumnCount())])

    # 4. Write updated dataset back to HVSV2
    new_hvsv2_ds = toDataSet(hvsv2_cols, filtered_data)
    system.tag.writeBlocking(["[default]Sec211/Hervoss/DataAutomation/HVSV2"], [new_hvsv2_ds])