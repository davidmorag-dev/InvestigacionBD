"""Datos del experimento: Oracle, validacion y division temporal.

Fuente: FOOD_INSPECTIONS_SCIENCE. La contrasena se pide en consola.
ANO separa train/test; FAIL es el target. Ninguno es una predictora.
"""

import getpass
import re
from pathlib import Path

import oracledb
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PREDICTORAS = ["RISK", "FACILITY_TYPE", "ZIP", "MES"]
COLUMNAS = PREDICTORAS + ["ANO", "FAIL"]


def conectar_oracle():
    """Conecta con GRUPO2 sin guardar la contrasena."""
    clave = getpass.getpass("Contrasena de Oracle GRUPO2: ")
    try:
        return oracledb.connect(user="GRUPO2", password=clave,
                               host="localhost", port=1521, sid="xe")
    finally:
        del clave


def ejecutar_preparacion(conexion):
    """Ejecuta las sentencias simples del SQL oficial (sin bloques PL/SQL)."""
    texto = (RAIZ / "sql" / "05science_dataset.sql").read_text(encoding="utf-8")
    texto = re.sub(r"--[^\n]*", "", texto)
    with conexion.cursor() as cursor:
        for numero, sentencia in enumerate(texto.split(";"), start=1):
            if not sentencia.strip():
                continue
            print(f"\nSQL {numero}")
            cursor.execute(sentencia.strip())
            if cursor.description:
                nombres = [columna[0] for columna in cursor.description]
                print(pd.DataFrame(cursor.fetchall(), columns=nombres).to_string(index=False))
            else:
                print("Vista FOOD_INSPECTIONS_SCIENCE creada.")


def leer_y_validar(conexion):
    """Contrasta conteos de la fuente, la vista y las filas leidas por Python."""
    with conexion.cursor() as cursor:
        cursor.execute("""
            SELECT EXTRACT(YEAR FROM INSPECTION_DATE) AS ANO,
                   COUNT(*) AS TOTAL,
                   SUM(CASE WHEN RESULTS = 'Fail' THEN 1 ELSE 0 END) AS FAIL
            FROM FOOD_INSPECTIONS_CLEAN
            WHERE RESULTS IN ('Fail', 'Pass', 'Pass w/ Conditions')
              AND (INSPECTION_TYPE IS NULL OR INSPECTION_TYPE <> 'NON-INSPECTION')
              AND INSPECTION_DATE >= DATE '2019-01-01'
              AND INSPECTION_DATE < DATE '2026-01-01'
            GROUP BY EXTRACT(YEAR FROM INSPECTION_DATE)
            ORDER BY ANO
        """)
        control_oracle = cursor.fetchall()
        cursor.execute("""
            SELECT ANO, COUNT(*), SUM(FAIL)
            FROM FOOD_INSPECTIONS_SCIENCE GROUP BY ANO ORDER BY ANO
        """)
        if cursor.fetchall() != control_oracle:
            raise ValueError("Los conteos de la vista no coinciden con CLEAN filtrada.")
        cursor.arraysize = 5000
        cursor.execute("""
            SELECT RISK, FACILITY_TYPE, ZIP, MES, ANO, FAIL
            FROM FOOD_INSPECTIONS_SCIENCE
            ORDER BY ANO, MES, RISK, FACILITY_TYPE, ZIP
        """)
        datos = pd.DataFrame(cursor.fetchall(), columns=COLUMNAS)

    if datos.empty or datos[["MES", "ANO", "FAIL"]].isna().any().any():
        raise ValueError("Conjunto vacio o mes, ano o target con NULL.")
    if not datos["ANO"].between(2019, 2025).all():
        raise ValueError("Hay anos fuera del periodo aprobado.")
    if not datos["MES"].between(1, 12).all() or not datos["FAIL"].isin([0, 1]).all():
        raise ValueError("Mes o target invalido.")
    control_python = datos.groupby("ANO")["FAIL"].agg(["count", "sum"])
    if list(control_python.itertuples(name=None)) != control_oracle:
        raise ValueError("Las filas leidas por Python no coinciden con Oracle.")
    print("\nValidacion: fuente filtrada, vista y Python coinciden por ano y clase.")
    return datos


def cargar_datos(preparar=False):
    """Lee la vista y comprueba que CLEAN conserve sus filas."""
    with conectar_oracle() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT USER FROM DUAL")
            print("Usuario Oracle:", cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM FOOD_INSPECTIONS_CLEAN")
            clean_antes = cursor.fetchone()[0]
        if preparar:
            ejecutar_preparacion(conexion)
        datos = leer_y_validar(conexion)
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM FOOD_INSPECTIONS_CLEAN")
            clean_despues = cursor.fetchone()[0]
        if clean_antes != clean_despues:
            raise ValueError("Cambio inesperado en el numero de filas de CLEAN.")
        print(f"CLEAN antes/despues: {clean_antes}/{clean_despues}; sin DML sobre CLEAN.")
    return datos


def separar_datos(datos):
    train = datos.loc[datos["ANO"].between(2019, 2024)].copy()
    test = datos.loc[datos["ANO"] == 2025].copy()
    if len(train) + len(test) != len(datos) or not train.index.intersection(test.index).empty:
        raise ValueError("La division temporal no cubre las filas correctamente.")
    if set(train["FAIL"]) != {0, 1} or set(test["FAIL"]) != {0, 1}:
        raise ValueError("Train y test deben contener ambas clases.")
    return train, test


def preparar_variables(train, test):
    """Regla fija para NULL; el mes tambien se trata como categoria."""
    x_train = train[PREDICTORAS].fillna("SIN DATO").astype(str)
    x_test = test[PREDICTORAS].fillna("SIN DATO").astype(str)
    y_train = train["FAIL"].astype(int)
    y_test = test["FAIL"].astype(int)
    return x_train, x_test, y_train, y_test


def describir_muestra(nombre, datos):
    fail = int(datos["FAIL"].sum())
    print(f"{nombre}: {len(datos):,} registros; Fail={fail:,}; "
          f"No Fail={len(datos) - fail:,}; Fail={100 * fail / len(datos):.4f}%")

