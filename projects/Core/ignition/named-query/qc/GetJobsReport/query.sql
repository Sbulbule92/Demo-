SELECT
    wo.serial_number                                  AS job_id,
    wo.program_name,
    l.LineCode                                        AS line_code,
    m.MachineCode                                     AS machine_code,
    COALESCE(wo.actual_start, wo.scheduled_start)     AS job_start,
    wo.actual_end                                     AS job_end,
    COALESCE(wo.StartUser, qc.created_by)             AS operator,
    CASE
        WHEN wo.actual_end   IS NOT NULL THEN 'Completed'
        WHEN wo.actual_start IS NOT NULL THEN 'In Progress'
        ELSE 'Not Started'
    END                                               AS job_status,
    COALESCE(qc.status, 'NOT_STARTED')                AS qc_status
FROM work_orders wo
LEFT JOIN quality_checks qc ON qc.job_id    = wo.serial_number
LEFT JOIN tbl_Machine    m  ON m.MachineID  = wo.machine_id
LEFT JOIN tbl_Line       l  ON l.LineID     = m.LineID
WHERE COALESCE(wo.actual_start, wo.scheduled_start) >= :startDate
  AND COALESCE(wo.actual_start, wo.scheduled_start) <  DATEADD(day, 1, CAST(:endDate AS date))
  AND (:lineId    = -1    OR m.LineID      = :lineId)
  AND (:machineId = -1    OR wo.machine_id = :machineId)
  AND (:qcStatus  = 'ALL' OR COALESCE(qc.status, 'NOT_STARTED') = :qcStatus)
ORDER BY COALESCE(wo.actual_start, wo.scheduled_start) DESC;