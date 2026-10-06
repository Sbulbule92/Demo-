
Select Distinct Top 5000
    po.ExternalId as 'Production Order',  
    po.priority,
    vps.MaterialCode 'Part Name',
    pb.Blank 'Material',
    po.Quantity,
    vps.ProductionStatus,
    po.DownloadDate,
    po.ReleaseDate,
    po.ScheduledStart,
    pop.startDate,
    ps.Description as 'Equipment' -- Join Tables and Views from ECS and MachineReady dbs
From ecs.dbo.ProductionOrder po
    Join ecs.TVQ.SegmentResponse_ProductionOrder qp (NOLOCK) on qp.ProductionOrderId = po.ProductionOrderId
    Join ecs.dbo.SegmentResponse sr (NOLOCK) on sr.SegmentResponseId = qp.SegmentResponseId
    Join ecs.dbo.ProductSegment ps (NOLOCK) on ps.ProductSegmentId = sr.ProductSegmentId
    JOIN ecs.dbo.ProductType pt (NOLOCK) on pt.ProductTypeId = ps.ProductTypeId
    join ecs.dbo.ProductionPerformance pop (NOLOCK) on pop.ProductionOrderId = po.ProductionOrderId
    join ecs.dbo.ProductSegmentEquipmentDefinition ed (NOLOCK) on ed.ProductSegmentId = ps.ProductSegmentId
    join ecs.TVQ.SegmentResponse_Product srp (NOLOCK) on srp.SegmentResponseId = qp.SegmentResponseId
    join ecs.dbo.vw_ProductStatus vps (NOLOCK) on vps.OrderNumber = po.ExternalId
    join MachineReady.Engineering.ProductBlank pb (NOLOCK) on pb.Product = vps.MaterialCode
    join ecs.dbo.Product pro (NOLOCK) on pro.ProductionOrderId = po.ProductionOrderId
    left join ecs.dbo.EquipmentDefinition eqd (NOLOCK) on eqd.EquipmentDefinitionId = ed.EquipmentDefinitionId --join EcsSupport.dbo.Feedback_Machine_log fm (NOLOCK) on fm.segment_Id = ps.ProductSegmentId
    -- Change how far back to pull data
where 1=1
    and ps.ExternalId = '21148;2110'
    --and po.EndProductionTime > DATEADD(DAY,-45,GETDATE())
    --and vps.ProductionStatus = 'Waiting'
	--or vps.ProductionStatus = 'In Progress'
	AND vps.ProductionStatus IN ('Waiting')
    --and po.externalid = '1002682502'
order by pop.startDate desc