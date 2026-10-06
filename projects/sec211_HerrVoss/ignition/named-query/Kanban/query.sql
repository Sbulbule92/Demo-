
--Set Herr Voss Kanban into #HVK

IF OBJECT_ID('tempdb..#HVK') IS NOT NULL DROP TABLE #HVK;
CREATE TABLE #HVK
(
    [PO Number]     varchar(30)      NULL,
    [Blank]         varchar(100)     NULL,
    [Count]         decimal(18,3)    NULL,
    [Download Date] datetime         NULL
    -- If the proc returns more columns, add 
    -- exact order
);
 
INSERT INTO #HVK
EXEC EcsSupport.[dbo].[spRPT_SetHervossKanban];
 

-- Kanban Steel Where Are You 

IF OBJECT_ID('tempdb..#KSWAY') IS NOT NULL DROP TABLE #KSWAY;
CREATE TABLE #KSWAY
(
    [PO Number]          varchar(30)      NULL,
    [Current_Operation]  varchar(200)     NULL,
    [Part/Description]   varchar(200)     NULL,  -- name contains '/', bracket
    [Released Date]      datetime         NULL,
    [Workcenter]         varchar(100)     NULL,
    [ProductSegmentId]   varchar(50)      NULL
 
);
 
INSERT INTO #KSWAY
EXEC EcsSupport.[dbo].[spRPT_KanbanSteelWhereAreYou];
 
------------------------------------------------------------
 
------------------------------------------------------------
SELECT
    h.[PO Number],
    h.[Blank],
    h.[Count],
    h.[Download Date],
    ks.[Current_Operation] AS [Current_Operation]
    -- , ks.[Part/Description]
    -- , ks.[Released Date]
    -- , ks.[Workcenter]
    -- , ks.[ProductSegmentId]
FROM
(
    SELECT
        LTRIM(RTRIM([PO Number])) AS [PO Number],
        [Blank],
        [Count],
        [Download Date]
    FROM #HVK
) AS h
OUTER APPLY
(
    SELECT TOP (1)
        k.[Current_Operation],
        k.[Part/Description],
        k.[Released Date],
        k.[Workcenter],
        k.[ProductSegmentId]
    FROM #KSWAY AS k
    WHERE LTRIM(RTRIM(k.[PO Number])) = h.[PO Number]
    ORDER BY
        k.[Released Date] DESC,
        k.[Current_Operation] ASC
) AS ks
ORDER BY
    h.[Download Date] DESC,
    h.[PO Number];
 