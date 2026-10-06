DECLARE @Date1 DATETIME = DATEADD(DAY, +1, GETDATE());
DECLARE @Date2 DATETIME = GETDATE();
DECLARE @Date3 DATETIME = DATEADD(DAY, -1, GETDATE());
DECLARE @Date4 DATETIME = DATEADD(DAY, -2, GETDATE());
DECLARE @Date5 DATETIME = DATEADD(DAY, -3, GETDATE());
DECLARE @Date6 DATETIME = DATEADD(DAY, -4, GETDATE());
DECLARE @Date7 DATETIME = DATEADD(DAY, -5, GETDATE());
DECLARE @Date8 DATETIME = DATEADD(DAY, -6, GETDATE());
DECLARE @Date9 DATETIME = DATEADD(DAY, -7, GETDATE());

CREATE TABLE #Results (
    Column1 VARCHAR(100),
    Column2 NUMERIC(18, 2)
);

INSERT INTO #Results
EXEC [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[spRpt_Make_base_Report_stn_test] @Date1;

IF NOT EXISTS (SELECT 1 FROM #Results)
BEGIN
    TRUNCATE TABLE #Results;
    INSERT INTO #Results
    EXEC [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[spRpt_Make_base_Report_stn_test] @Date2;
END

IF NOT EXISTS (SELECT 1 FROM #Results)
BEGIN
    TRUNCATE TABLE #Results;
    INSERT INTO #Results
    EXEC [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[spRpt_Make_base_Report_stn_test] @Date3;
END

IF NOT EXISTS (SELECT 1 FROM #Results)
BEGIN
    TRUNCATE TABLE #Results;
    INSERT INTO #Results
    EXEC [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[spRpt_Make_base_Report_stn_test] @Date4;
END

IF NOT EXISTS (SELECT 1 FROM #Results)
BEGIN
    TRUNCATE TABLE #Results;
    INSERT INTO #Results
    EXEC [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[spRpt_Make_base_Report_stn_test] @Date5;
END

IF NOT EXISTS (SELECT 1 FROM #Results)
BEGIN
    TRUNCATE TABLE #Results;
    INSERT INTO #Results
    EXEC [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[spRpt_Make_base_Report_stn_test] @Date6;
END

IF NOT EXISTS (SELECT 1 FROM #Results)
BEGIN
    TRUNCATE TABLE #Results;
    INSERT INTO #Results
    EXEC [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[spRpt_Make_base_Report_stn_test] @Date7;
END

IF NOT EXISTS (SELECT 1 FROM #Results)
BEGIN
    TRUNCATE TABLE #Results;
    INSERT INTO #Results
    EXEC [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[spRpt_Make_base_Report_stn_test] @Date8;
END

IF NOT EXISTS (SELECT 1 FROM #Results)
BEGIN
    TRUNCATE TABLE #Results;
    INSERT INTO #Results
    EXEC [usjef-s-ecsdb\EcsData].[EcsSupport].[dbo].[spRpt_Make_base_Report_stn_test] @Date9;
END

SELECT * FROM #Results;
DROP TABLE #Results
