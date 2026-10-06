SELECT
    qc.job_id,
    l.LineCode        AS line_code,
    m.MachineCode     AS machine_code,
    qc.shift_id,
    qc.core_shifted,
    qc.ins_thickness_ok,
    qc.ins_width_ok,
    qc.long_wound_in,
    qc.short_wound_in,
    qc.comments,
    qc.status,
    qc.created_by,
    qc.created_at,
    qc.completed_by,
    qc.completed_at,
    w.wire_seq,
    w.wire_manufacturer,
    w.lot_number,
    w.coating_type,
    w.round_wire_diameter,
    w.width_inches,
    w.thickness_inches,
    w.hv_wire_tension
FROM quality_checks qc
LEFT JOIN hv_wires    w  ON w.job_id    = qc.job_id
LEFT JOIN work_orders wo ON wo.serial_number = qc.job_id
LEFT JOIN tbl_Machine m  ON m.MachineID = wo.machine_id
LEFT JOIN tbl_Line    l  ON l.LineID    = m.LineID
WHERE COALESCE(wo.actual_start, wo.scheduled_start, qc.created_at) >= :startDate
  AND COALESCE(wo.actual_start, wo.scheduled_start, qc.created_at) <  DATEADD(day, 1, CAST(:endDate AS date))
  AND (:lineId    = -1    OR m.LineID      = :lineId)
  AND (:machineId = -1    OR wo.machine_id = :machineId)
  AND (:qcStatus  = 'ALL' OR qc.status     = :qcStatus)
ORDER BY qc.job_id, w.wire_seq;