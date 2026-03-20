SELECT
    FORMAT(DATEADD(HOUR, DATEPART(HOUR, time), 0), 'HH:00') AS [Hour],
    AVG(actualCT)  AS IdealCycleTime,
    AVG(idealCT) AS ActualCycleTime
FROM Completed_Jobs1
WHERE shift = :Shift And CONVERT(DATE, time) = CONVERT(DATE, :Day) 
GROUP BY DATEPART(HOUR, time)
ORDER BY [Hour];