SELECT * FROM wo_event_history
WHERE userName =  :operator 
	AND (update_time BETWEEN  :startTime AND  :endTime )
