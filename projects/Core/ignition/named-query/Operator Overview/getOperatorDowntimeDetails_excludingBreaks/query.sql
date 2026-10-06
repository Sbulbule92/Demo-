-- =====================================================
-- Operator Daily Summary Report
-- Parameters: @UserName, @StartDate, @EndDate
-- =====================================================

DECLARE @UserName   NVARCHAR(100) =  :UserName 
DECLARE @StartDate  DATETIME      =  :StartTime 
DECLARE @EndDate    DATETIME      =  :EndTime 

;WITH

-- ── 1. All downtime logs for this user in the date range ──────────────────────
UserDowntime AS (
    SELECT
        dl.LogID,
        dl.MachineID,
        dl.ShiftID,
        dl.ReasonID,
        dl.DurationMinutes,
        dl.StartTime,
        dl.EndTime,
        DATEDIFF(SECOND, dl.StartTime, dl.EndTime) AS DurationSeconds
    FROM tbl_DowntimeLog dl
    WHERE
        dl.UserName  = @UserName
        AND dl.StartTime >= @StartDate
        AND dl.StartTime <= @EndDate
        AND dl.ReasonID NOT IN (8, 9, 10, 11, 12, 13)
),

-- ── 2. Downtime aggregates ────────────────────────────────────────────────────
DowntimeAgg AS (
    SELECT
        MIN(ShiftID)                                                    AS ShiftID,
        MIN(MachineID)                                                  AS MachineID,

        MIN(StartTime)                                                  AS LoginTime,
        MAX(EndTime)                                                    AS LogoutTime,

        -- Total logged downtime (all entries)
        SUM(DurationSeconds)                                            AS TotalDowntimeSec,

        -- Breaks → ReasonID 8 or 9 only
        SUM(CASE WHEN ReasonID IN (8, 9, 10, 11, 12, 13) THEN DurationSeconds ELSE 0 END) AS BreakSec,

        -- Unplanned → everything that is NOT a break (ReasonID not 8 or 9)
        SUM(CASE WHEN ReasonID NOT IN (8, 9, 10, 11, 12, 13) THEN DurationSeconds ELSE 0 END) AS UnplannedSec,

        COUNT(*)                                                        AS DowntimeEntries
    FROM UserDowntime
),

-- ── 3. Work-order aggregates for this user ────────────────────────────────────
WorkOrderAgg AS (
    SELECT
        COUNT(CASE WHEN wo.StartUser = @UserName THEN 1 END)            AS CoilsStarted,

        -- Adjust serial_status = 3 to your "Completed" status code
        COUNT(CASE WHEN wo.EndUser = @UserName
                        AND wo.serial_status = 3 THEN 1 END)           AS CoilsCompleted,

        COUNT(CASE WHEN wo.StartUser = @UserName
                        AND wo.serial_status NOT IN (3)
                        AND wo.actual_end IS NULL THEN 1 END)          AS CoilsInProgress,

        MIN(wo.actual_start)                                            AS WO_LoginTime,
        MAX(wo.actual_end)                                              AS WO_LogoutTime
    FROM work_orders wo
    WHERE
        (wo.StartUser = @UserName OR wo.EndUser = @UserName)
        AND wo.actual_start >= @StartDate
        AND wo.actual_start <= @EndDate
),

-- ── 4. Combine and compute derived metrics ────────────────────────────────────
Combined AS (
    SELECT
        da.ShiftID,
        da.MachineID,

        COALESCE(da.LoginTime,  wa.WO_LoginTime)  AS LoginTime,
        COALESCE(da.LogoutTime, wa.WO_LogoutTime) AS LogoutTime,

        da.TotalDowntimeSec,
        da.BreakSec,
        da.UnplannedSec,
        da.DowntimeEntries,

        wa.CoilsStarted,
        wa.CoilsCompleted,
        wa.CoilsInProgress,

        DATEDIFF(SECOND,
            COALESCE(da.LoginTime,  wa.WO_LoginTime),
            COALESCE(da.LogoutTime, wa.WO_LogoutTime)
        )                                          AS SessionSec,

        DATEDIFF(SECOND,
            COALESCE(da.LoginTime,  wa.WO_LoginTime),
            COALESCE(da.LogoutTime, wa.WO_LogoutTime)
        ) - da.TotalDowntimeSec                   AS OperatingSec

    FROM DowntimeAgg da
    CROSS JOIN WorkOrderAgg wa
)

-- ── 5. Final SELECT ───────────────────────────────────────────────────────────
SELECT
    c.ShiftID                                                           AS [SHIFT WORKED],
    m.MachineCode                                                       AS [MACHINE],

    CONVERT(VARCHAR(8), DATEADD(SECOND, c.TotalDowntimeSec, 0), 108)   AS [LOGGED DOWNTIME],
    CONVERT(VARCHAR(8), DATEADD(SECOND, c.BreakSec,         0), 108)   AS [BREAKS],
    CONVERT(VARCHAR(8), DATEADD(SECOND, c.UnplannedSec,     0), 108)   AS [UNPLANNED DOWNTIME],

    -- Availability = Operating Time / Session Time × 100
    IIF(
    CAST(
        CAST(c.OperatingSec AS FLOAT)
        / NULLIF(c.SessionSec, 0) * 100.0
    AS INT)>0,
    CAST(
        CAST(c.OperatingSec AS FLOAT)
        / NULLIF(c.SessionSec, 0) * 100.0
    AS INT),
    0
    )                                                             AS [Availability],

    -- Performance = Coils Completed / Coils Started × 100
    CAST(
        CAST(c.CoilsCompleted AS FLOAT)
        / NULLIF(c.CoilsStarted, 0) * 100.0
    AS INT)                                                             AS [Performance],

    c.CoilsStarted                                                      AS [Coils Started],
    c.CoilsCompleted                                                    AS [Coils Completed],
    c.CoilsInProgress                                                   AS [Coils Inprogress],
    c.DowntimeEntries                                                   AS [No of Downtime Entries],

    CONVERT(VARCHAR(8), c.LoginTime,  108)                              AS [Login Time],
    CONVERT(VARCHAR(8), c.LogoutTime, 108)                              AS [Logout Time],

    CONVERT(VARCHAR(8), DATEADD(SECOND, c.OperatingSec, 0), 108)       AS [Operating Time]

FROM Combined c
LEFT JOIN tbl_Machine m ON m.MachineID = c.MachineID