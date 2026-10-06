SELECT 
    XFR_Serial_Number,
    
    ISNULL(
        MAX(CASE 
            WHEN ProductTypeId = 182 THEN ProductSegmentName 
        END),
        'Ready'
    ) AS Tank_Status,
    
    ISNULL(
        MAX(CASE 
            WHEN ProductTypeId = 159 THEN ProductSegmentName 
        END),
        'Ready'
    ) AS Core_Status

FROM vw_HV_Core_Tank_Status   -- 👈 replace with your actual table/view
WHERE ProductTypeId IN (159, 182)
GROUP BY XFR_Serial_Number;