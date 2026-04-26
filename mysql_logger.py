import os
import json
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


class MySQLLogger:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "sentinel_db")
        self.connection = None
        self._initialize_db()

    def _initialize_db(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            if self.connection.is_connected():
                print("[MySQLLogger] Connected successfully.")
        except Error as e:
            print(f"[MySQLLogger] Error connecting to MySQL: {e}")
            self.connection = None

    def log_report(self, document_id: str, data: dict):
        """Insert or update a report in the emergency_reports table."""
        if not self.connection or not self.connection.is_connected():
            return

        try:
            cursor = self.connection.cursor()
            history = json.dumps(data.get("conversation_history", []))
            dispatch_needed = 1 if data.get("dispatch_needed") else 0

            query = """
                INSERT INTO emergency_reports (
                    id, situation_id, report_date, report_time,
                    emergency_category, emergency_sub_type, incident_description,
                    reporter_type, caller_name, caller_contact_number, caller_gender,
                    state, district_city, locality_area, pin_code,
                    latitude, longitude,
                    severity_level, threat_to_human_life,
                    number_of_casualties, number_of_injuries,
                    weapon_hazard_involved,
                    dispatch_needed, dispatch_reason,
                    conversation_history
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                ) ON DUPLICATE KEY UPDATE
                    situation_id=VALUES(situation_id),
                    report_date=VALUES(report_date),
                    report_time=VALUES(report_time),
                    emergency_category=VALUES(emergency_category),
                    emergency_sub_type=VALUES(emergency_sub_type),
                    incident_description=VALUES(incident_description),
                    reporter_type=VALUES(reporter_type),
                    caller_name=VALUES(caller_name),
                    caller_contact_number=VALUES(caller_contact_number),
                    caller_gender=VALUES(caller_gender),
                    state=VALUES(state),
                    district_city=VALUES(district_city),
                    locality_area=VALUES(locality_area),
                    pin_code=VALUES(pin_code),
                    latitude=VALUES(latitude),
                    longitude=VALUES(longitude),
                    severity_level=VALUES(severity_level),
                    threat_to_human_life=VALUES(threat_to_human_life),
                    number_of_casualties=VALUES(number_of_casualties),
                    number_of_injuries=VALUES(number_of_injuries),
                    weapon_hazard_involved=VALUES(weapon_hazard_involved),
                    dispatch_needed=VALUES(dispatch_needed),
                    dispatch_reason=VALUES(dispatch_reason),
                    conversation_history=VALUES(conversation_history)
            """

            def _safe_float(val):
                try:
                    return float(val) if val is not None else None
                except (ValueError, TypeError):
                    return None

            def _safe_int(val):
                try:
                    return int(val) if val is not None else 0
                except (ValueError, TypeError):
                    return 0

            values = (
                document_id,
                data.get("situation_id"),
                data.get("report_date"),
                data.get("report_time"),
                data.get("emergency_category"),
                data.get("emergency_sub_type"),
                data.get("incident_description"),
                data.get("reporter_type"),
                data.get("caller_name"),
                data.get("caller_contact_number"),
                data.get("caller_gender"),
                data.get("state"),
                data.get("district_city"),
                data.get("locality_area"),
                data.get("pin_code"),
                _safe_float(data.get("latitude")),
                _safe_float(data.get("longitude")),
                data.get("severity_level"),
                data.get("threat_to_human_life"),
                _safe_int(data.get("number_of_casualties")),
                _safe_int(data.get("number_of_injuries")),
                data.get("weapon_hazard_involved"),
                dispatch_needed,
                data.get("dispatch_reason"),
                history,
            )

            cursor.execute(query, values)
            self.connection.commit()
            print(f"[MySQLLogger] Logged '{document_id}' to MySQL.")

        except Error as e:
            print(f"[MySQLLogger] Error: {e}")
            self.connection.rollback()
        finally:
            if "cursor" in locals():
                cursor.close()
