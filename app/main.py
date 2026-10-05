from contextlib import closing

from fastapi import FastAPI, HTTPException

from app.db import get_connection, init_db
from app.schemas import (
    MeasurementCreate,
    MeasurementResponse,
    PatientCreate,
    PatientResponse,
)

app = FastAPI(title="eCare Plus Backend")
init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/patients", response_model=PatientResponse)
def create_patient(payload: PatientCreate) -> PatientResponse:
    with closing(get_connection()) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO patients(full_name, chronic_conditions) VALUES (?, ?)",
            (payload.full_name, ",".join(payload.chronic_conditions)),
        )
        patient_id = cursor.lastrowid
        connection.commit()
    return PatientResponse(id=patient_id, **payload.model_dump())


@app.get("/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: int) -> PatientResponse:
    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT id, full_name, chronic_conditions FROM patients WHERE id = ?",
            (patient_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")

    return PatientResponse(
        id=row["id"],
        full_name=row["full_name"],
        chronic_conditions=row["chronic_conditions"].split(","),
    )


@app.post(
    "/patients/{patient_id}/measurements",
    response_model=MeasurementResponse,
)
def add_measurement(patient_id: int, payload: MeasurementCreate) -> MeasurementResponse:
    with closing(get_connection()) as connection:
        patient = connection.execute(
            "SELECT 1 FROM patients WHERE id = ?",
            (patient_id,),
        ).fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO measurements(patient_id, type, glucose_mg_dl, systolic, diastolic)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                payload.type,
                payload.glucose_mg_dl,
                payload.systolic,
                payload.diastolic,
            ),
        )
        measurement_id = cursor.lastrowid
        connection.commit()
        row = connection.execute(
            """
            SELECT id, patient_id, type, glucose_mg_dl, systolic, diastolic, taken_at
            FROM measurements
            WHERE id = ?
            """,
            (measurement_id,),
        ).fetchone()

    return MeasurementResponse(**dict(row))


@app.get(
    "/patients/{patient_id}/measurements",
    response_model=list[MeasurementResponse],
)
def list_measurements(patient_id: int) -> list[MeasurementResponse]:
    with closing(get_connection()) as connection:
        patient = connection.execute(
            "SELECT 1 FROM patients WHERE id = ?",
            (patient_id,),
        ).fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        rows = connection.execute(
            """
            SELECT id, patient_id, type, glucose_mg_dl, systolic, diastolic, taken_at
            FROM measurements
            WHERE patient_id = ?
            ORDER BY taken_at DESC, id DESC
            """,
            (patient_id,),
        ).fetchall()

    return [MeasurementResponse(**dict(row)) for row in rows]


@app.get("/patients/{patient_id}/alerts")
def get_alerts(patient_id: int) -> list[dict[str, str | int]]:
    with closing(get_connection()) as connection:
        patient = connection.execute(
            "SELECT 1 FROM patients WHERE id = ?",
            (patient_id,),
        ).fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        rows = connection.execute(
            """
            SELECT id, type, glucose_mg_dl, systolic, diastolic
            FROM measurements
            WHERE patient_id = ?
            ORDER BY id DESC
            """,
            (patient_id,),
        ).fetchall()

    alerts: list[dict[str, str | int]] = []
    for row in rows:
        if row["type"] == "glucose" and row["glucose_mg_dl"] is not None and row["glucose_mg_dl"] >= 180:
            alerts.append(
                {
                    "measurement_id": row["id"],
                    "type": "diabetes",
                    "severity": "high",
                    "message": "High glucose level detected",
                }
            )
        if row["type"] == "blood_pressure" and (
            (row["systolic"] is not None and row["systolic"] >= 140)
            or (row["diastolic"] is not None and row["diastolic"] >= 90)
        ):
            alerts.append(
                {
                    "measurement_id": row["id"],
                    "type": "hypertension",
                    "severity": "high",
                    "message": "High blood pressure detected",
                }
            )

    return alerts
