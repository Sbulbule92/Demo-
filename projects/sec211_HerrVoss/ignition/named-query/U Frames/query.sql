SELECT TOP (1000)
    c.[SerialNumber],
    c.[UFRAME],
    ts.schedule_run_date,
    f.[PRODPRNT],
    f.partname,
    f2.PRODCOMP,
    pt.PARTNAME,
    f2.PRODQNTY
FROM ecssupport.dbo.TankSchedule ts
JOIN [MachineReady].[dbo].[ABB_CoreReportData] c ON ts.jCSerial = c.SerialNumber
CROSS APPLY [MachineReady].[Engineering].fn_Flat_Eng_BOM(c.uframe) f
JOIN [MachineReady].[Engineering].[Prod] f2 ON f.PRODCOMP = f2.PRODPRNT AND f2.PRODPODT = 99999
JOIN [MachineReady].[Engineering].[part] pt ON pt.PARTCTRL = f2.prodcomp
WHERE f.partname = 'CRCLUFRMOD'
  AND pt.PARTNAME = 'BLNK'
  AND ts.schedule_run_date = CAST(DATEADD(DAY, -1, GETDATE()) AS DATE)

UNION ALL

SELECT TOP (1000)
    c.[SerialNumber],
    c.[UFRAME],
    ts.schedule_run_date,
    f.[PRODPRNT],
    f.partname,
    f2.PRODCOMP,
    pt.PARTNAME,
    f2.PRODQNTY
FROM ecssupport.dbo.TankSchedule ts
JOIN [MachineReady].[dbo].[ABB_CoreReportData] c ON ts.jCSerial = c.SerialNumber
CROSS APPLY [MachineReady].[Engineering].fn_Flat_Eng_BOM(c.uframe) f
JOIN [MachineReady].[Engineering].[Prod] f2 ON f.PRODCOMP = f2.PRODPRNT AND f2.PRODPODT = 99999
JOIN [MachineReady].[Engineering].[part] pt ON pt.PARTCTRL = f2.prodcomp
WHERE f.partname = 'CRCLUFRMOD'
  AND pt.PARTNAME = 'BLNK'
  AND ts.schedule_run_date = CAST(DATEADD(DAY, -5, GETDATE()) AS DATE)
  AND NOT EXISTS (
        SELECT 1
        FROM ecssupport.dbo.TankSchedule ts2
        WHERE ts2.schedule_run_date = CAST(DATEADD(DAY, -1, GETDATE()) AS DATE)
    )

UNION ALL

SELECT TOP (1000)
    c.[SerialNumber],
    c.[UFRAME],
    ts.schedule_run_date,
    f.[PRODPRNT],
    f.partname,
    f2.PRODCOMP,
    pt.PARTNAME,
    f2.PRODQNTY
FROM ecssupport.dbo.TankSchedule ts
JOIN [MachineReady].[dbo].[ABB_CoreReportData] c ON ts.jCSerial = c.SerialNumber
CROSS APPLY [MachineReady].[Engineering].fn_Flat_Eng_BOM(c.uframe) f
JOIN [MachineReady].[Engineering].[Prod] f2 ON f.PRODCOMP = f2.PRODPRNT AND f2.PRODPODT = 99999
JOIN [MachineReady].[Engineering].[part] pt ON pt.PARTCTRL = f2.prodcomp
WHERE f.partname = 'CRCLUFRMOD'
  AND pt.PARTNAME = 'BLNK'
  AND ts.schedule_run_date = CAST(DATEADD(DAY, -4, GETDATE()) AS DATE)
  AND NOT EXISTS (
        SELECT 1
        FROM ecssupport.dbo.TankSchedule ts2
        WHERE ts2.schedule_run_date IN (
            CAST(DATEADD(DAY, -1, GETDATE()) AS DATE),
            CAST(DATEADD(DAY, -3, GETDATE()) AS DATE)
        )
    );