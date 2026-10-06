SELECT
     w.serial_number
    ,w.lspec_id
    ,w.machine_id
    ,w.op_status
    ,CASE w.op_status
        WHEN  4  THEN 'Running'
        WHEN  8  THEN 'Paused'
        WHEN 16  THEN 'Completed'
        WHEN 32  THEN 'Cancelled'
        WHEN 45  THEN 'Cancel Requested'
        ELSE          'Unknown'
     END                        AS status_label
    ,w.actual_start
    ,w.actual_end
    ,bounds.effective_start
    ,bounds.effective_end
    ,evt.event_end_time         AS pause_cancel_event_time
    ,c.winding_minutes
    ,c.hv_winding_minutes
    ,IIF(
        c.winding_minutes <= 0,
        NULL,
        IIF(
            ROUND(CAST(c.hv_winding_minutes AS FLOAT) / c.winding_minutes, 4) > 1,
            1.0,
            ROUND(CAST(c.hv_winding_minutes AS FLOAT) / c.winding_minutes, 4)
        )
     ) AS actual_ratio,
     w.StartUser,
     w.EndUser
FROM work_orders AS w
JOIN lspec_metadata AS l ON l.lspec_id = w.lspec_id
-- ══════════════════════════════════════════════════════════════
-- ✅ FIX: each :param used ONCE here — JDBC sees exactly 3 x ?
-- All APPLY blocks and WHERE reference p.* columns instead
-- ══════════════════════════════════════════════════════════════
CROSS JOIN (
    SELECT
        CAST(:StartTime AS DATETIME) AS p_start,
        CAST(:EndTime   AS DATETIME) AS p_end
--        CAST(:MachineID AS INT)      AS p_machine
) AS p

-- ── Latest Pause / Cancel event within this shift ─────────────
OUTER APPLY (
    SELECT TOP 1
         e.update_time   AS event_end_time
        ,e.event_type_id AS event_type
    FROM wo_event_history AS e
    WHERE
        e.serial_number  =  w.serial_number
        AND e.event_type_id IN (8, 32, 45)
        AND e.update_time  >  p.p_start          -- ← p.* not :param
        AND e.update_time  <= p.p_end
    ORDER BY e.update_time DESC
) AS evt

-- ── Shift-clamped effective start & end ───────────────────────
CROSS APPLY (
    SELECT
        IIF(w.actual_start > p.p_start, w.actual_start, p.p_start)
            AS effective_start,
        CASE
            WHEN w.op_status IN (8, 32, 45)
             AND evt.event_end_time IS NOT NULL
                THEN IIF(evt.event_end_time < p.p_end,
                         evt.event_end_time, p.p_end)
            WHEN w.op_status = 4
                THEN p.p_end
            ELSE
                IIF(ISNULL(w.actual_end, p.p_end) < p.p_end,
                    ISNULL(w.actual_end, p.p_end), p.p_end)
        END AS effective_end
) AS bounds

-- ── Duration in minutes + standard hv_winding conversion ─────
CROSS APPLY (
    SELECT
        IIF(bounds.effective_end > bounds.effective_start,
            DATEDIFF(MINUTE, bounds.effective_start, bounds.effective_end),
            0
        ) AS winding_minutes,
        (
            FLOOR(l.hv_winding_time) * 60
            + ROUND((l.hv_winding_time - FLOOR(l.hv_winding_time)) * 100, 0)
        ) AS hv_winding_minutes
) AS c

WHERE
--    w.machine_id  =  p.p_machine             -- ← p.* not :param
     w.op_status  IN (4, 8, 16, 32, 45, 18)
    AND w.actual_start <  p.p_end
    AND (
        w.op_status = 4
        OR (w.op_status = 16  AND w.actual_end           > p.p_start)
        OR (w.op_status IN (8, 32, 45)
            AND (w.actual_start >= p.p_start OR evt.event_end_time IS NOT NULL))
    )
    AND c.winding_minutes > 0 AND (w.StartUser =  :Operator OR w.EndUser =  :Operator)