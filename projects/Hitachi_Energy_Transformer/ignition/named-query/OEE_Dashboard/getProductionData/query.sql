-- Declare variables if testing in SSMS
DECLARE @shiftParam CHAR(1) = NULL;   -- Can be 'A', 'B', 'C', or NULL/blank
DECLARE @machineParam INT = NULL;      -- Optional
DECLARE @dayParam DATE = '2026-01-16';

SELECT *
FROM Completed_Jobs1
WHERE 
    -- Handle shift filter: blank/NULL = all shifts
    ((@shiftParam IS NULL OR @shiftParam = '') AND shift IN ('A','B','C'))
    OR (shift = @shiftParam AND @shiftParam IS NOT NULL AND @shiftParam <> '')
    
    -- Machine filter
    AND (@machineParam IS NULL OR MachineID = @machineParam)

    -- actualCT not null
    AND actualCT IS NOT NULL

    -- Date adjustment for Shift C
    AND CONVERT(DATE, time) = 
        CASE 
            WHEN @shiftParam = 'C' THEN DATEADD(DAY, 1, CONVERT(DATE, @dayParam))
            ELSE CONVERT(DATE, @dayParam)
        END;

