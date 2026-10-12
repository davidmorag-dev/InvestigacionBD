"""Primera version: Fail con informacion disponible antes del resultado.

Instalar: py -3.14 -m pip install -r python/requirements.txt
Primera ejecucion: py -3.14 python/01_data_science.py --preparar
Siguientes ejecuciones: py -3.14 python/01_data_science.py

La contrasena se solicita en consola y no se guarda. --preparar ejecuta
sql/05science_dataset.sql; crea la vista y muestra sus validaciones.
El script imprime resultados y no guarda datos ni modelos en archivos.
"""

import argparse
import getpass
import platform
import re
import warnings
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

import oracledb
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier


RAIZ = Path(__file__).resolve().parents[1]
PREDICTORAS = ["RISK", "FACILITY_TYPE", "ZIP", "MES"]
COLUMNAS = PREDICTORAS + ["ANO", "FAIL"]


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


def separar_datos(datos):
    train = datos.loc[datos["ANO"].between(2019, 2024)].copy()
    test = datos.loc[datos["ANO"] == 2025].copy()
    if len(train) + len(test) != len(datos) or not train.index.intersection(test.index).empty:
        raise ValueError("La division temporal no cubre las filas correctamente.")
    if set(train["FAIL"]) != {0, 1} or set(test["FAIL"]) != {0, 1}:
        raise ValueError("Train y test deben contener ambas clases.")
    return train, test


def describir_muestra(nombre, datos):
    fail = int(datos["FAIL"].sum())
    print(f"{nombre}: {len(datos):,} registros; Fail={fail:,}; "
          f"No Fail={len(datos) - fail:,}; Fail={100 * fail / len(datos):.4f}%")


def evaluar(nombre, reales, predichos):
    matriz = confusion_matrix(reales, predichos, labels=[0, 1])
    resultado = {
        "Modelo": nombre,
        "Accuracy": accuracy_score(reales, predichos),
        "Precision Fail": precision_score(reales, predichos, pos_label=1, zero_division=0),
        "Recall Fail": recall_score(reales, predichos, pos_label=1, zero_division=0),
        "F1 Fail": f1_score(reales, predichos, pos_label=1, zero_division=0),
    }
    print(f"\n{nombre}")
    print(pd.Series(resultado).drop("Modelo").to_string(float_format=lambda n: f"{n:.6f}"))
    print("Matriz: filas=reales, columnas=predichos; orden No Fail (0), Fail (1)")
    print(pd.DataFrame(matriz, index=["Real No Fail", "Real Fail"],
                       columns=["Pred No Fail", "Pred Fail"]).to_string())
    if int(matriz.sum()) != len(reales):
        raise ValueError("La matriz de confusion no contiene todas las filas de test.")
    return resultado


def mostrar_importancia_arbol(pipeline):
    nombres = pipeline.named_steps["categorias"].get_feature_names_out(PREDICTORAS)
    pesos = pipeline.named_steps["modelo"].feature_importances_
    importancia = pd.Series({
        variable: sum(peso for nombre, peso in zip(nombres, pesos)
                      if nombre.startswith(variable + "_"))
        for variable in PREDICTORAS
    }).sort_values(ascending=False)
    print("\nImportancia del arbol agrupada por variable (aprendida con train):")
    print(importancia.to_string(float_format=lambda n: f"{n:.6f}"))
    print("Es importancia interna del arbol, no causalidad ni una medida del otro modelo.")


def main():
    parser = argparse.ArgumentParser(description="Experimento temporal de Fail en Oracle.")
    parser.add_argument("--preparar", action="store_true", help="Crear la vista y ejecutar el SQL oficial.")
    argumentos = parser.parse_args()
    print("DATA SCIENCE - VERSION 1")
    print("Inicio local:", datetime.now().isoformat(timespec="seconds"))
    print("Python:", platform.python_version())
    for paquete in ["oracledb", "pandas", "scikit-learn", "numpy", "scipy"]:
        print(f"{paquete}: {version(paquete)}")

    clave = getpass.getpass("Contrasena de Oracle GRUPO2: ")
    try:
        conexion = oracledb.connect(user="GRUPO2", password=clave,
                                    host="localhost", port=1521, sid="xe")
    finally:
        del clave
    with conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT USER FROM DUAL")
            print("Usuario Oracle:", cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM FOOD_INSPECTIONS_CLEAN")
            clean_antes = cursor.fetchone()[0]
        if argumentos.preparar:
            ejecutar_preparacion(conexion)
        datos = leer_y_validar(conexion)
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM FOOD_INSPECTIONS_CLEAN")
            clean_despues = cursor.fetchone()[0]
        if clean_antes != clean_despues:
            raise ValueError("Cambio inesperado en el numero de filas de CLEAN.")
        print(f"CLEAN antes/despues: {clean_antes}/{clean_despues}; sin DML sobre CLEAN.")

    train, test = separar_datos(datos)
    describir_muestra("TOTAL", datos)
    describir_muestra("TRAIN 2019-2024", train)
    describir_muestra("TEST 2025", test)
    print("NULL por predictora antes de sustituir por SIN DATO:")
    print(pd.DataFrame({"Train": train[PREDICTORAS].isna().sum(),
                        "Test": test[PREDICTORAS].isna().sum()}).to_string())

    # Regla fija: no aprende del test. El mes se trata como categoria.
    x_train = train[PREDICTORAS].fillna("SIN DATO").astype(str)
    x_test = test[PREDICTORAS].fillna("SIN DATO").astype(str)
    y_train = train["FAIL"].astype(int)
    y_test = test["FAIL"].astype(int)
    nuevas = {columna: int((~x_test[columna].isin(x_train[columna].unique())).sum())
              for columna in PREDICTORAS}
    print("Filas de test con categoria ausente de train:", nuevas)

    # La clase mayoritaria se obtiene exclusivamente de train.
    mayoritaria = int(y_train.value_counts().idxmax())
    baseline = [mayoritaria] * len(y_test)
    resultados = [evaluar(f"Baseline: siempre clase {mayoritaria}", y_test, baseline)]
    modelos = {
        "Regresion Logistica": LogisticRegression(max_iter=1000, solver="lbfgs",
                                                  class_weight="balanced", random_state=42),
        "Arbol de Decision": DecisionTreeClassifier(max_depth=4, min_samples_leaf=100,
                                                     class_weight="balanced", random_state=42),
    }
    print("\nParametros fijados antes de evaluar: class_weight=balanced en ambos modelos;")
    print("logistica C=1, max_iter=1000; arbol max_depth=4, min_samples_leaf=100; semilla=42.")
    print("Umbral de clasificacion predeterminado: 0.5. No se ajusta con test.")
    for nombre, modelo in modelos.items():
        # Cada encoder aprende sus categorias solo al ajustar con x_train.
        pipeline = Pipeline([
            ("categorias", OneHotEncoder(handle_unknown="ignore")),
            ("modelo", modelo),
        ])
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            pipeline.fit(x_train, y_train)
        predichos = pipeline.predict(x_test)
        resultados.append(evaluar(nombre, y_test, predichos))
        if len(set(predichos)) < 2:
            raise ValueError(f"{nombre} predice una sola clase. Detener y revisar.")
        print("Categorias codificadas:", len(pipeline.named_steps["categorias"].get_feature_names_out()))
        if nombre == "Regresion Logistica":
            print("Iteraciones:", modelo.n_iter_.tolist())
        else:
            print("Profundidad:", modelo.get_depth(), "; hojas:", modelo.get_n_leaves())
            mostrar_importancia_arbol(pipeline)

    print("\nCOMPARACION EN TEST 2025 (metricas de 0 a 1)")
    print(pd.DataFrame(resultados).to_string(index=False, float_format=lambda n: f"{n:.6f}"))
    print("LIMITES: establecimientos repetidos; categorias raras; valores previos asumidos;")
    print("2026 excluido; importancia no causal; ponderar Fail puede reducir accuracy.")
    print("EXPERIMENTO TERMINADO SIN ERRORES. No se modificaron Word ni PDF.")


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        print(f"\nERROR: {error}. Experimento detenido; revisar antes de continuar.", flush=True)
        raise SystemExit(1)
