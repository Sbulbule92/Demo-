SELECT
    wo.serial_number,
    wo.op_status,
    CAST(lm.hv_winding_time * 60.0 AS decimal(10, 2))                       AS ideal_time,
    CASE WHEN DATEDIFF(MINUTE, wo.actual_start, COALESCE(wo.actual_end, :fallbackEnd)) < 0
         THEN 0
         ELSE DATEDIFF(MINUTE, wo.actual_start, COALESCE(wo.actual_end, :fallbackEnd))
    END                                                                    AS actual_time
FROM dbo.work_orders wo
LEFT JOIN dbo.lspec_metadata lm
       ON lm.lspec_id = wo.lspec_id
      AND lm.is_active = 1
WHERE wo.machine_id = :machineId
  AND wo.op_status IN (16, 4, 8, 32)
  AND wo.actual_start >= :startTime
  AND wo.actual_start <  :endTime
ORDER BY wo.actual_start;
