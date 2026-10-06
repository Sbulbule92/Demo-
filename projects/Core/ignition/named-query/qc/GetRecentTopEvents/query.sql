SELECT TOP (5) [id]
      ,[serial_number]
      ,(Select name from wo_event_types where id = event_type_id) As Event
      ,[update_time]
      ,[userName]
      ,[wip]
      ,[actual_num_turns]
      ,[machine_id]
      ,[remarks]
  FROM [Ignition].[dbo].[wo_event_history] where machine_id=:machine_id order by id desc;