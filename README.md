# eCare_plus_backend
Partie web (Backend) de eCare plus.

Backend minimal pour le suivi de maladies chroniques (diabète et hypertension).

## Lancer le projet

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Endpoints principaux

- `POST /patients` : créer un patient
- `GET /patients/{patient_id}` : récupérer un patient
- `POST /patients/{patient_id}/measurements` : enregistrer glycémie ou tension artérielle
- `GET /patients/{patient_id}/measurements` : historique des mesures
- `GET /patients/{patient_id}/alerts` : alertes de diabète/hypertension

## Tests

```bash
pytest tests/test_api.py -q
```
