SELECT 
    Coil_ID, LSPEC, Duration, Percent_Complete,
    Status, Actual_Start, Actual_Finish,
    Sched_Start, Sched_Finish, Sched_Setup_Time,
    Sched_Mach_Time, Workstation_ID, Operator_ID,
    Operator_ID2, Actual_Start2, Actual_Finish2,
    Operator_Percent_Complete, MatlOrd, Duplex,
    BIL, Style, MI_Dlvrd
FROM [LWCTPROD].[dbo].[COILWINDING_FEEDBACK]
WHERE Coil_ID = :searchValue1
   OR Coil_ID = :searchValue2
   OR Coil_ID = :searchValue3
   OR Coil_ID = :searchValue4
   OR Coil_ID = :searchValue5
   OR Coil_ID = :searchValue6
ORDER By Coil_ID ASC