
# the point of this script is to essentially validate real process against ECS / BOMS. This behaves primarily as a scheduling software to supercede ECS and align schedule
# closer to the real process. If ECS is a bucket, this script floats what is important to the top, in an order that makes sense, with added improvements to reduce changeovers.
# this tool is very important because of inventory contraints. We can't afford to make everything. Nowhere to store the extra, and might be plenty of the wrong stuff.
# the primary data sources for the scripting is from stored procs that more dyanmically schedule what is needed. Using stored procs to ensure they are maintained and reliable.
# MERGER
import re
from datetime import datetime, timedelta
# TAGS
TAG_PATHS = {
 "3PHTT": "[default]Sec211/Hervoss/DataAutomation/3PHTT",
 "3PHU": "[default]Sec211/Hervoss/DataAutomation/3PHU",
 "BASING": "[default]Sec211/Hervoss/DataAutomation/BASING",
 "TFR": "[default]Sec211/Hervoss/DataAutomation/TFR",
 "Submersibles": "[default]Sec211/Hervoss/DataAutomation/Submersibles",
 "1PH Steel": "[default]Sec211/Hervoss/DataAutomation/1PH Steel",
 "Kanban": "[default]Sec211/Hervoss/DataAutomation/Kanban",
 "3PHBlank": "[default]Sec211/Hervoss/DataAutomation/3PHBlank",
 "HVSV2_OUT": "[default]Sec211/Hervoss/DataAutomation/HVSV2",
 "MERGER_DEBUG": "[default]Sec211/Hervoss/DataAutomation/MERGER_Debug",
}
SOURCE_LABELS = {
 "3PHTT": "3PHTT",
 "3PHU": "3PHU",
 "BASING": "BASES",
 "TFR": "3PHTFR",
 "Submersibles": "sub",
 "1PH Steel": "ST",
 "Kanban": "KanbanSteel",
 "3PHBlank": "3PHBlankCUT",
}
# Named Query path
HVSCREEN_NAMED_QUERY_PATH = "HVSCREEN"
HVSCREEN_NAMED_QUERY_PARAMS = {}
INCLUDE_IN_PROGRESS = True # If False, exclude "In progress" rows from HVSCREEN
PARTIAL_ON_LAST = True # allow partial usage on the last PO to form exact demand
# dataset columns that go to the tag
MASTER_COLS = ["Identifier","Date","Part ID","Raw Coil","Additional","Quantity","ECSQTY","Source File","HVIndex"]
# Functional Part ID pattern (e.g., 15H66PA370)
FUNC_ID_RE = re.compile(r'^[0-9A-Z]{2}H[0-9A-Z]{3}A[0-9A-Z]{3}$')
# Width decoding tables
DECIMAL_SUFFIX = {
 "A": 0.05, "B": 0.15, "C": 0.25, "D": 0.35,
 "G": 0.45, "H": 0.55, "J": 0.65, "P": 0.75, "T": 0.85, "R": 0.95
}
HUNDREDS_PREFIX = {"A": 100.0, "B": 110.0, "C": 120.0, "D": 130.0, "G": 140.0}
WIDTH_SEGMENT_RE = re.compile(r'H([0-9A-Z]{3})A')
def _width_from_code(code):
 try:
  if not isinstance(code, basestring) or len(code) != 3:
   return None
  code = code.upper()
  c0, c1, c2 = code[0], code[1], code[2]
  if c0.isdigit():
   if c1.isdigit() and c2 in DECIMAL_SUFFIX:
    return int(c0 + c1) + DECIMAL_SUFFIX[c2]
   return None
  if c0 in HUNDREDS_PREFIX and c1.isdigit() and c2 in DECIMAL_SUFFIX:
   return HUNDREDS_PREFIX[c0] + int(c1) + DECIMAL_SUFFIX[c2]
  return None
 except:
  return None
def _decode_width_from_partid(part_id):
 s = _coerce_str(part_id).upper()
 if not s:
  return None
 m = WIDTH_SEGMENT_RE.search(s)
 if not m:
  return None
 return _width_from_code(m.group(1))
def _width_sort_preamble(row):
 w = _decode_width_from_partid(row.get("Part ID"))
 if w is None:
  return (1, float("inf"))
 return (0, float(w))
# DATASET calls
def _empty_dataset():
 return system.dataset.toDataSet([], [])
def _is_dataset(val):
 try:
  _ = val.getColumnCount(); _ = val.getRowCount(); _ = val.getColumnNames()
  return True
 except:
  return False
def _read_dataset_tag(path, debug=False):
 log = system.util.getLogger("MERGER")
 try:
  qv = system.tag.readBlocking([path])[0]
  if not qv.quality.isGood():
   if debug: log.warn("Bad quality: %s (%s) -> empty dataset" % (path, qv.quality))
   return _empty_dataset()
  val = qv.value
  if not _is_dataset(val):
   if debug: log.warn("Not a Dataset at %s (type=%s) -> empty dataset" % (path, type(val)))
   return _empty_dataset()
  if debug: log.info("Read %s rows=%d cols=%d" % (path, val.getRowCount(), val.getColumnCount()))
  return val
 except Exception as ex:
  if debug: log.warn("Read failed %s: %s -> empty dataset" % (path, ex))
  return _empty_dataset()
def _ds_to_list_of_dicts(ds):
 cols = list(ds.getColumnNames())
 out = []
 for r in range(ds.getRowCount()):
  row = {}
  for c in cols:
   row[c] = ds.getValueAt(r, c)
  out.append(row)
 return cols, out
def _to_dataset(rows, columns):
 data = []
 for row in rows:
  cleaned = _enforce_types(row)
  data.append([cleaned.get(c, None) for c in columns])
 return system.dataset.toDataSet(columns, data)
def _write_dataset_tag(path, ds):
 system.tag.writeBlocking([path], [ds])
def _coerce_str(x):
 try:
  return ("" if x is None else unicode(x)).strip()
 except:
  return ""
def _coerce_int(x, default=0):
 try:
  if x is None or (isinstance(x, basestring) and x.strip()==""):
   return default
  return int(float(x))
 except:
  return default
def _excel_serial_to_date(val):
 if val is None: return None
 try:
  f = float(val)
  if 1 <= f <= 80000:
   return datetime(1899,12,30) + timedelta(days=f)
 except:
  pass
 s = _coerce_str(val)
 if not s: return None
 fmts = [
  "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y",
  "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m-%d-%Y",
  "%b %d, %Y, %I:%M:%S %p", "%b %d, %Y, %I:%M %p",
 ]
 for fmt in fmts:
  try: return datetime.strptime(s, fmt)
  except: pass
 try: return system.date.parse(s)
 except: return None
def _getcol(rows, headers, *candidates):
 for cand in candidates:
  if isinstance(cand, basestring) and cand in headers:
   return [row.get(cand, None) for row in rows]
 for cand in candidates:
  if isinstance(cand, basestring) and len(cand)==1 and cand.isalpha():
   idx = ord(cand.upper()) - ord('A')
   if 0 <= idx < len(headers):
    name = headers[idx]
    return [row.get(name, None) for row in rows]
 return [None]*len(rows)
def _canonical_additional(val):
 t = _coerce_str(val)
 if not t: return ""
 tl = t.lower()
 if tl in ("600 ton press","600t press","600 ton","600t"): return "600 Ton Press"
 if tl in ("weid 7","weid7","weid-7","weid #7","weid#7","weid seven"): return "Weid 7"
 return t
def _canon_alnum(s):
 t = _coerce_str(s).upper()
 if not t: return ""
 return re.sub(r'[^0-9A-Z]', '', t)
def _source_name(key): return SOURCE_LABELS.get(key, key)
# hard formatting
def _enforce_types(row):
 out = dict(row)
 for key in ("Identifier","Part ID","Raw Coil","Additional","Source File"):
  v = out.get(key, None)
  out[key] = (_coerce_str(v) if v is not None and _coerce_str(v)!="" else None)
 if out.get("Identifier") in (None, ""):
  out["Identifier"] = ""
 for key in ("Quantity","ECSQTY","HVIndex"):
  v = out.get(key, None)
  if isinstance(v, basestring) and v.strip()=="":
   out[key] = None
  else:
   try:
    out[key] = int(v) if v is not None else None
   except:
    out[key] = None
 d = out.get("Date", None)
 out["Date"] = _excel_serial_to_date(d) if d and not hasattr(d, "year") else d
 return out
# HEADER Resolution
def __norm_header(s):
 return re.sub(r'[^0-9a-z]', '', _coerce_str(s).lower())
def __map_headers(headers):
 return { __norm_header(h): h for h in headers }
def __hget(row, hmap, *names):
 for cand in names:
  k = __norm_header(cand)
  if k in hmap: return row.get(hmap[k], None)
 return None
# HVSCREEN -- ECS live touch point and debug/protection items
def _read_hvscreen_dataset(debug=False):
 log = system.util.getLogger("MERGER")
 try:
  ds = system.db.runNamedQuery(HVSCREEN_NAMED_QUERY_PATH, HVSCREEN_NAMED_QUERY_PARAMS)
  if debug: log.info("HVSCREEN via NQ (client/designer): %d rows" % ds.getRowCount())
 except TypeError:
  proj = system.util.getProjectName() or ""
  if not proj:
   raise ValueError("Named Query 'HVSCREEN' requires project name in Gateway scope.")
  ds = system.db.runNamedQuery(proj, HVSCREEN_NAMED_QUERY_PATH, HVSCREEN_NAMED_QUERY_PARAMS)
  if debug: log.info("HVSCREEN via NQ (gateway): %d rows" % ds.getRowCount())
 _assert_hvscreen_ready(ds)
 return ds
def _assert_hvscreen_ready(ds):
 if not _is_dataset(ds):
  raise ValueError("HVSCREEN did not return a Dataset.")
 if ds.getRowCount() == 0:
  raise ValueError("HVSCREEN returned 0 rows.")
 cols = set(__norm_header(c) for c in list(ds.getColumnNames()))
 req = set(__norm_header(x) for x in ("PO", "code", "left"))
 miss = req.difference(cols)
 if miss:
  raise ValueError("HVSCREEN missing required columns (normalized): %s; seen=%s" %
  (sorted(miss), sorted(list(ds.getColumnNames()))))
def peek_hvscreen(n=10):
 log = system.util.getLogger("MERGER")
 ds = _read_hvscreen_dataset(debug=False)
 headers, rows = _ds_to_list_of_dicts(ds)
 hmap = __map_headers(headers)
 out = []
 for row in rows[:min(n,len(rows))]:
  out.append({
  "PO": _coerce_str(__hget(row, hmap, " PO","PO")),
  "Part": _coerce_str(__hget(row, hmap, "code","Code")),
  "Qty": _coerce_int(__hget(row, hmap, "Left"), 0),
  "Status": _coerce_str(__hget(row, hmap, "Product Status","ProductStatus")),
  "Sched": _excel_serial_to_date(
   __hget(row, hmap, "ScheduledStart") or
   __hget(row, hmap, "ReleaseDate") or
   __hget(row, hmap, "startDate")
  ),
  })
 log.info("HVSCREEN peek: %s" % out)
 return out
# BUILDER
def _empty_master_row():
 return {"Identifier":None,"Date":None,"Part ID":None,"Raw Coil":None,
 "Additional":None,"Quantity":None,"ECSQTY":None,"Source File":None, "HVIndex": None}
# 3PHTT
def _build_bucket1_phtt(headers, rows):
 out = []
 A = _getcol(rows, headers, "A")
 B = _getcol(rows, headers, "B")
 C = _getcol(rows, headers, "C")
 F = _getcol(rows, headers, "F")
 J = _getcol(rows, headers, "Matched_Raw_Coil", "J")
 for i in range(len(rows)):
  r = _empty_master_row()
  r["Date"] = _excel_serial_to_date(A[i])
  r["Additional"] = _canonical_additional(B[i])
  r["Quantity"] = _coerce_int(F[i], 0)
  r["Raw Coil"] = _coerce_str(J[i]) or None
  pid = _coerce_str(C[i]).upper()
  r["Part ID"] = pid if FUNC_ID_RE.match(pid) else None
  out.append(r)
 return out
# 3PHU
def _build_bucket1_phu(headers, rows):
 out = []
 Order = _getcol(rows, headers, "Order")
 Part = _getcol(rows, headers, "Materials_Clean")
 Raw = _getcol(rows, headers, "Matched_Raw_Coil")
 Left = _getcol(rows, headers, "Left", "Quantity")
 Routing = _getcol(rows, headers, "Routing", "Additional")
 for i in range(len(rows)):
  r = _empty_master_row()
  r["Identifier"] = _coerce_str(Order[i])
  r["Part ID"] = _coerce_str(Part[i]) or None
  r["Raw Coil"] = _coerce_str(Raw[i]) or None
  r["Quantity"] = _coerce_int(Left[i], 0)
  r["Additional"] = _canonical_additional(Routing[i])
  out.append(r)
 return out
# BASES
def _build_bucket1_bases(headers, rows):
 out = []
 A = _getcol(rows, headers, headers[0] if headers else "A")
 B = _getcol(rows, headers, headers[1] if len(headers)>1 else "B")
 C = _getcol(rows, headers, headers[2] if len(headers)>2 else "C")
 MR = _getcol(rows, headers, "Matched_Raw_Coil", headers[3] if len(headers)>3 else "D")
 for i in range(len(rows)):
  r = _empty_master_row()
  r["Part ID"] = _coerce_str(A[i]) or None
  r["Date"] = _excel_serial_to_date(B[i])
  r["Quantity"] = _coerce_int(C[i], 0)
  r["Raw Coil"] = _coerce_str(MR[i]) or None
  out.append(r)
 return out
# TFR
def _build_bucket1_tfr(headers, rows):
 out = []
 Order = _getcol(rows, headers, "Order")
 Item = _getcol(rows, headers, "Item", "Part ID")
 Raw = _getcol(rows, headers, "Matched_Raw_Coil")
 Left = _getcol(rows, headers, "Left", "Quantity")
 Routing = _getcol(rows, headers, "Routing", "Additional")
 for i in range(len(rows)):
  r = _empty_master_row()
  r["Identifier"] = _coerce_str(Order[i])
  r["Part ID"] = _coerce_str(Item[i]) or None
  r["Raw Coil"] = _coerce_str(Raw[i]) or None
  r["Quantity"] = _coerce_int(Left[i], 0)
  r["Additional"] = _canonical_additional(Routing[i])
  out.append(r)
 return out
# Submersibles
def _build_bucket1_sub(headers, rows):
 out = []
 try:
  tmp = []
  for row in rows:
   loc = _coerce_str(row.get("B") if "B" in headers else row.get("Location"))
   mih = _coerce_str(row.get("G") if "G" in headers else row.get("MIH"))
   if loc.lower() != "metal fab w7": continue
   if mih and mih.upper() != "MIH": continue
   dt = _excel_serial_to_date(row.get("C"))
   serial = row.get("A")
   pos = _coerce_str(row.get("Position") if "Position" in headers else row.get("F"))
   if pos.lower() == "console": continue
   tmp.append({"serial":serial,"date":dt})
  tmp.sort(key=lambda x: (x["date"] if x["date"] else datetime.max))
  keep, seen = [], set()
  for t in tmp:
   s = _coerce_str(t["serial"])
   if not s or s in seen: continue
   keep.append(s); seen.add(s)
   if len(keep)>=7: break
  for row in rows:
   if _coerce_str(row.get("A")) not in keep: continue
   r = _empty_master_row()
   r["Identifier"] = _coerce_str(row.get("A"))
   r["Additional"] = _canonical_additional((_coerce_str(row.get("B"))+" "+_coerce_str(row.get("G"))).strip())
   r["Date"] = _excel_serial_to_date(row.get("C"))
   r["Raw Coil"] = _coerce_str(row.get("Matched_Raw_Coil") or row.get("N"))
   r["Part ID"] = _coerce_str(row.get("Functional_Part_ID") or row.get("H")) or None
   r["Quantity"] = 1
   out.append(r)
 except:
  pass
 return out
# ST
def _build_bucket2_st(headers, rows):
 out = []
 A = _getcol(rows, headers, headers[0] if headers else "A")
 B = _getcol(rows, headers, headers[1] if len(headers)>1 else "B")
 C = _getcol(rows, headers, headers[2] if len(headers)>2 else "C")
 MR = _getcol(rows, headers, "Matched_Raw_Coil", headers[3] if len(headers)>3 else "D")
 for i in range(len(rows)):
  r = _empty_master_row()
  r["Additional"] = _canonical_additional(A[i])
  r["Part ID"] = _coerce_str(B[i]) or None
  r["Quantity"] = _coerce_int(C[i], 0)
  r["Raw Coil"] = _coerce_str(MR[i]) or None
  out.append(r)
 return out
# Kanban
def _build_bucket2_kanban(headers, rows):
 out = []
 PO = _getcol(rows, headers, "ProductionOrder", "A")
 Loc = _getcol(rows, headers, "Location", "B")
 PID = _getcol(rows, headers, "Blank", "D", "Part ID")
 Dt = _getcol(rows, headers, "Date", "E")
 Raw = _getcol(rows, headers, "Matched_Raw_Coil","Matched_raw","Matched_raw_coil","F")
 Qty = _getcol(rows, headers, "Quantity", "H")
 for i in range(len(rows)):
  r = _empty_master_row()
  r["Identifier"] = _coerce_str(PO[i])
  r["Additional"] = _canonical_additional(Loc[i])
  r["Part ID"] = _coerce_str(PID[i]) or None
  r["Date"] = _excel_serial_to_date(Dt[i])
  r["Raw Coil"] = _coerce_str(Raw[i]) or None
  r["Quantity"] = _coerce_int(Qty[i], 0)
  out.append(r)
 return out
# 3PHBlankCUT
def _build_bucket3_blankcut(headers, rows):
 out = []
 Part = _getcol(rows, headers, "Part ID", "Part")
 Need = _getcol(rows, headers, "Needed Quantity", "Quantity")
 Locs = _getcol(rows, headers, "Locations", "Additional")
 Raw = _getcol(rows, headers, "Raw Coil")
 for i in range(len(rows)):
  r = _empty_master_row()
  r["Part ID"] = _coerce_str(Part[i]) or None
  r["Quantity"] = _coerce_int(Need[i], 0)
  r["Additional"] = _canonical_additional(Locs[i])
  r["Raw Coil"] = _coerce_str(Raw[i]) or None
  out.append(r)
 return out
# SORTING
def _sort_bucket1_section(rows, source_prefix):
 sp = _coerce_str(source_prefix).lower()
 def key_phtt(r):
  add = _coerce_str(r.get("Additional"))
  hasw, w = _width_sort_preamble(r)
  raw = _coerce_str(r.get("Raw Coil"))
  dt = r.get("Date") or datetime.max
  ident = _coerce_str(r.get("Identifier"))
  return (add, hasw, w, raw, dt, ident)
 def key_other(r):
  hasw, w = _width_sort_preamble(r)
  raw = _coerce_str(r.get("Raw Coil"))
  add = _coerce_str(r.get("Additional")) if sp.startswith("3phtt") else "Not Serialized"
  dt = r.get("Date") or datetime.max
  ident = _coerce_str(r.get("Identifier"))
  return (hasw, w, raw, add, dt, ident)

 # >>> CHANGE: BASING must group by Raw Coil, then width ascending
 if sp.startswith("basing"):
  return _sort_rawcoil_then_width_asc(rows)

 keyfunc = key_phtt if sp.startswith("3phtt") else key_other
 return sorted(rows, key=keyfunc)
def _sort_bucket2_section(rows):
 def key(r):
  hasw, w = _width_sort_preamble(r)
  raw = _coerce_str(r.get("Raw Coil"))
  dt = r.get("Date") or datetime.max
  pid = _coerce_str(r.get("Part ID"))
  return (hasw, w, raw, dt, pid)
 return sorted(rows, key=key)
def _sort_bucket3_section(rows):
 def key(r):
  hasw, w = _width_sort_preamble(r)
  raw = _coerce_str(r.get("Raw Coil"))
  pid = _coerce_str(r.get("Part ID"))
  return (hasw, w, raw, pid)
 return sorted(rows, key=key)

# >>> CHANGE: Strict Raw-Coil-first sorter, width ascending within coil (unknown widths last)
def _sort_rawcoil_then_width_asc(rows):
 def key(r):
  raw = _coerce_str(r.get("Raw Coil"))
  raw_is_empty = (raw is None or raw == "")
  hasw, w = _width_sort_preamble(r)  # (0, width) when decoded; (1, inf) when unknown
  dt = r.get("Date") or datetime.max
  pid = _coerce_str(r.get("Part ID"))
  # Sort: real raw coils first, then empty; within raw, decodable widths first, ascending; then date, pid
  return (raw_is_empty, raw or "", hasw, float(w), dt, pid)
 return sorted(rows, key=key)

# BUILD HVSV2
def _build_hvsv2(debug=False):
 log = system.util.getLogger("MERGER")
 def read_and_build(key, builder, sorter):
  ds = _read_dataset_tag(TAG_PATHS[key], debug=debug)
  headers, rows = _ds_to_list_of_dicts(ds)
  mapped = builder(headers, rows)
  if not mapped: return []
  for r in mapped: r["Source File"] = _source_name(key)
  return sorter(mapped) if sorter else mapped
 b1, b2 = [], []
 b1 += read_and_build("3PHTT", _build_bucket1_phtt, lambda rows: _sort_bucket1_section(rows, "3PHTT"))
 #b1 += read_and_build("3PHU", _build_bucket1_phu, lambda rows: _sort_bucket1_section(rows, "3PHU"))
 b1 += read_and_build("BASING",_build_bucket1_bases,lambda rows: _sort_bucket1_section(rows, "BASING"))  # >>> CHANGE: BASING uses RawCoil→Width ASC
 #b1 += read_and_build("TFR", _build_bucket1_tfr, lambda rows: _sort_bucket1_section(rows, "TFR"))
 b1 += read_and_build("Submersibles", _build_bucket1_sub, lambda rows: _sort_bucket1_section(rows, "Submersibles"))
 # >>> CHANGE: ST (1PH Steel) must use RawCoil→Width ASC sorter; Kanban stays legacy
 b2 += read_and_build("1PH Steel", _build_bucket2_st, _sort_rawcoil_then_width_asc)
 b2 += read_and_build("Kanban", _build_bucket2_kanban, _sort_bucket2_section)
 b3 = read_and_build("3PHBlank", _build_bucket3_blankcut, _sort_bucket3_section)
 combined = (b1 or []) + (b2 or []) + (b3 or [])
 for r in combined:
  ident = _coerce_str(r.get("Identifier"))
  r["Identifier"] = ident if ident and ident.lower() != "nan" else "Not Serialized"
  r["Quantity"] = _coerce_int(r.get("Quantity"), 0)
  r["ECSQTY"] = r.get("ECSQTY")
 norm = [_enforce_types(r) for r in combined]
 if debug: log.info("HVSV2 base rows: %d" % len(norm))
 return norm

# HVSCREEN AVAILABILITY // matchback!
def _load_hvscreen_availability(debug=False):
 """
 Return availability dict keyed by normalized part variants, each item includes:
 Order, Qty, ScheduledStart, Status, Code (original code string).
 """
 log = system.util.getLogger("MERGER")
 ds = _read_hvscreen_dataset(debug=debug)
 headers, rows = _ds_to_list_of_dicts(ds)
 hmap = __map_headers(headers)
 raw_items = []
 for row in rows:
  part_name = __hget(row, hmap, "code"," code","Code")
  if not part_name: continue
  status = _coerce_str(__hget(row, hmap, "Product Status","ProductStatus"))
  if not INCLUDE_IN_PROGRESS and status and status.lower() == "in progress":
   continue
  qty = _coerce_int(__hget(row, hmap, "Left"), 0)
  if qty <= 0: continue
  po = _coerce_str(__hget(row, hmap, " PO","PO"))
  dt = (__hget(row, hmap, "ScheduledStart") or
   __hget(row, hmap, "ReleaseDate") or
   __hget(row, hmap, "startDate"))
  dt = _excel_serial_to_date(dt)
  item = {"Order": po, "Qty": int(qty), "ScheduledStart": dt, "Status": status, "Code": _coerce_str(part_name)}
  raw_items.append((part_name, item))
 def _itkey(tup):
  pn, it = tup
  d = it["ScheduledStart"] if it["ScheduledStart"] else datetime.max
  return (_canon_alnum(pn), d, it["Order"])
 raw_items.sort(key=_itkey)
 availability = {}
 for pn, item in raw_items:
  for k in _key_variants(pn):
   availability.setdefault(k, []).append(item)
 if debug:
  total = sum(len(v) for v in availability.values())
  log.info("HVSCREEN availability keyed entries: %d keys / %d items" % (len(availability), total))
 return availability
def _key_variants(s):
 raw = _coerce_str(s)
 if not raw: return []
 exact = raw.strip()
 upper = exact.upper()
 alnum = _canon_alnum(upper)
 out, seen = [], set()
 for k in (exact, upper, alnum):
  if k and k not in seen:
   out.append(k); seen.add(k)
 return out
def _gather_candidates(availability, part_id):
 cands, seen = [], set()
 for k in _key_variants(part_id):
  for it in availability.get(k, []):
   oid = id(it)
   if oid in seen: continue
   seen.add(oid)
   if int(it.get("Qty", 0)) > 0:
    cands.append(it)
 cands.sort(key=lambda it: (it.get("ScheduledStart") or datetime.max, it.get("Order")))
 return cands
# ALLOCATION
def _exact_combo_by_qty(cands, target, max_consider=700):
 c = cands[:max_consider]
 dp = {0: []}
 for i, it in enumerate(c):
  q = int(it.get("Qty", 0))
  for cur, path in list(dp.items()):
   new = cur + q
   if new > target: continue
   if new not in dp:
    dp[new] = path + [i]
   if new == target:
    return dp[new]
 return None
def _allocate_for_row(part_id, demand, availability, used_orders, debug=False):
 log = system.util.getLogger("MERGER")
 cands = [c for c in _gather_candidates(availability, part_id) if c["Order"] not in used_orders]
 if debug:
  log.info("Alloc try: Part=%s demand=%d \n candidates=%s" %
  (part_id, demand, [(c["Order"], c["Qty"]) for c in cands]))
 if demand <= 0 or not cands:
  return None
 # 1) exact single
 for it in cands:
  if int(it["Qty"]) == demand:
   used_orders.add(it["Order"])
   return [ (it["Order"], demand, it) ]
 # 2) exact combo
 combo_idx = _exact_combo_by_qty(cands, demand)
 if combo_idx:
  result = []
  for i in combo_idx:
   it = cands[i]
   q = int(it["Qty"])
   used_orders.add(it["Order"])
   result.append((it["Order"], q, it))
  return result
 # 3) oldest-first; optionally partial
 remaining = demand
 result = []
 for it in cands:
  if remaining <= 0: break
  q = int(it["Qty"])
  take = q if not PARTIAL_ON_LAST or q <= remaining else remaining
  used_orders.add(it["Order"])
  result.append((it["Order"], take, it))
  remaining -= take
 if sum(t for _, t, _ in result) <= 0:
  return None
 return result
# ECS UNMATCHED BUCKET (HVSCREEN rows not used in matchback)
def _build_bucket_hvscreen_unmatched(used_pairs, debug=False):
 """
 Build a bucket of HVSCREEN rows that were NOT matched back during allocation.
 used_pairs: set of tuples (canon_alnum(Code), PO) collected from actual allocations.
 Sorting: ONLY by Date (ScheduledStart) ascending.
 """
 log = system.util.getLogger("MERGER")
 ds = _read_hvscreen_dataset(debug=debug)
 headers, rows = _ds_to_list_of_dicts(ds)
 hmap = __map_headers(headers)
 out = []
 for row in rows:
  po = _coerce_str(__hget(row, hmap, " PO","PO"))
  code = _coerce_str(__hget(row, hmap, "code","Code"))
  if not code:
   # If there's no code, we can't key; include it if PO not used (basically if there is no part ID, it still reports the ecs order)
   pass
  else:
   key = (_canon_alnum(code), po)
   if key in used_pairs:
    continue # HVSCREEN line was matched back by allocation; skip
  r = _empty_master_row()
  r["Identifier"] = po or "Not Serialized"
  r["Quantity"] = _coerce_int(__hget(row, hmap, "Quantity"), 0) # keep "Quantity" as-is source column
  r["ECSQTY"] = _coerce_int(__hget(row, hmap, "Left"), 0)
  r["Date"] = _excel_serial_to_date(
   __hget(row, hmap, "ScheduledStart") or
   __hget(row, hmap, "ReleaseDate") or
   __hget(row, hmap, "startDate")
  )
  r["Part ID"] = _coerce_str(__hget(row, hmap, "code","Code")) or None
  # Next Op missing -> "NULL" (as text value)
  add_val = _coerce_str(__hget(row, hmap, "Next Op","NextOp"))
  r["Additional"] = add_val if add_val else "NULL"
  r["Source File"]= "ECS" # hardcoded value to isolate subtypes
  out.append(r)
 # Sort ONLY by Date for this ECS bucket
 out.sort(key=lambda x: x.get("Date") or datetime.max)
 if debug:
  log.info("[HVSCREEN Bucket] Added %d unmatched rows" % len(out))
 return out
# RUNNER
def run(debug=False, notify=False):
 log = system.util.getLogger("MERGER")
 try:
  if debug: log.info("[MERGER] Build HVSV2 + matchback starting...")
  hvsv2_rows = _build_hvsv2(debug=debug)
  availability = _load_hvscreen_availability(debug=debug)
  expanded = []
  allocations = 0
  no_match = 0
  used_orders = set() # to avoid reusing the same PO across allocations
  used_pairs = set() # (canon_alnum(code), PO) to identify matched HVSCREEN lines
  # Allocate Not Serialized demand against HVSCREEN availability
  for row in hvsv2_rows:
   ident = _coerce_str(row.get("Identifier"))
   if ident != "Not Serialized":
    expanded.append(_enforce_types(row))
    continue
   part = _coerce_str(row.get("Part ID"))
   demand = _coerce_int(row.get("Quantity"), 0)
   if not part or demand <= 0:
    expanded.append(_enforce_types(row))
    continue
   taken = _allocate_for_row(part, demand, availability, used_orders, debug=debug)
   if not taken:
    no_match += 1
    expanded.append(_enforce_types(row))
    if debug: log.warn("No PO match: Part=%s Qty=%s" % (part, demand))
    continue
   # Split rows per matched PO
   for j, (po, qty_taken, item) in enumerate(taken):
    r = dict(row)
    r["Identifier"] = po
    r["ECSQTY"] = int(qty_taken)
    r["Quantity"] = int(demand) if j == 0 else None
    expanded.append(_enforce_types(r))
    allocations += 1
    # Track which HVSCREEN line was consumed: key by (code, po)
    used_pairs.add((_canon_alnum(item.get("Code")), po))
  # After allocations, add unmatched HVSCREEN bucket (ONLY sorted by Date)
  unmatched_rows = _build_bucket_hvscreen_unmatched(used_pairs, debug=debug)
  expanded += unmatched_rows
  # Assign HVIndex sequentially across ALL rows before writing out
  for idx, r in enumerate(expanded, start=1):
   r["HVIndex"] = idx
  # Write to HVSV2 dataset tag
  ds_out = _to_dataset(expanded, MASTER_COLS)
  _write_dataset_tag(TAG_PATHS["HVSV2_OUT"], ds_out)
  # Results message (SQL write removed)
  msg = "[Results] HVSV2 -> %s \nAllocated=%d \nNo-match=%d \nRows=%d \nECS-unmatched-added=%d" % (
   TAG_PATHS["HVSV2_OUT"], allocations, no_match, len(expanded), len(unmatched_rows)
  )
  if debug: log.info(msg)
  if notify:
   try: system.gui.messageBox(msg, "MERGER")
   except: log.info(msg)
  return True
 except Exception as ex:
  if notify:
   try: system.gui.errorBox("MERGER failed:\n%s" % ex, "MERGER")
   except: pass
  system.util.getLogger("MERGER").error("MERGER.run() failed: %s" % ex)
  return False
# HELPERS
def trace(part_id, qty, debug=True):
 log = system.util.getLogger("MERGER")
 availability = _load_hvscreen_availability(debug=debug)
 taken = _allocate_for_row(part_id, _coerce_int(qty, 0), availability, set(), debug=debug)
 log.info("TRACE %s x %s -> %s" % (part_id, qty, [(po, q) for (po, q, _it) in taken] if taken else None))
 return taken
def dumpDiagnostics():
 hvsv2_rows = _build_hvsv2(debug=False)
 availability = _load_hvscreen_availability(debug=False)
 dem = {}
 for r in hvsv2_rows:
  if _coerce_str(r.get("Identifier")) == "Not Serialized":
   pid = _coerce_str(r.get("Part ID"))
   dem[pid] = dem.get(pid, 0) + _coerce_int(r.get("Quantity"), 0)
 av = {}
 for k, items in availability.items():
  if k != _canon_alnum(k): continue # tally only pure ALNUM keys
  av[k] = av.get(k, 0) + sum(int(it.get("Qty", 0)) for it in items)
 rows = []
 for pid, dq in dem.items():
  keys = _key_variants(pid)
  atotal = sum(av.get(_canon_alnum(k), 0) for k in keys)
  rows.append({"Part": pid, "DemandTotal": dq, "AvailSeen": atotal, "KeysTried": ", ".join(keys)})
 ds = _to_dataset(rows, ["Part","DemandTotal","AvailSeen","KeysTried"])
 _write_dataset_tag(TAG_PATHS["MERGER_DEBUG"], ds)
FORCED_BP_COIL_ID = "10702BMXU0"
HARD_PREFER_B2_Y24 = True
PREFER_B2_COIL_ID = "10702BMY24"
HARD_PREFER_12H_Y73 = True
PREFER_12H_COIL_ID = "10101CKY72"
def normalize_coil_family(material_str):
 s = (_coerce_str(material_str)).upper()
 if "304L" in s: return "304L SST"
 if "409HP" in s or "400HP" in s or "400 HP" in s or "409 HP" in s: return "400 HP Stainless"
 if s.startswith("10101CK") or "CARB" in s or "1010CK" in s or "MILD" in s or "CARBON" in s: return "Mild Steel"
 return material_str
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
def decode_material_thickness(part_id):
 s = _coerce_str(part_id).upper()
 if len(s) < 2: return None, None
 prefix = s[:2]
 return MATERIAL_THICKNESS.get(prefix, (None, None))
def _build_bucket_hvscreen_unmatched(used_pairs, debug=False):
 """Build a bucket of HVSCREEN rows that were NOT matched back during allocation.
 Sorting: ONLY by Date (ScheduledStart) ascending."""
 log = system.util.getLogger("MERGER")
 ds = _read_hvscreen_dataset(debug=debug)
 headers, rows = _ds_to_list_of_dicts(ds)
 hmap = __map_headers(headers)
 out = []
 pir_ds = _read_dataset_tag("[default]Pirmada Inputs")
 pir_headers, pir_rows = _ds_to_list_of_dicts(pir_ds)
 pir_flat = []
 for prow in pir_rows:
  mat = _coerce_str(prow.get("Material"))
  thk = prow.get("Thickness")
  wid = prow.get("Width")
  coil_id = _coerce_str(prow.get("Part ID"))
  try:
   thk_val = float(thk) if thk is not None else None
  except:
   thk_val = None
  try:
   wid_val = float(wid) if wid is not None else float('inf')
  except:
   wid_val = float('inf')
  if mat and thk_val is not None and coil_id:
   pir_flat.append({"Material": mat, "Thickness": thk_val, "Width": wid_val, "Coil_ID": coil_id})
 for row in rows:
  po = _coerce_str(__hget(row, hmap, " PO","PO"))
  code = _coerce_str(__hget(row, hmap, "code","Code"))
  if code:
   key = (_canon_alnum(code), po)
   if key in used_pairs:
    continue
  r = _empty_master_row()
  r["Identifier"] = po or "Not Serialized"
  r["Quantity"] = _coerce_int(__hget(row, hmap, "Quantity"), 0)
  r["ECSQTY"] = _coerce_int(__hget(row, hmap, "Left"), 0)
  r["Date"] = _excel_serial_to_date(__hget(row, hmap, "ScheduledStart") or __hget(row, hmap, "ReleaseDate") or __hget(row, hmap, "startDate"))
  r["Part ID"] = _coerce_str(__hget(row, hmap, "code","Code")) or None
  add_val = _coerce_str(__hget(row, hmap, "Next Op","NextOp"))
  r["Additional"] = add_val if add_val else "NULL"
  r["Source File"] = "ECS"
  fam, thk = decode_material_thickness(r["Part ID"])
  required_width = _decode_width_from_partid(r["Part ID"])
  raw_val = None
  # Forced coil rules
  if r["Part ID"].startswith("BP"):
   raw_val = FORCED_BP_COIL_ID
  elif HARD_PREFER_B2_Y24 and r["Part ID"].startswith("B2"):
   raw_val = PREFER_B2_COIL_ID
  elif HARD_PREFER_12H_Y73 and r["Part ID"].startswith("12H"):
   raw_val = PREFER_12H_COIL_ID
  else:
   if fam and thk is not None:
    candidates = [c for c in pir_flat if normalize_coil_family(c["Material"]) == fam and abs(c["Thickness"] - thk) <= 0.01]
    if candidates:
     feasible = []
     if required_width is not None:
      feasible = [c for c in candidates if c["Width"] >= required_width]
     if feasible:
      feasible.sort(key=lambda x: x["Width"])
      raw_val = _coerce_str(feasible[0].get("Coil_ID"))
     else:
      # Fallback: largest width among same material/thickness
      candidates.sort(key=lambda x: x["Width"], reverse=True)
      raw_val = _coerce_str(candidates[0].get("Coil_ID"))
  r["Raw Coil"] = raw_val or None
  if debug and not raw_val:
   log.warn("No Raw Coil match for Part ID=%s (Material=%s, Thk=%s, ReqWidth=%s)" % (r['Part ID'], fam, thk, required_width))
  out.append(r)
 out.sort(key=lambda x: x.get("Date") or datetime.max)
 if debug:
  log.info("[HVSCREEN Bucket] Added %d unmatched rows" % len(out))
 return out