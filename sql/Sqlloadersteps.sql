-- Vacía RAW para probar una carga completa desde el dataset original
TRUNCATE TABLE FOOD_INSPECTIONS_RAW;



-- Confirma que RAW quedó vacía antes de ejecutar SQL*Loader
SELECT COUNT(*) AS TOTAL_FILAS
FROM FOOD_INSPECTIONS_RAW;


--Ejecutamos este comando en powershell

--$env:ORACLE_SID = 'XE'
--sqlldr userid=GRUPO2 control=sql/loader/food_inspections.ctl log=sql/loader/carga_raw.log

--------------------------------------------------------------------------------------------------------

-- Verifica la cantidad total de filas cargadas en RAW
SELECT COUNT(*) AS TOTAL_FILAS
FROM FOOD_INSPECTIONS_RAW;

-- Verifica que los identificadores sigan siendo únicos
SELECT COUNT(DISTINCT INSPECTION_ID) AS IDS_UNICOS
FROM FOOD_INSPECTIONS_RAW;

