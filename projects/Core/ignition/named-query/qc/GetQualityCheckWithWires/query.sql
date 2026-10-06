SELECT
    qc.job_id, qc.line_id, qc.machine_id, qc.shift_id,
    qc.core_shifted, qc.ins_thickness_ok, qc.ins_width_ok,
    qc.long_wound_in, qc.short_wound_in, qc.comments,
    qc.status, qc.created_by, qc.created_at,
    qc.completed_by, qc.completed_at,
    w.wire_seq, w.wire_manufacturer, w.lot_number, w.coating_type,
    w.round_wire_diameter, w.width_inches, w.thickness_inches,
    w.hv_wire_tension
FROM quality_checks qc
LEFT JOIN hv_wires w ON w.job_id = qc.job_id
WHERE qc.job_id = :jobId
ORDER BY w.wire_seq;