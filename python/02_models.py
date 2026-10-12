"""Codificacion categorica y los dos modelos del experimento original.

Aqui se construyen los pipelines; 03_evaluate.py los entrena con train.
Los parametros y nombres se conservan sin ajustes.
"""

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier


def crear_modelos():
    """Cada modelo tiene su propio encoder, ajustado solo con train."""
    modelos = {
        "Regresion Logistica": LogisticRegression(max_iter=1000, solver="lbfgs",
                                                  class_weight="balanced", random_state=42),
        "Arbol de Decision": DecisionTreeClassifier(max_depth=4, min_samples_leaf=100,
                                                     class_weight="balanced", random_state=42),
    }
    return {
        nombre: Pipeline([
            ("categorias", OneHotEncoder(handle_unknown="ignore")),
            ("modelo", modelo),
        ])
        for nombre, modelo in modelos.items()
    }

