# oasis_phoenix

Structure du projet:

- `models/`: dossier vide pour les fichiers `.pkl` generes depuis le notebook.
- `data/`: dossier vide pour `with_causes.csv` genere depuis le notebook.
- `static/carte.html`: page HTML statique servie par Flask.
- `app.py`: point d'entree de l'application Flask.
- `requirements.txt`: dependances Python.

## Demarrage rapide

```bash
pip install -r requirements.txt
python app.py
```

Puis ouvrez http://127.0.0.1:5000 dans votre navigateur.
