-- 1. Omite el encabezado y detiene la carga ante cualquier error
OPTIONS (SKIP=1, ERRORS=0, EMPTY_LOBS_ARE_NULL=TRUE)

-- 2. Carga el dataset original completo conservando sus espacios
LOAD DATA
CHARACTERSET AL32UTF8
INFILE 'data/Food_Inspections_20261010.csv'

BADFILE 'evidencias/sql_loader/carga_raw.bad'
DISCARDFILE 'evidencias/sql_loader/carga_raw.dsc'

PRESERVE BLANKS

-- 3. Carga directamente en la tabla RAW oficial
INTO TABLE FOOD_INSPECTIONS_RAW

FIELDS CSV WITH EMBEDDED
TRAILING NULLCOLS

-- 4. Lee las 17 columnas en el mismo orden del CSV original
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

    -- Permite almacenar textos largos completos en la columna CLOB
    VIOLATIONS       CHAR(32767),

    LATITUDE         CHAR(50),
    LONGITUDE        CHAR(50),
    LOCATION         CHAR(255)
)