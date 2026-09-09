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
                    f"MANDATORY STATUTORY COMPLIANCE: Under Quality Control Orders issued under the BIS Act 2016, "
                    f"the offered product must conform to {is_code} and bear the mandatory Standard Mark (ISI Mark). "
                    f"The bidder must furnish a valid BIS License (CML Number) valid as on the bid closing date. "
                    f"Supplies without genuine ISI marking will be summarily rejected and reported per GFR Rule 144(xi)."
                )
            elif "Scheme-II" in scheme or "CRS" in scheme:
                clause = (
                    f"MANDATORY STATUTORY COMPLIANCE: The product must be registered under the BIS Compulsory "
                    f"Registration Scheme (CRS) pursuant to {is_code}. The bidder must submit an active BIS "
                    f"Registration Number (R-Number) verifiable on the BIS portal before commercial award."
                )
            elif "Scheme-IV" in scheme or "Hallmarking" in scheme:
                clause = (
                    f"MANDATORY STATUTORY COMPLIANCE: Under the Department of Consumer Affairs (DoCA) Hallmarking Order, "
                    f"all precious metal articles supplied under {is_code} must carry the 3 mandatory hallmark marks: "
                    f"BIS Logo, Purity in Carats/Fineness, and a verifiable 6-digit alphanumeric HUID (Hallmark Unique Identification) "
                    f"issued by a recognized BIS Assaying and Hallmarking Centre."
                )
            else:
                clause = f"MANDATORY COMPLIANCE: The product must strictly conform to {is_code} as per {data['order_name']}."

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
