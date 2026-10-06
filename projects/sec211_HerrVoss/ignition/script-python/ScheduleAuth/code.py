
# HVSV2 -> SQL writer 
#

import re
from datetime import datetime, timedelta

# --- CONFIG
DB_CONN_NAME = "JeffCity2EngineeringTestServer"  # Gateway database connection name
SQL_TABLE = "[Engineering].[dbo].[Herr_Voss_Schedule]"
SQL_INSERT = (
    "INSERT INTO {table} "
    "(Identifier, Date, Part_ID, Raw_Coil, Additional, Quantity, ECSQTY, Source_File, DownloadTime, HVIndex) "
    "VALUES (?,?,?,?,?,?,?,?,?,?)"
).format(table=SQL_TABLE)

# HVSV2 dataset tag path
HVSV2_TAG_PATH = "[default]Sec211/Hervoss/DataAutomation/HVSV2"

# --- HELPER
def _coerce_str(x):
    try:
        return ("" if x is None else unicode(x)).strip()
    except:
        return ""

def _coerce_int(x, default=None):
    try:
        if x is None or (isinstance(x, basestring) and x.strip() == ""):
            return default
        return int(float(x))
    except:
        return default

def _excel_serial_to_date(val):
    """Accepts Excel serial, ISO/date strings, or returns None if not parseable."""
    if val is None:
        return None
    try:
        # python datetime
        if hasattr(val, "year"):
            return val
    except:
        pass
    #  python datetime
    try:
        f = float(val)
        if 1 <= f <= 80000:
            return datetime(1899, 12, 30) + timedelta(days=f)
    except:
        pass
    # String parse
    s = _coerce_str(val)
    if not s:
        return None
    try:
        return system.date.parse(s)
    except:
        fmts = [
            "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y",
            "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m-%d-%Y",
            "%b %d, %Y, %I:%M:%S %p", "%b %d, %Y, %I:%M %p",
        ]
        for fmt in fmts:
            try:
                return datetime.strptime(s, fmt)
            except:
                pass
    return None

def _is_dataset(val):
    try:
        _ = val.getColumnCount(); _ = val.getRowCount(); _ = val.getColumnNames()
        return True
    except:
        return False

def _read_hvsv2():
    """Reads the HVSV2 dataset tag; returns (columns, list_of_row_dicts)."""
    qv = system.tag.readBlocking([HVSV2_TAG_PATH])[0]
    if not qv.quality.isGood():
        raise ValueError("HVSV2 tag read has bad quality: %s" % qv.quality)

    ds = qv.value
    if not _is_dataset(ds):
        raise ValueError("HVSV2 tag is not a Dataset (type=%s)" % type(ds))

    cols = list(ds.getColumnNames())
    rows = []
    for r in range(ds.getRowCount()):
        d = {}
        for c in cols:
            d[c] = ds.getValueAt(r, c)
        rows.append(d)
    return cols, rows

def _canonical_source(s):
    return _coerce_str(s).upper()

def _normalize_additional_for_check(val):
    """Case-insensitive trim for 'Weid 1' / 'Weid 7' checks."""
    t = _coerce_str(val)
    return t.strip().lower()

def _ecs_row_is_allowed(additional):
    t = _normalize_additional_for_check(additional)
    # Accept exactly 'weid 1' or 'weid 7' (case-insensitive).
    return t == "weid 1" or t == "weid 7"

def _enforce_for_insert(row, ordinal, now_ts, debug=False):
    """
    Shapes the row args to match the SQL INSERT (INCLUDES 'Not Serialized'):
      - Identifier: keep as-is (including "Not Serialized")
      - Defaults: Raw_Coil="NONE" if blank; Part_ID="NF" if blank
      - Date falls back to now if missing/unparseable
      - Source File truncated to 20 chars
      - HVIndex uses row value or running ordinal
    """
    ident = _coerce_str(row.get("Identifier")) or "Not Serialized"

    qty = _coerce_int(row.get("Quantity"), 0)
    ecsqty = _coerce_int(row.get("ECSQTY"), None)

    date_val = row.get("Date", None)
    date_val = _excel_serial_to_date(date_val) or now_ts

    raw_coil = _coerce_str(row.get("Raw Coil")) or "NONE"
    src_file = _coerce_str(row.get("Source File")) or None
    additional = _coerce_str(row.get("Additional")) or None
    part_id = _coerce_str(row.get("Part ID")) or "NF"

    hvindex = _coerce_int(row.get("HVIndex"), None)
    if hvindex is None:
        hvindex = ordinal

    # Limit Source File length like before
    MAX_SOURCEFILE_LEN = 20
    if src_file:
        src_file = src_file[:MAX_SOURCEFILE_LEN]

    args = [
        ident, date_val, part_id, raw_coil,
        additional, qty, ecsqty, src_file,
        now_ts, hvindex
    ]
    return args

# --- RUNNER
def run(debug=False, notify=False):
    """
    Reads HVSV2 tag, filters rows per spec, DELETEs table, writes filtered rows to SQL.
    Includes rows where Identifier == "Not Serialized".
    Returns True on success, False on error (and logs the error).
    """
    log = system.util.getLogger("MERGER_HVSV2_SQL")
    tx = None
    try:
        if debug:
            log.info("[MERGER_HVSV2_SQL] Starting filtered write from HVSV2 -> SQL...")

        # 1) Load HVSV2
        cols, rows = _read_hvsv2()
        if debug:
            log.info("HVSV2 read: rows=%d cols=%d" % (len(rows), len(cols)))

        # 2) Apply filter 
        filtered = []
        for r in rows:
            src = _canonical_source(r.get("Source File"))
            if src != "ECS":
                filtered.append(r)
            else:
                if _ecs_row_is_allowed(r.get("Additional")):
                    filtered.append(r)
                else:
                    if debug:
                        log.info("Excluded ECS row: Additional=%s, Identifier=%s"
                                 % (_coerce_str(r.get("Additional")), _coerce_str(r.get("Identifier"))))

        if debug:
            log.info("Filtered rows to insert: %d (of %d total)" % (len(filtered), len(rows)))

        # 3) DELETE
        clear_query = "DELETE FROM [Engineering].[dbo].[Herr_Voss_Schedule]"
        system.db.runUpdateQuery(clear_query, DB_CONN_NAME)
        if debug:
            log.info("[SQL] Cleared table via DELETE: %s" % SQL_TABLE)

        if not filtered:
            msg = "[Results] HVSV2 -> SQL\nInserted=0\nTotalRead=%d\nFiltered=0" % len(rows)
            if debug: log.info(msg)
            if notify:
                try: system.gui.messageBox(msg, "MERGER_HVSV2_SQL")
                except: log.info(msg)
            return True  # Successful run

        # 4) Insert 
        now_ts = system.date.now()
        tx = system.db.beginTransaction(DB_CONN_NAME, system.db.SERIALIZABLE, 5000)

        inserted = 0
        for ordinal, r in enumerate(filtered, start=1):
            args = _enforce_for_insert(r, ordinal, now_ts, debug=debug)
            system.db.runPrepUpdate(SQL_INSERT, args, DB_CONN_NAME, tx)
            inserted += 1

        system.db.commitTransaction(tx)

        msg = "[Results] HVSV2 -> SQL\nInserted=%d\nTotalRead=%d\nFiltered=%d" % (inserted, len(rows), len(filtered))
        if debug: log.info(msg)
        if notify:
            try: system.gui.messageBox(msg, "MERGER_HVSV2_SQL")
            except: log.info(msg)
        return True

    except Exception as ex:
        if tx:
            try: system.db.rollbackTransaction(tx)
            except: pass
        err = "MERGER_HVSV2_SQL.run() failed: %s" % ex
        system.util.getLogger("MERGER_HVSV2_SQL").error(err)
        if notify:
            try: system.gui.errorBox(err, "MERGER_HVSV2_SQL")
            except: pass
        return False
    finally:
        if tx:
            try: system.db.closeTransaction(tx)
            except: pass


def writeOnce(debug=False):
    return run(debug=debug, notify=False)