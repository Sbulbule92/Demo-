SELECT *
FROM vw_WindingTime_Tuboly A
CROSS APPLY (
    SELECT TOP 1 B.KVA,B.hv1_bil,B.PRODCOMP
    FROM vw_HV_Winding_Part_Detail B
    WHERE B.lspec = A.LSPEC
) B 