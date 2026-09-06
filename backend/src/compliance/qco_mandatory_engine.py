"""Quality Control Order (QCO) & Mandatory Certification Compliance Engine.

Identifies whether an Indian Standard is mandated by line ministries
under Scheme-I (ISI Mark), Scheme-II (Compulsory Registration Scheme), or Scheme-IV (Hallmarking).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.database.sqlite_manager import DB_PATH, get_connection


@dataclass
class ComplianceReport:
    is_code: str
    is_mandatory: bool
    scheme_type: str
    issuing_ministry: str
    order_name: str
    effective_date: str | None
    warning_text: str
    procurement_clause: str


class QCOMandatoryEngine:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def check_compliance(self, is_code: str) -> ComplianceReport | None:
        """Checks if a standard has an active Quality Control Order."""
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT * FROM qco_compliance_rules
                WHERE is_code = ?
                """,
                (is_code,),
            ).fetchone()

            if not row:
                # Voluntary standard
                return ComplianceReport(
                    is_code=is_code,
                    is_mandatory=False,
                    scheme_type="Voluntary / Standard BIS Conformance",
                    issuing_ministry="Bureau of Indian Standards",
                    order_name="General BIS Standards Catalogue",
                    effective_date=None,
                    warning_text="Voluntary standard: Conformance is recommended for quality assurance but not legally mandated by a ministry QCO.",
                    procurement_clause=f"The product shall conform to the specifications laid down in {is_code}.",
                )

            data = dict(row)
            scheme = data["scheme_type"]
            clause = ""
            if "Scheme-I" in scheme:
                clause = (
                    f"MANDATORY COMPLIANCE: The offered product must conform to {is_code} and bear the "
                    f"valid Standard Mark (ISI Mark). The bidder must submit a copy of the valid BIS CML "
                    f"License valid as on the date of tender submission."
                )
            elif "Scheme-II" in scheme:
                clause = (
                    f"MANDATORY COMPLIANCE: The product must be registered under BIS Compulsory Registration "
                    f"Scheme (CRS) as per {is_code}. The bidder must submit a valid BIS Registration Number (R-Number)."
                )
            else:
                clause = f"The product must strictly conform to {is_code} as per {data['order_name']}."

            return ComplianceReport(
                is_code=is_code,
                is_mandatory=bool(data["is_mandatory"]),
                scheme_type=data["scheme_type"],
                issuing_ministry=data["issuing_ministry"],
                order_name=data["order_name"],
                effective_date=data["effective_date"],
                warning_text=data["compliance_warning"],
                procurement_clause=clause,
            )
