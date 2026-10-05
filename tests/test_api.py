import os
import tempfile

from fastapi.testclient import TestClient

fd, db_path = tempfile.mkstemp(prefix="ecare_test_", suffix=".db")
os.close(fd)
os.environ["ECARE_DB_PATH"] = db_path

from app.main import app  # noqa: E402

client = TestClient(app)


def test_create_patient_and_fetch_it():
    payload = {
        "full_name": "Alice Martin",
        "chronic_conditions": ["diabetes", "hypertension"],
    }
    create_response = client.post("/patients", json=payload)
    assert create_response.status_code == 200

    patient = create_response.json()
    assert patient["full_name"] == payload["full_name"]
    assert patient["chronic_conditions"] == payload["chronic_conditions"]

    get_response = client.get(f"/patients/{patient['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == patient["id"]


def test_measurements_and_alerts_for_diabetes_and_hypertension():
    create_patient = client.post(
        "/patients",
        json={"full_name": "Bob Diallo", "chronic_conditions": ["diabetes", "hypertension"]},
    )
    patient_id = create_patient.json()["id"]

    glucose_response = client.post(
        f"/patients/{patient_id}/measurements",
        json={"type": "glucose", "glucose_mg_dl": 210},
    )
    assert glucose_response.status_code == 200

    pressure_response = client.post(
        f"/patients/{patient_id}/measurements",
        json={"type": "blood_pressure", "systolic": 150, "diastolic": 95},
    )
    assert pressure_response.status_code == 200

    history = client.get(f"/patients/{patient_id}/measurements")
    assert history.status_code == 200
    assert len(history.json()) >= 2

    alerts = client.get(f"/patients/{patient_id}/alerts")
    assert alerts.status_code == 200
    alert_types = {alert["type"] for alert in alerts.json()}
    assert "diabetes" in alert_types
    assert "hypertension" in alert_types
