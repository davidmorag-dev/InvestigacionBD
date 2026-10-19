# Reproducir el caso práctico

Ejecutar desde la raíz del proyecto en Windows. La carga oficial es el CSV completo mediante SQL*Loader.

## Requisitos

- Oracle XE activo, usuario GRUPO2 y permisos para crear tablas y vistas.
- Conexión local: localhost, puerto 1521, SID xe; espacio disponible para RAW y CLEAN.
- SQL*Plus y SQL*Loader en PATH: comprobar con `Get-Command sqlplus, sqlldr`.
- Python 3.14 y las dependencias de `python/requirements.txt`.
- Power BI Desktop con la conexión a Oracle configurada.

Los comandos piden la contraseña en consola. No escribirla en archivos ni en el comando.

## 1. Crear RAW

Este paso corresponde a una base preparada desde cero, donde RAW todavía no existe. Si RAW ya contiene los datos verificados, conservarla y comenzar por el perfilado. No cargar otra vez sobre esa tabla.

```powershell
$env:ORACLE_SID = 'XE'
sqlplus GRUPO2@localhost:1521/xe
```

Dentro de SQL*Plus:

```sql
WHENEVER SQLERROR EXIT SQL.SQLCODE
@sql/01create_raw.sql
EXIT
```

RAW tiene 17 columnas y VIOLATIONS es CLOB para conservar los textos largos.

## 2. Cargar el CSV completo

RAW debe estar vacía. Desde PowerShell, en la raíz:

```powershell
sqlldr userid=GRUPO2 control=sql/loader/food_inspections.ctl log=sql/loader/carga_raw.log
```

El control lee `data/Food_Inspections_20261010.csv`, omite el encabezado y carga directamente FOOD_INSPECTIONS_RAW. Respeta comillas, campos CSV multilínea, fechas MM/DD/YYYY y VIOLATIONS hasta 32.767 caracteres por campo.

Esperado: **316.961 cargadas, 0 rechazadas y 0 descartadas**. Si hay errores o diferencias, detenerse antes de continuar. El log incluido conserva la ejecución real de la carga completa; su ruta de control refleja la ubicación anterior al cambio de carpeta. Una nueva ejecución reemplaza ese log, por lo que conviene guardar una copia si se desea conservar el historial.

## 3. Ejecutar el perfilado

Abrir SQL*Plus nuevamente y mantener la sesión para los pasos 3–7:

```sql
WHENEVER SQLERROR EXIT SQL.SQLCODE
@sql/02profiling.sql
```

Las 12 consultas solo diagnostican. Esperado: 316.961 filas e IDs distintos, 61.038 Fail, 3 direcciones con solo espacios, 527 FACILITY_TYPE y 110 INSPECTION_TYPE distintos. VIOLATIONS: 89.410 NULL, máximo 12.706 caracteres y 4.469 textos mayores de 4.000.

## 4. Crear o reconstruir CLEAN

Si CLEAN ya existe y se desea reconstruirla, ejecutar primero únicamente:

```sql
DROP TABLE FOOD_INSPECTIONS_CLEAN PURGE;
```

Después, o directamente si CLEAN no existe:

```sql
@sql/03cleaning.sql
```

El script conserva RAW, crea CLEAN y ejecuta sus validaciones. Aplica TRIM a ADDRESS, UPPER(TRIM()) a FACILITY_TYPE e INSPECTION_TYPE y convierte coordenadas a NUMBER. No elimina filas ni cambia otras variables.

## 5. Revisar RAW frente a CLEAN

Revisar las consultas 2–8 que acaba de ejecutar `03cleaning.sql`; no volver a ejecutar su CREATE TABLE. Para repetir solo las validaciones, seleccionar esos bloques en SQL Developer.

Esperado: ambas tablas con 316.961 filas e IDs distintos; categorías 527→473 y 110→98; direcciones con solo espacios 3→0, convertidas a NULL. Coordenadas: 1.061 NULL por columna y ninguna fuera de rango. VIOLATIONS conserva los mismos NULL, máximo y textos mayores de 4.000. Ante una diferencia, detenerse.

## 6. Ejecutar Analytics

```sql
@sql/04analytics.sql
```

Las siete consultas calculan y validan los resultados: **316.961 inspecciones, 61.038 Fail, 19,26 % Fail**. Las asociaciones por riesgo, establecimiento, tipo de inspección y año no prueban causalidad.

## 7. Crear y verificar Science

```sql
@sql/05science_dataset.sql
EXIT
```

La vista FOOD_INSPECTIONS_SCIENCE entrega 103.596 registros. Train 2019–2024: 87.539; test 2025: 16.057, incluidos 3.391 Fail y 12.666 No Fail. El script permite volver a crear la vista después de reconstruir CLEAN.

## 8. Ejecutar Python

```powershell
py -3.14 -m pip install -r python/requirements.txt
py -3.14 python/03_evaluate.py
```

`03_evaluate.py` usa `01_data_prep.py` para leer y validar Oracle y `02_models.py` para crear los modelos. No hace falta ejecutar los tres por separado. El encoder y los modelos aprenden solo de train.

Resultados de test, con Fail como clase positiva:

| Método | Accuracy | Precision Fail | Recall Fail | F1 Fail |
|---|---:|---:|---:|---:|
| Regresión Logística | 0,535530 | 0,228831 | 0,506045 | 0,315152 |
| Árbol de Decisión | 0,771751 | 0,256228 | 0,042465 | 0,072856 |
| Siempre No Fail | 0,788815 | 0,000000 | 0,000000 | 0,000000 |
| Siempre Fail | 0,211185 | 0,211185 | 1,000000 | 0,348725 |

Siempre Fail consigue mayor recall y F1, pero genera 12.666 falsas alarmas; la logística genera 5.783 y detecta 1.716 Fail. Se prefiere la logística frente al árbol por recall y F1, considerando sus limitaciones. La capacidad predictiva es modesta y el experimento es académico, sin justificar uso operativo.

## 9. Abrir y refrescar Power BI

Abrir `powerbi/Data Analytics final.pbix`, configurar las credenciales de GRUPO2 si se solicitan y actualizar la conexión a CLEAN. Revisar las dos páginas, los filtros y los indicadores generales: 316.961, 61.038 y 19,26 %. SQL conserva la función de cálculo y validación.

## Evidencia disponible

`sql/loader/carga_raw.log` conserva la carga completa. `evidencias/` contiene salidas verificadas de perfilado, normalización, limpieza, Analytics y Science. Las capturas finales del documento se tomarán manualmente; los archivos de texto son respaldo técnico.
