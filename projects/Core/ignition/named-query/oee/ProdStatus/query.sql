SELECT
    COUNT(*)                                                      AS started,
    SUM(CASE WHEN op_status IN (16, 18) THEN 1 ELSE 0 END)        AS completed,
    SUM(CASE WHEN op_status IN (4, 8)   THEN 1 ELSE 0 END)        AS in_progress
FROM dbo.work_orders
WHERE machine_id = :machineId
  AND actual_start >= :startTime
  AND actual_start <  :endTime;