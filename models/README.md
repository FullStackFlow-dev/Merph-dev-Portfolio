# 🤖 Modèles ML

> Modèles entraînés et sauvegardés

---

## my_simple_model.keras

| Propriété | Valeur |
|---|---|
| **Framework** | Keras 3.10.0 |
| **Type** | Sequential |
| **Date de sauvegarde** | 2026-01-29 |
| **Tâche** | Classification binaire |
| **Fichier** | `my_simple_model.keras` |

---

### Architecture

```
┌─────────────────────────────────┐
│  InputLayer                     │
│  shape: (None, 10)              │
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Dense(32)                      │
│  activation: relu               │
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Dense(16)                      │
│  activation: relu               │
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Dense(1)                       │
│  activation: sigmoid            │
│  → Sortie : 0 ou 1             │
└─────────────────────────────────┘
```

### Détails

- **Entrée** : 10 features (float32)
- **Couche cachée 1** : 32 neurones, activation ReLU
- **Couche cachée 2** : 16 neurones, activation ReLU
- **Sortie** : 1 neurone, activation Sigmoid (classification binaire)
- **Initialiseur des poids** : Glorot Uniform
- **Initialisation des biais** : Zeros

### Comment charger le modèle

```python
import keras

model = keras.models.load_model("models/my_simple_model.keras")
model.summary()
```

---

### Fichiers internes du .keras (ZIP)

| Fichier | Contenu |
|---|---|
| `metadata.json` | Version Keras, date de sauvegarde |
| `config.json` | Architecture complète du modèle |
| `model.weights.h5` | Poids entraînés |
