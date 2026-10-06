USE [Engineering];

SELECT 
    ts.jCSerial AS [Serial No],
    ts.schedule_run_date AS [Schedule Date],
    ncsp.BlankID AS [Blank ID],
    prod.PRODCOMP AS [Coil ID]
FROM [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[TankSchedule] AS ts (nolock)
LEFT JOIN [Engineering].[dbo].[NC_Serial_Parts] AS ncsp 
    ON ts.jCSerial = ncsp.Serial_No
JOIN [Engineering].[dbo].[prod] as prod
    ON ncsp.BlankID = prod.PRODPRNT
WHERE 
    ncsp.Machine = 22152
    AND ncsp.Part_Type IN ('Front_Panel', 'Back_Panel')
    AND prod.PRODPODT = 99999
    AND ts.jCSerial IN (
        SELECT prod.XFR_Serial_Number
        FROM [usjef-s-ecsdb\EcsData].[ECS].[dbo].[Product] AS prod
        INNER JOIN [usjef-s-ecsdb\EcsData].[ECS].[TVQ].[SegmentResponse_Product] AS SRP (nolock)
            ON SRP.ProductId = prod.ProductId
        INNER JOIN [usjef-s-ecsdb\EcsData].[ECS].[dbo].[SegmentResponse] AS SR (nolock)
            ON SR.SegmentResponseId = SRP.SegmentResponseId
        INNER JOIN [usjef-s-ecsdb\EcsData].[ECS].[dbo].[ProductSegment] AS PS (nolock)
            ON PS.ProductSegmentId = SR.ProductSegmentId
        WHERE 
            SR.actualEndTime IS NULL
            AND prod.ProductionStatus = '2'
            AND PS.Name = 'TPTM_3PHLaserPunch'
    )
ORDER BY 
    [Schedule Date] ASC, 
    [Serial No] ASC;