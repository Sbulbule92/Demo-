
def run():
    """
    Removes rows from the dataset memory tag
    [default]Sec211/Hervoss/DataAutomation/HVSV2
    when its 'Identifier' matches any 'ProductionOrder' returned by the
    'MTSFB' named query.

    Behavior:
      - Never raises exceptions (safe for gateway events).
      - Shows a local Vision popup (client/designer) with the result summary.
      - Skips any popup if running on the Gateway.

    Returns (dict):
        {
          "success": True/False,
          "message": str,
          "productionOrdersCount": int,
          "rowsBefore": int,
          "rowsRemoved": int,
          "rowsAfter": int
        }
    """
    logger = system.util.getLogger("HVSV2_MTSFB_Cleanup")

    # --- Config ---
    tagpath = "[default]Sec211/Hervoss/DataAutomation/HVSV2"
    named_query_path = "MTSFB"   
    named_query_params = {}      

    # Helper: normalize values for reliable matching
    try:
        _unicode = unicode   # Jython 2.7 (Ignition 8)
    except NameError:
        _unicode = str

    def _norm(val):
        return _unicode(val).strip() if val is not None else None

    # Helper: local-only popup 
    def _maybe_popup(title, msg):
        try:
            flags = system.util.getSystemFlags()
            is_client = (flags & system.util.CLIENT_FLAG) == system.util.CLIENT_FLAG
            is_designer = (flags & system.util.DESIGNER_FLAG) == system.util.DESIGNER_FLAG
            if is_client or is_designer:
                try:
                    system.gui.messageBox(_unicode(msg), _unicode(title))
                except Exception as e:
                    # Log but never raise.
                    logger.warn("Popup attempt failed (suppressed): {}".format(e))
            # If gateway, do nothing.
        except Exception as e:
            
            logger.warn("Scope detection failed (suppressed): {}".format(e))

    summary = {
        "success": False,
        "message": "",
        "productionOrdersCount": 0,
        "rowsBefore": 0,
        "rowsRemoved": 0,
        "rowsAfter": 0
    }

    try:
        # 1) Run named query and collect ProductionOrder values
        nq_result = system.db.runNamedQuery(named_query_path, named_query_params)
        if nq_result is None:
            msg = "Named query '{}' returned None".format(named_query_path)
            logger.warn(msg)
            summary["message"] = msg
            _maybe_popup("HVSV2 Cleanup", msg)
            return summary

        production_orders = set()
        for r in range(nq_result.getRowCount()):
            po = nq_result.getValueAt(r, "ProductionOrder")  # Column in MTSFB
            po_norm = _norm(po)
            if po_norm:
                production_orders.add(po_norm)

        summary["productionOrdersCount"] = len(production_orders)
        if not production_orders:
            msg = "No ProductionOrder values from named query '{}'. Nothing to remove.".format(named_query_path)
            logger.info(msg)
            summary["message"] = msg
            summary["success"] = True
            _maybe_popup("HVSV2 Cleanup", msg)
            return summary

        # 2) Read the dataset from the memory tag
        qv = system.tag.readBlocking([tagpath])[0]
        ds = qv.value

        if ds is None or not hasattr(ds, "getRowCount"):
            msg = "Tag '{}' has no dataset value. Nothing to do.".format(tagpath)
            logger.info(msg)
            summary["message"] = msg
            summary["success"] = True
            _maybe_popup("HVSV2 Cleanup", msg)
            return summary

        ds_row_count = ds.getRowCount()
        ds_col_count = ds.getColumnCount()
        summary["rowsBefore"] = ds_row_count

        if ds_row_count == 0 or ds_col_count == 0:
            msg = "Tag '{}' dataset is empty. Nothing to do.".format(tagpath)
            logger.info(msg)
            summary["message"] = msg
            summary["success"] = True
            _maybe_popup("HVSV2 Cleanup", msg)
            return summary

        # 3) Locate the 'Identifier' column
        col_names = [ds.getColumnName(i) for i in range(ds_col_count)]
        try:
            id_col_idx = col_names.index("Identifier")
        except ValueError:
            msg = "Column 'Identifier' not found in tag dataset at '{}'.".format(tagpath)
            logger.warn(msg)
            summary["message"] = msg
            _maybe_popup("HVSV2 Cleanup", msg)
            return summary  # No raise

        # 4) Filter out rows where Identifier matches a ProductionOrder
        kept_rows = []
        removed = 0
        for r in range(ds_row_count):
            ident_val = ds.getValueAt(r, id_col_idx)
            ident_norm = _norm(ident_val)
            if ident_norm in production_orders:
                removed += 1
            else:
                kept_rows.append([ds.getValueAt(r, c) for c in range(ds_col_count)])

        summary["rowsRemoved"] = removed
        summary["rowsAfter"] = len(kept_rows)

        
        if removed == 0:
            msg = ("HVSV2 refresh complete.\n"
                   "Removed: 0\n"
                   "Before: {b}\nAfter: {a}\n"
                   "Scanned ProductionOrders: {po}").format(
                        b=summary["rowsBefore"], a=summary["rowsAfter"],
                        po=summary["productionOrdersCount"])
            logger.info(msg)
            summary["message"] = msg
            summary["success"] = True
            _maybe_popup("HVSV2 Cleanup", msg)
            return summary

        # 5) Write the filtered dataset back to the tag
        from system.dataset import toDataSet
        new_ds = toDataSet(col_names, kept_rows)
        write_results = system.tag.writeBlocking([tagpath], [new_ds])

        # Evaluate write result (no raise)
        wr = write_results[0]
        try:
            err = wr.getErrorMessage()
        except AttributeError:
            err = None 

        if err:
            msg = "Write to '{}' reported error: {}".format(tagpath, err)
            logger.warn(msg)
            summary["message"] = msg
            _maybe_popup("HVSV2 Cleanup", msg)
            return summary

        msg = ("HVSV2 refresh complete.\n"
               "Removed: {r}\n"
               "Before: {b}\nAfter: {a}\n"
               "Scanned ProductionOrders: {po}").format(
                    r=removed, b=summary["rowsBefore"], a=summary["rowsAfter"],
                    po=summary["productionOrdersCount"])
        logger.info(msg)
        summary["message"] = msg
        summary["success"] = True
        _maybe_popup("HVSV2 Cleanup", msg)
        return summary

    except Exception as ex:
        # Catch-all: log and return summary;
        msg = "HVSV2 cleanup encountered an error: {}".format(ex)
        logger.error(msg)
        summary["message"] = msg
        _maybe_popup("HVSV2 Cleanup", msg)
        return summary