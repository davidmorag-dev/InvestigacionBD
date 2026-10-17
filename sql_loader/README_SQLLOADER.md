# Demo de SQL*Loader: CSV → tabla de prueba

SQL*Loader lee un CSV siguiendo las instrucciones de un archivo de control y carga sus datos en Oracle. Aquí usamos las primeras **500 filas** del CSV original, sin transformar valores ni modificar RAW, CLEAN o SCIENCE.

## Ejecución desde la carpeta principal del proyecto

En PowerShell:

```powershell
$env:ORACLE_HOME = 'C:\app\Administrador\product\21c\dbhomeXE'
$env:ORACLE_SID = 'XE'
sqlplus GRUPO2@localhost:1521/xe
```

Dentro de SQL*Plus, vaciar la demo eliminando **solo la tabla de prueba** y recrearla:

```sql
DROP TABLE FOOD_INSPECTIONS_RAW_LOADER_TEST PURGE;
@sql/00_sql_loader_test.sql
EXIT
```

Después, en PowerShell:

```powershell
sqlldr userid=GRUPO2 control=sql_loader/food_inspections.ctl log=evidencias/sql_loader/demo.log
sqlplus GRUPO2@localhost:1521/xe @evidencias/sql_loader/validacion_demo.sql
```

Cada cliente pide la contraseña; no se guarda. `ORACLE_SID=XE` identifica la instancia local. Si SQL*Loader no está en PATH, comprobar `Get-Command sqlldr` y ejecutar `& "$env:ORACLE_HOME\bin\sqlldr.exe"` con los mismos argumentos. El control exige una tabla vacía; ante un error, detenerse y revisar `demo.log`.

## Qué explicar y mostrar

- **Muestra:** `sql_loader/food_inspections_demo_500.csv`, encabezado y 500 filas con 17 columnas. Es una demo de carga, no una muestra estadística.
- **Control:** `food_inspections.ctl` indica el archivo, la tabla y las columnas; omite el encabezado, lee UTF-8, comas y comillas, interpreta fechas `MM/DD/YYYY` y conserva espacios. Los campos vacíos quedan NULL.
- **Textos largos:** `CHAR(32767)` es el límite de lectura de VIOLATIONS; la tabla usa CLOB para almacenarlo completo.
- **Validación:** primero mostrar conteo, IDs y longitudes; después la comparación con RAW. `DECODE` devuelve 0 si dos valores son iguales, incluidos dos NULL, y 1 si difieren. `DBMS_LOB.COMPARE` comprueba el CLOB completo y devuelve 0 si coincide.

## Resultado verificado en Oracle

**500 filas, 500 IDs únicos, cero rechazos y cero diferencias de contenido frente a RAW.** VIOLATIONS: máximo **6.411 caracteres**, **10 textos mayores de 4.000** y **169 NULL**. RAW y CLEAN conservaron 316.961 filas cada una; SCIENCE conservó 103.596.

Evidencia vigente: `evidencias/sql_loader/demo.log`, `demo_preparacion.txt`, `demo_resultados.txt` y `demo_resumen.txt`. Los archivos de la carga completa fallida y sus errores se conservan como evidencia histórica; no forman parte de la demo.