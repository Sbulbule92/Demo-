WITH ClampedDowntime AS (
    -- Step 1: Clamp each record to the shift window
    SELECT 
         LogID
        ,IIF(StartTime > :StartTime, StartTime, :StartTime) AS EffectiveStart
        ,IIF(EndTime < :EndTime, EndTime, :EndTime) AS EffectiveEnd
    FROM tbl_DowntimeLog
    WHERE 
        DurationMinutes > 0
        AND DurationMinutes IS NOT NULL
        AND (:MachineID IS NULL OR MachineID = :MachineID)
        AND StartTime < :EndTime
        AND EndTime > :StartTime
),
RankedDowntime AS (
    -- Step 2: Find previous max end time
    SELECT 
        *,
        MAX(EffectiveEnd) OVER (
            ORDER BY EffectiveStart 
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS PreviousMaxEnd
    FROM ClampedDowntime
),
IslandStarts AS (
    -- Step 3: Identify where new non-overlapping periods start
    SELECT 
        *,
        CASE 
            WHEN PreviousMaxEnd IS NULL OR EffectiveStart > PreviousMaxEnd 
            THEN 1 
            ELSE 0 
        END AS IsNewIsland
    FROM RankedDowntime
),
IslandGroups AS (
    -- Step 4: Group overlapping periods together
    SELECT 
        *,
        SUM(IsNewIsland) OVER (ORDER BY EffectiveStart) AS IslandID
    FROM IslandStarts
),
MergedDowntime AS (
    -- Step 5: Merge overlapping periods into continuous blocks
    SELECT 
         IslandID
        ,MIN(EffectiveStart) AS PeriodStart
        ,MAX(EffectiveEnd) AS PeriodEnd
        ,DATEDIFF(MINUTE, MIN(EffectiveStart), MAX(EffectiveEnd)) AS PeriodMinutes
    FROM IslandGroups
    GROUP BY IslandID
)
-- Step 6: Calculate total and format as HH:MM:SS
SELECT 
    CASE 
        WHEN SUM(PeriodMinutes) IS NULL 
             OR SUM(PeriodMinutes) <= 0
        THEN '00:00:00'
        ELSE
            RIGHT('0' + CAST(SUM(IIF(PeriodMinutes<1170, PeriodMinutes, 1170)) / 60 AS VARCHAR), 2) + ':' +
            RIGHT('0' + CAST(SUM(IIF(PeriodMinutes<1170, PeriodMinutes, 1170)) % 60 AS VARCHAR), 2) + ':00'
    END AS dt
FROM MergedDowntime