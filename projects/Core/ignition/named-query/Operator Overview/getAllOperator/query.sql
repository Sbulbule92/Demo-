SELECT
     base.operator
    ,base.machineID
    ,COUNT(*)                                        AS session_count
    ,MIN(base.effective_login)                       AS first_login
    ,MAX(base.effective_logout)                      AS last_logout
    ,SUM(base.logged_seconds)                        AS total_seconds
    ,ROUND(SUM(base.logged_seconds) / 60.0,   2)    AS total_minutes
    ,ROUND(SUM(base.logged_seconds) / 3600.0, 4)    AS total_hours

FROM (
    SELECT
         o.operator
        ,o.machineID
        ,o.login_time
        ,o.logout_time
        ,bounds.effective_login
        ,bounds.effective_logout
        ,bounds.logged_seconds

    FROM Trace_Operator AS o

    CROSS JOIN (
        SELECT
            CAST(:StartTime AS DATETIME) AS p_start,
            CAST(:EndTime   AS DATETIME) AS p_end
    ) AS p

    CROSS APPLY (
        SELECT
            IIF(o.login_time > p.p_start, o.login_time, p.p_start)
                AS effective_login,
            IIF(ISNULL(o.logout_time, p.p_end) < p.p_end,
                ISNULL(o.logout_time, p.p_end),
                p.p_end)
                AS effective_logout
    ) AS bounds_raw

    CROSS APPLY (
        SELECT
            bounds_raw.effective_login   AS effective_login,
            bounds_raw.effective_logout  AS effective_logout,
            IIF(
                bounds_raw.effective_logout > bounds_raw.effective_login,
                DATEDIFF(SECOND,
                         bounds_raw.effective_login,
                         bounds_raw.effective_logout),
                0
            ) AS logged_seconds
    ) AS bounds

    WHERE
        -- ✅ Filter overlap with shift window
        o.login_time                       < p.p_end
        AND ISNULL(o.logout_time, p.p_end) > p.p_start

        -- ✅ Exclude junk epoch rows (1970 bad data)
        AND o.login_time > '2000-01-01'

        -- ✅ Exclude rows with no operator name
        AND o.operator IS NOT NULL
        AND LTRIM(RTRIM(o.operator)) <> ''

) AS base

GROUP BY
     base.operator
    ,base.machineID

ORDER BY total_seconds DESC