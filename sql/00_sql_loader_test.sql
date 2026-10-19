-- Ejecuta estos pasos desde la raíz del proyecto; cada cliente pide la contraseña.
-- SQL*Plus: sqlplus GRUPO2@localhost:1521/xe
-- Si la tabla de prueba ya existe: DROP TABLE FOOD_INSPECTIONS_RAW_LOADER_TEST PURGE;
-- SQL*Plus: @sql/00_sql_loader_test.sql y luego EXIT
-- PowerShell: $env:ORACLE_SID = 'XE'
-- PowerShell: sqlldr userid=GRUPO2 control=sql/food_inspections.ctl log=evidencias/sql_loader/demo_rutas.log
-- Validación: sqlplus GRUPO2@localhost:1521/xe @sql/validacion_demo.sql

-- 1. Crea solamente la tabla de prueba con las mismas 17 columnas de RAW
CREATE TABLE FOOD_INSPECTIONS_RAW_LOADER_TEST (
    INSPECTION_ID    NUMBER(38),
    DBA_NAME         VARCHAR2(255),
    AKA_NAME         VARCHAR2(255),
    LICENSE_NUMBER   NUMBER(38),
    FACILITY_TYPE    VARCHAR2(255),
    RISK             VARCHAR2(100),
    ADDRESS          VARCHAR2(255),
    CITY             VARCHAR2(100),
    STATE            VARCHAR2(20),
    ZIP              VARCHAR2(20),
    INSPECTION_DATE  DATE,
    INSPECTION_TYPE  VARCHAR2(255),
    RESULTS          VARCHAR2(100),
    VIOLATIONS       CLOB,
    LATITUDE         VARCHAR2(50),
    LONGITUDE        VARCHAR2(50),
    LOCATION         VARCHAR2(255)
);
