SELECT 
    w.serial_number,
    w.actual_start,
    w.actual_end,

    -- Total duration
    DATEDIFF(second, w.actual_start, w.actual_end) AS total_sec,

    -- Shift 1 (06:00–14:00)
    CASE 
        WHEN w.actual_end > DATEADD(hour, 6, CAST(w.actual_start AS DATE)) 
         AND w.actual_start < DATEADD(hour, 14, CAST(w.actual_start AS DATE))
        THEN DATEDIFF(second,
            CASE 
                WHEN w.actual_start > DATEADD(hour, 6, CAST(w.actual_start AS DATE)) 
                THEN w.actual_start 
                ELSE DATEADD(hour, 6, CAST(w.actual_start AS DATE)) 
            END,
            CASE 
                WHEN w.actual_end < DATEADD(hour, 14, CAST(w.actual_start AS DATE)) 
                THEN w.actual_end 
                ELSE DATEADD(hour, 14, CAST(w.actual_start AS DATE)) 
            END
        )
        ELSE 0
    END AS shift1_sec

FROM work_orders w