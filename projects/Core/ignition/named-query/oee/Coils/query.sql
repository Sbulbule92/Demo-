SELECT
    wo.serial_number,
    wo.lspec_id,
    wo.op_status,
    wo.actual_start,
    wo.actual_end,
    v.actual_min,
    lm.hv_winding_time                                 AS hv_winding_time_hours,
    v.ideal_ct_min,
    CASE
        WHEN wo.op_status = 16 THEN 100.0                       -- Completed = 100%
        WHEN v.ideal_ct_min IS NULL OR v.ideal_ct_min = 0 THEN 0.0
        ELSE CAST(
            CASE
                WHEN v.elapsed_min < 0 THEN 0.0
                WHEN (v.elapsed_min / v.ideal_ct_min) * 100.0 > 100.0 THEN 100.0
                ELSE (v.elapsed_min / v.ideal_ct_min) * 100.0
            END AS decimal(10, 2))
    END AS completion_percent
FROM dbo.work_orders wo
LEFT JOIN dbo.lspec_metadata lm
       ON lm.lspec_id = wo.lspec_id
      AND lm.is_active = 1
CROSS APPLY (VALUES (
        DATEDIFF(MINUTE, wo.actual_start, wo.actual_end),                            -- actual_min (NULL if running)
        DATEDIFF(MINUTE, wo.actual_start, COALESCE(wo.actual_end, :fallbackEnd)),    -- elapsed_min (capped at selection end)
        CAST(lm.hv_winding_time * 60.0 AS decimal(10, 2))                            -- ideal_ct_min
    )) v(actual_min, elapsed_min, ideal_ct_min)
WHERE wo.machine_id = :machineId
  AND wo.actual_start >= :startTime
  AND wo.actual_start <  :endTime
ORDER BY wo.actual_start;
