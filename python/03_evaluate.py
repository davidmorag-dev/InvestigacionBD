"""Ejecuta y evalua el mismo experimento temporal de Fail.

Instalar: py -3.14 -m pip install -r python/requirements.txt
Ejecutar: py -3.14 python/03_evaluate.py
Si falta la vista: py -3.14 python/03_evaluate.py --preparar

Imprime resultados; no guarda contrasenas, datos ni modelos.
"""

import argparse
import platform
import warnings
from datetime import datetime
from importlib import import_module
from importlib.metadata import version

import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# import_module permite cargar los archivos cuyos nombres empiezan con numeros.
data_prep = import_module("01_data_prep")
models = import_module("02_models")
PREDICTORAS = data_prep.PREDICTORAS


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

    datos = data_prep.cargar_datos(preparar=argumentos.preparar)
    train, test = data_prep.separar_datos(datos)
    data_prep.describir_muestra("TOTAL", datos)
    data_prep.describir_muestra("TRAIN 2019-2024", train)
    data_prep.describir_muestra("TEST 2025", test)
    print("NULL por predictora antes de sustituir por SIN DATO:")
    print(pd.DataFrame({"Train": train[PREDICTORAS].isna().sum(),
                        "Test": test[PREDICTORAS].isna().sum()}).to_string())

    x_train, x_test, y_train, y_test = data_prep.preparar_variables(train, test)
    nuevas = {columna: int((~x_test[columna].isin(x_train[columna].unique())).sum())
              for columna in PREDICTORAS}
    print("Filas de test con categoria ausente de train:", nuevas)

    # La clase mayoritaria se obtiene exclusivamente de train.
    mayoritaria = int(y_train.value_counts().idxmax())
    baseline = [mayoritaria] * len(y_test)
    resultados = [evaluar(f"Baseline: siempre clase {mayoritaria}", y_test, baseline)]

    print("\nParametros fijados antes de evaluar: class_weight=balanced en ambos modelos;")
    print("logistica C=1, max_iter=1000; arbol max_depth=4, min_samples_leaf=100; semilla=42.")
    print("Umbral de clasificacion predeterminado: 0.5. No se ajusta con test.")
    for nombre, pipeline in models.crear_modelos().items():
        # El encoder y el modelo aprenden exclusivamente de train.
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            pipeline.fit(x_train, y_train)
        predichos = pipeline.predict(x_test)
        resultados.append(evaluar(nombre, y_test, predichos))
        if len(set(predichos)) < 2:
            raise ValueError(f"{nombre} predice una sola clase. Detener y revisar.")
        print("Categorias codificadas:", len(pipeline.named_steps["categorias"].get_feature_names_out()))
        modelo = pipeline.named_steps["modelo"]
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

