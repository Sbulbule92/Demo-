UPDATE TankPrograms
SET priority=  :priority 
OUTPUT inserted.id
WHERE id=  :id 
