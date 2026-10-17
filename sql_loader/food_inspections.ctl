-- 1. Omite el encabezado y detiene la carga ante errores
OPTIONS (SKIP=1, ERRORS=0, EMPTY_LOBS_ARE_NULL=TRUE)
-- 2. Carga solo la muestra y conserva sus espacios originales
LOAD DATA
CHARACTERSET AL32UTF8
INFILE 'sql_loader/food_inspections_demo_500.csv'
BADFILE 'evidencias/sql_loader/demo.bad'
DISCARDFILE 'evidencias/sql_loader/demo.dsc'
PRESERVE BLANKS
INTO TABLE FOOD_INSPECTIONS_RAW_LOADER_TEST
FIELDS CSV WITH EMBEDDED
TRAILING NULLCOLS
-- 3. Lee las 17 columnas en el mismo orden del CSV
(
    INSPECTION_ID    INTEGER EXTERNAL(38),
    DBA_NAME         CHAR(255),
    AKA_NAME         CHAR(255),
    LICENSE_NUMBER   INTEGER EXTERNAL(38),
    FACILITY_TYPE    CHAR(255),
    RISK             CHAR(100),
    ADDRESS          CHAR(255),
    CITY             CHAR(100),
    STATE            CHAR(20),
    ZIP              CHAR(20),
    INSPECTION_DATE  DATE "MM/DD/YYYY",
    INSPECTION_TYPE  CHAR(255),
    RESULTS          CHAR(100),
    -- Permite leer textos largos que se almacenan completos como CLOB
    VIOLATIONS       CHAR(32767),
    LATITUDE         CHAR(50),
    LONGITUDE        CHAR(50),
    LOCATION         CHAR(255)
)
