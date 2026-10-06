SELECT
    wo.po_number,
    wo.serial_number,
    wo.lspec_id,
    wo.op_status,
    wo.actual_start,
    wo.actual_end,
    ls.hv_winding_time,
    DATEDIFF(SECOND, wo.actual_start, e.EffEnd) / 60.0 AS ActualMinutes,
    CASE WHEN x.ClipEnd > x.ClipStart
         THEN DATEDIFF(SECOND, x.ClipStart, x.ClipEnd) / 60.0
         ELSE 0 END                                    AS ClippedMinutes
FROM dbo.work_orders wo
LEFT JOIN dbo.lspec_metadata ls ON ls.lspec_id = wo.lspec_id
CROSS APPLY (SELECT
        CASE WHEN wo.actual_end IS NOT NULL THEN wo.actual_end
             ELSE GETDATE() END AS EffEnd) e
CROSS APPLY (SELECT
        CASE WHEN wo.actual_start > :startDate THEN wo.actual_start ELSE :startDate END AS ClipStart,
        CASE WHEN e.EffEnd        < :endDate   THEN e.EffEnd        ELSE :endDate   END AS ClipEnd) x
WHERE wo.machine_id = :machineId
  AND wo.actual_start IS NOT NULL
  AND wo.actual_start < :endDate
  AND e.EffEnd        > :startDate
ORDER BY wo.actual_start;
