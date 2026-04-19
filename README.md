# oasis_phoenix

Structure du projet:

- `models/`: contient les modeles `.pkl` utilises a l'execution.
- `data/`: contient les datasets utilises par l'application.
- `templates/carte.html`: dashboard web principal.
- `app.py`: point d'entree de l'application Flask.
- `requirements.txt`: dependances Python.

## Modeles requis

Les fichiers suivants doivent exister dans `models/` pour que l'IA fonctionne apres un clone:

- `models/isolation_forest.pkl`
- `models/random_forest.pkl`
- `models/ridge_regression.pkl`
- `models/scaler.pkl`
- `models/scaler_ridge.pkl`

Ces fichiers sont charges par `services/model_loader.py`.

## Demarrage rapide

```bash
pip install -r requirements.txt
python app.py
```

Puis ouvrez http://127.0.0.1:5000 dans votre navigateur.
