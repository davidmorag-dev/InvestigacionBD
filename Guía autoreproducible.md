# Reproducir el caso práctico

Ejecutar desde la raíz del proyecto.

## Requisitos

- Oracle XE con el usuario GRUPO2.
- SQL*Plus y SQL*Loader.
- Python 3.14.
- Power BI Desktop.

## Pasos

### 1. Crear RAW

Desde PowerShell:

sqlplus GRUPO2@localhost:1521/xe

Dentro de SQL*Plus:

@sql/01create_raw.sql

### 2. Cargar el CSV

sqlldr userid=GRUPO2 control=sql/loader/food_inspections.ctl log=sql/loader/carga_raw.log

Resultado esperado: 316961 filas cargadas, 0 rechazadas y 0 descartadas.

### 3. Perfilado

@sql/02profiling.sql

### 4. Crear CLEAN

@sql/03cleaning.sql

Resultados principales: RAW y CLEAN con 316961 filas, FACILITY_TYPE 527 → 473 e INSPECTION_TYPE 110 → 98.

### 5. Analytics

@sql/04analytics.sql

Resultados principales: 316961 inspecciones, 61038 Fail y 19,26 % Fail.

### 6. Preparar Science

@sql/05science_dataset.sql

### 7. Ejecutar Python

py -3.14 -m pip install -r python/requirements.txt
py -3.14 python/03_evaluate.py

Se comparan la Regresión Logística, Árbol de Decisión, Baseline Siempre No Fail y Baseline Siempre Fail.

### 8. Power BI

Abrir:

powerbi/Data Analytics final.pbix

Actualizar la conexión a Oracle si solicita las credenciales.

## Flujo general

CSV → RAW → Profiling → CLEAN → Analytics → Science → Power BI