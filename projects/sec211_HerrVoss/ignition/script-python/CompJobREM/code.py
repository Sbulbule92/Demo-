
def run():
    try:
        # Read HVSV2 dataset from memory tag
        hvsv2_ds = system.tag.readBlocking(["[default]Sec211/Hervoss/DataAutomation/HVSV2"])[0].value
        hvsv2_cols = list(hvsv2_ds.getColumnNames())
        hvsv2_rows = []
        for i in range(hvsv2_ds.getRowCount()):
            hvsv2_rows.append([hvsv2_ds.getValueAt(i, col) for col in range(len(hvsv2_cols))])

        # Get Completed Jobs dataset from Named Query
        completed_ds = system.db.runNamedQuery("Completed Jobs", {})
        completed_cols = list(completed_ds.getColumnNames())
        completed_rows = []
        for i in range(completed_ds.getRowCount()):
            completed_rows.append([completed_ds.getValueAt(i, col) for col in range(len(completed_cols))])

        # Calculate cutoff date (last 2 days)
        cutoff = system.date.addHours(system.date.now(), -16)

        # Debug logging
        logger = system.util.getLogger("CompJobREM")
        logger.info("Cutoff date: {}".format(cutoff))
        logger.info("HVSV2 rows: {}".format(len(hvsv2_rows)))
        logger.info("Completed Jobs rows: {}".format(len(completed_rows)))

        filtered_rows = []
        removed_rows = []

        # Filtering logic
        for hv_row in hvsv2_rows:
            keep = True
            hv_dict = dict(zip(hvsv2_cols, hv_row))

            for comp_row in completed_rows:
                comp_dict = dict(zip(completed_cols, comp_row))

                # Check if Completed Job is within last 2 days
                if system.date.isAfter(comp_dict["Date"], cutoff):
                    # Condition 1: Identifier match
                    if hv_dict["Identifier"] == comp_dict["Identifier"]:
                        keep = False
                        removed_rows.append(hv_dict)
                        break

                    # Condition 2: Identifier == "Not Serialized"
                    if comp_dict["Identifier"] == "Not Serialized":
                        if (hv_dict["Part ID"] == comp_dict["Part_ID"] and
                            hv_dict["Additional"] == comp_dict["Additional"] and
                            hv_dict["Quantity"] == comp_dict["Quantity"] and
                            hv_dict["Source File"] == comp_dict["Source_File"]):
                            keep = False
                            removed_rows.append(hv_dict)
                            break

            if keep:
                filtered_rows.append(hv_row)

        # Write filtered dataset back to memory tag
        new_ds = system.dataset.toDataSet(hvsv2_cols, filtered_rows)
        system.tag.writeBlocking(["[default]Sec211/Hervoss/DataAutomation/HVSV2"], [new_ds])

        # Log summary
        logger.info("Rows removed: {}".format(len(removed_rows)))
        if removed_rows:
            logger.info("Sample removed row: {}".format(removed_rows[0]))

    except Exception as e:
        system.util.getLogger("CompJobREM").error("Error filtering HVSV2: {}".format(e))