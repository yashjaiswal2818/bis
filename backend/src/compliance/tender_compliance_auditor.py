"""Tender Compliance & Hallmark Auditor.

Audits tender clauses, specifications, and BoQ items to verify:
1. Indian Standard (IS Code) citation.
2. Mandatory Certification Mark citation (BIS Hallmark with 6-digit HUID, ISI Mark, or CRS).
3. If no standard or hallmark/mark is missing, explicitly confirms "Everything is fine".
2. Active vs Superseded currency check against standards_master.db.
3. Mandatory Certification Mark citation:
   - Scheme-I (ISI Mark) under statutory QCOs
   - Scheme-II (CRS Registration) under MeitY / MNRE
   - Scheme-IV (BIS Hallmark with 6-digit HUID)
4. Strict Fail-Closed Build Philosophy:
   - COMPLIANT: Active standard and mandatory marks are present and verified.
   - NON_COMPLIANT: Missing mandatory standard/mark or obsolete standard cited.
   - UNVERIFIED: Ambiguous specification or low retrieval confidence.
   - NOT_APPLICABLE: Non-standardized labor, civil excavation, or services exempt from BIS.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.database.sqlite_manager import DB_PATH, extract_base_code, get_connection


# Keywords defining non-standardized services, labor, and civil earthwork exempt from BIS
EXEMPT_SERVICE_KEYWORDS = [
    "unskilled labour", "skilled labour", "coolie", "mazdoor", "bhisti",
    "earth work in excavation", "excavation by mechanical means", "disposal of surplus earth",
    "site clearance", "clearing jungle", "felling trees", "rough excavation",
    "loading and unloading", "carriage of materials", "transportation charges",
    "freight charges", "housekeeping services", "security services",
    "consultancy services", "survey charges", "hiring charges of machinery",
    "dismantling and demolishing", "cleaning and sweeping", "catering services"
]


@dataclass
class ItemAuditVerdict:
    clause_text: str
    recommended_is_code: str | None
    recommended_title: str | None
    

    # IS Code Check
    is_code_missing: bool
    missing_is_code: str | None
    detected_is_code: str | None
    

    # Currency & Superseded Status
    is_superseded: bool = False
    superseded_by: str | None = None

    # Hallmark & Certification Checks
    scheme_type: str | None
    hallmark_required: bool
    hallmark_missing: bool
    missing_hallmark: str | None
    
    isi_mark_required: bool
    isi_mark_missing: bool
    missing_isi_mark: str | None
    
    crs_required: bool
    crs_missing: bool
    missing_crs: str | None
    
    any_mark_missing: bool
    missing_mark_label: str | None
    
    scheme_type: str | None = None
    hallmark_required: bool = False
    hallmark_missing: bool = False
    missing_hallmark: str | None = None

    isi_mark_required: bool = False
    isi_mark_missing: bool = False
    missing_isi_mark: str | None = None

    crs_required: bool = False
    crs_missing: bool = False
    missing_crs: str | None = None

    any_mark_missing: bool = False
    missing_mark_label: str | None = None

    # Non-standardized Service Exemption
    is_exempt_service: bool = False

    # Statutory QCO Rules
    qco_details: dict[str, Any] | None = None

    # Overall Item Verdict
    is_fine: bool
    verdict: str  # "Everything is fine" when compliant
    verdict_message: str
    compliance_status: str  # "FINE" | "NON_COMPLIANT"
    
    is_fine: bool = False
    verdict: str = "Unverified"
    verdict_message: str = "Audit pending"
    compliance_status: str = "UNVERIFIED"  # "COMPLIANT" | "NON_COMPLIANT" | "UNVERIFIED" | "NOT_APPLICABLE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_fine": self.is_fine,
            "verdict": self.verdict,
            "verdict_message": self.verdict_message,
            "compliance_status": self.compliance_status,
            "is_code_missing": self.is_code_missing,
            "missing_is_code": self.missing_is_code,
            "detected_is_code": self.detected_is_code,
            "is_superseded": self.is_superseded,
            "superseded_by": self.superseded_by,
            "is_exempt_service": self.is_exempt_service,
            "scheme_type": self.scheme_type,
            "hallmark_required": self.hallmark_required,
            "hallmark_missing": self.hallmark_missing,
            "missing_hallmark": self.missing_hallmark,
            "isi_mark_required": self.isi_mark_required,
            "isi_mark_missing": self.isi_mark_missing,
            "missing_isi_mark": self.missing_isi_mark,
            "crs_required": self.crs_required,
            "crs_missing": self.crs_missing,
            "missing_crs": self.missing_crs,
            "any_mark_missing": self.any_mark_missing,
            "missing_mark_label": self.missing_mark_label,
            "qco_details": self.qco_details,
        }


class TenderComplianceAuditor:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def _query_qco_rules(self, is_code: str) -> list[dict[str, Any]]:
        """Queries SQLite for QCO rules matching the given code or base standard."""
        base = extract_base_code(is_code)
        try:
            with get_connection(self.db_path) as conn:
                rows = conn.execute(
                    """
                    SELECT * FROM qco_compliance_rules
                    WHERE is_code = ? OR is_code LIKE ?
                    """,
                    (is_code, f"{base}%"),
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []

    def _check_superseded_status(self, is_code: str) -> tuple[bool, str | None]:
        """Checks if a standard is marked as SUPERSEDED in the master database."""
        try:
            base = extract_base_code(is_code)
            with get_connection(self.db_path) as conn:
                row = conn.execute(
                    """
                    SELECT status, superseded_by FROM standards_registry
                    WHERE is_code = ? OR is_code_norm = ? OR base_code = ?
                    LIMIT 1
                    """,
                    (is_code, is_code.lower().replace(" ", ""), base),
                ).fetchone()
                if row and row["status"] == "SUPERSEDED":
                    return True, row["superseded_by"]
        except Exception:
            pass
        return False, None

    def _is_exempt_service(self, text: str) -> bool:
        """Determines if a clause explicitly describes unstandardized labor, civil earthwork, or service."""
        lower = text.lower()
        return any(kw in lower for kw in EXEMPT_SERVICE_KEYWORDS)

    def audit_clause(
        self,
        clause_text: str,
        recommended_standards: list[Any],
    ) -> ItemAuditVerdict:
        """Audits a single tender clause against recommended standards and QCO rules."""
        """Audits a single tender clause against recommended standards and QCO rules.

        Implements fail-closed design:
        - If no standards match: checks for exempt service (NOT_APPLICABLE), otherwise UNVERIFIED.
        - If standards match: verifies code citation, currency, and mandatory certification marks.
        """
        # Fail-closed check: No recommended standards available
        if not recommended_standards:
            return ItemAuditVerdict(
                clause_text=clause_text,
                recommended_is_code=None,
                recommended_title=None,
                is_code_missing=False,
                missing_is_code=None,
                detected_is_code=None,
                scheme_type=None,
                hallmark_required=False,
                hallmark_missing=False,
                missing_hallmark=None,
                isi_mark_required=False,
                isi_mark_missing=False,
                missing_isi_mark=None,
                crs_required=False,
                crs_missing=False,
                missing_crs=None,
                any_mark_missing=False,
                missing_mark_label=None,
                is_fine=True,
                verdict="Everything is fine",
                verdict_message="No mandatory standard or hallmark required for this general item.",
                compliance_status="FINE",
            )
            if self._is_exempt_service(clause_text):
                return ItemAuditVerdict(
                    clause_text=clause_text,
                    recommended_is_code=None,
                    recommended_title=None,
                    is_code_missing=False,
                    missing_is_code=None,
                    detected_is_code=None,
                    is_exempt_service=True,
                    is_fine=True,
                    verdict="Not Applicable",
                    verdict_message="No mandatory Indian Standard or certification mark applies to this general service or labor item.",
                    compliance_status="NOT_APPLICABLE",
                )
            else:
                return ItemAuditVerdict(
                    clause_text=clause_text,
                    recommended_is_code=None,
                    recommended_title=None,
                    is_code_missing=True,
                    missing_is_code="Unknown / Unmatched Standard",
                    detected_is_code=None,
                    is_fine=False,
                    verdict="Unverified: Manual Review Required",
                    verdict_message="Unable to determine applicable Indian Standard with high confidence. Specification requires manual verification.",
                    compliance_status="UNVERIFIED",
                )

        top_std = recommended_standards[0]
        # Handle dict or RecommendedStandard object
        if isinstance(top_std, dict):
            rec_code = top_std.get("is_code", "")
            rec_title = top_std.get("title", "")
            qco_rules = top_std.get("qco_rules") or []
        else:
            rec_code = getattr(top_std, "is_code", "")
            rec_title = getattr(top_std, "title", "")
            qco_rules = getattr(top_std, "qco_rules", []) or []

        if not qco_rules and rec_code:
            qco_rules = self._query_qco_rules(rec_code)

        base_code = extract_base_code(rec_code)
        code_num_match = re.search(r"\d+", base_code)
        code_num = code_num_match.group(0) if code_num_match else ""

        # 1. Check if IS code is cited in the clause text
        detected_is_code = None
        is_code_missing = True

        # Check for exact base code or number with IS prefix (e.g. "IS 694", "IS-694", "IS: 694", "IS694")
        if code_num:
            is_pattern = re.compile(rf"\bIS\s*[:\-–]?\s*{re.escape(code_num)}\b", re.IGNORECASE)
            match = is_pattern.search(clause_text)
            if match:
                is_code_missing = False
                detected_is_code = match.group(0).strip()
            elif re.search(rf"\b{re.escape(base_code)}\b", clause_text, re.IGNORECASE):
                is_code_missing = False
                detected_is_code = base_code

        # Check if other recommended standards are cited
        # Check alternative top recommendations
        if is_code_missing:
            for alt_std in recommended_standards[1:3]:
                alt_code = alt_std.get("is_code", "") if isinstance(alt_std, dict) else getattr(alt_std, "is_code", "")
                alt_base = extract_base_code(alt_code)
                alt_num_match = re.search(r"\d+", alt_base)
                if alt_num_match:
                    alt_pat = re.compile(rf"\bIS\s*[:\-–]?\s*{re.escape(alt_num_match.group(0))}\b", re.IGNORECASE)
                    alt_match = alt_pat.search(clause_text)
                    if alt_match:
                        is_code_missing = False
                        detected_is_code = alt_match.group(0).strip()
                        break

        missing_is_code = rec_code if is_code_missing else None

        # 2. Check Hallmark & Mandatory Certification Mark requirements
        # 2. Currency & Superseded check
        is_superseded = False
        superseded_by = None
        if detected_is_code:
            is_superseded, superseded_by = self._check_superseded_status(detected_is_code)

        # 3. Check Hallmark & Mandatory Certification Mark requirements
        scheme_type = None
        hallmark_required = False
        hallmark_missing = False
        missing_hallmark = None

        isi_mark_required = False
        isi_mark_missing = False
        missing_isi_mark = None

        crs_required = False
        crs_missing = False
        missing_crs = None

        # Inspect QCO rules or known schemes
        # Inspect QCO rules or known statutory schemes
        is_hallmark_item = (
            "1417" in base_code
            or "2112" in base_code
            or "15820" in base_code
            or any("hallmark" in q.get("scheme_type", "").lower() for q in qco_rules)
            or any(kw in clause_text.lower() for kw in ["gold", "silver jewellery", "gold coin", "gold medal", "silver medal", "bullion"])
        )

        for q in qco_rules:
            st = q.get("scheme_type", "")
            if "Scheme-IV" in st or "Hallmark" in st:
                is_hallmark_item = True
            elif "Scheme-I" in st or "ISI" in st:
                isi_mark_required = True
                scheme_type = scheme_type or "Scheme-I (Mandatory ISI Mark)"
            elif "Scheme-II" in st or "CRS" in st:
                crs_required = True
                scheme_type = scheme_type or "Scheme-II (Compulsory Registration Scheme - CRS)"

        if is_hallmark_item:
            hallmark_required = True
            scheme_type = "Scheme-IV (Mandatory BIS Hallmark with 6-Digit HUID)"
            # Check for hallmark citation in clause text
            hallmark_pat = re.compile(
                r"\b(hallmark(ed|ing)?|huid|bis\s*hallmark|assaying|fineness\s*916|fineness\s*999)\b",
                re.IGNORECASE,
            )
            if not hallmark_pat.search(clause_text):
                hallmark_missing = True
                missing_hallmark = "Mandatory BIS Hallmark with 6-digit HUID (Scheme-IV)"

        elif isi_mark_required:
            isi_pat = re.compile(
                r"\b(isi\s*mark(ed)?|isi\s*certif\w*|bis\s*license|bis\s*cml|cml\s*no|bis\s*standard\s*mark)\b",
                re.IGNORECASE,
            )
            if not isi_pat.search(clause_text):
                isi_mark_missing = True
                missing_isi_mark = "Mandatory BIS ISI Mark (Scheme-I under QCO)"

        elif crs_required:
            crs_pat = re.compile(
                r"\b(crs|r[-\s]?(no|number)|compulsory\s*registration|bis\s*registration)\b",
                re.IGNORECASE,
            )
            if not crs_pat.search(clause_text):
                crs_missing = True
                missing_crs = "Mandatory BIS CRS Registration with R-Number (Scheme-II)"

        any_mark_missing = hallmark_missing or isi_mark_missing or crs_missing
        missing_mark_label = missing_hallmark or missing_isi_mark or missing_crs

        # 4. Determine Final Verdict adhering to Build Philosophy
        # Must not be missing code, must not be superseded, must not miss required statutory marks
        if is_superseded:
            is_fine = False
            compliance_status = "NON_COMPLIANT"
            verdict = f"Non-Compliant: Obsolete standard {detected_is_code} cited"
            verdict_message = f"NON-COMPLIANT: Standard {detected_is_code} is superseded by {superseded_by or 'modern active revision'}. Update tender specification to latest active Indian Standard."
        elif is_code_missing or any_mark_missing:
            is_fine = False
            compliance_status = "NON_COMPLIANT"
            missing_parts = []
            if is_code_missing:
                missing_parts.append(f"Missing Indian Standard: {missing_is_code}")
            if hallmark_missing:
                missing_parts.append(f"Missing {missing_hallmark}")
            elif isi_mark_missing:
                missing_parts.append(f"Missing {missing_isi_mark}")
            elif crs_missing:
                missing_parts.append(f"Missing {missing_crs}")

            verdict = " & ".join(missing_parts)
            verdict_message = f"Compliance Notice: {'; '.join(missing_parts)}."
            verdict_message = f"Compliance Gaps Detected: {'; '.join(missing_parts)}."
        else:
            is_fine = True
            compliance_status = "COMPLIANT"
            verdict = "Everything is fine"
            if detected_is_code:
                verdict_message = f"Everything is fine: Conforms to active standard {detected_is_code} and all required statutory certifications/hallmarks are cited."
            else:
                verdict_message = "Everything is fine: All applicable Indian Standards and statutory marks are cited."

        primary_qco = qco_rules[0] if qco_rules else None

        return ItemAuditVerdict(
            clause_text=clause_text,
            recommended_is_code=rec_code,
            recommended_title=rec_title,
            is_code_missing=is_code_missing,
            missing_is_code=missing_is_code,
            detected_is_code=detected_is_code,
            is_superseded=is_superseded,
            superseded_by=superseded_by,
            scheme_type=scheme_type,
            hallmark_required=hallmark_required,
            hallmark_missing=hallmark_missing,
            missing_hallmark=missing_hallmark,
            isi_mark_required=isi_mark_required,
            isi_mark_missing=isi_mark_missing,
            missing_isi_mark=missing_isi_mark,
            crs_required=crs_required,
            crs_missing=crs_missing,
            missing_crs=missing_crs,
            any_mark_missing=any_mark_missing,
            missing_mark_label=missing_mark_label,
            is_exempt_service=False,
            qco_details=primary_qco,
            is_fine=is_fine,
            verdict=verdict,
            verdict_message=verdict_message,
            compliance_status=compliance_status,
        )

    def summarize_document_audit(self, audited_items: list[dict[str, Any]]) -> dict[str, Any]:
        """Summarizes document-level compliance status across all audited items."""
        total = len(audited_items)
        if total == 0:
            return {
                "all_compliant": True,
                "overall_verdict": "Everything is fine",
                "summary_message": "Everything is fine: Document contains no technical specification gaps.",
                "total_items": 0,
                "fine_count": 0,
                "missing_count": 0,
                "compliant_count": 0,
                "non_compliant_count": 0,
                "unverified_count": 0,
                "not_applicable_count": 0,
                "missing_standards_count": 0,
                "missing_hallmarks_count": 0,
                "missing_isi_count": 0,
            }

        fine_count = sum(1 for it in audited_items if it.get("is_fine", False))
        missing_count = total - fine_count
        compliant_count = sum(1 for it in audited_items if it.get("compliance_status") in ("COMPLIANT", "FINE"))
        non_compliant_count = sum(1 for it in audited_items if it.get("compliance_status") == "NON_COMPLIANT")
        unverified_count = sum(1 for it in audited_items if it.get("compliance_status") == "UNVERIFIED")
        not_applicable_count = sum(1 for it in audited_items if it.get("compliance_status") == "NOT_APPLICABLE")

        missing_count = non_compliant_count + unverified_count
        missing_standards_count = sum(1 for it in audited_items if it.get("is_code_missing", False))
        missing_hallmarks_count = sum(1 for it in audited_items if it.get("hallmark_missing", False))
        missing_isi_count = sum(1 for it in audited_items if it.get("isi_mark_missing", False))
        all_compliant = (fine_count == total)

        if all_compliant:
            overall_verdict = "Everything is fine"
            summary_message = (
                "Everything is fine: All technical clauses and line items cite the required "
                "Indian Standards and mandatory certifications/hallmarks."
                "Indian Standards and statutory certifications/hallmarks."
            )
        else:
            overall_verdict = "Compliance Gaps Detected"
            parts = []
            if missing_standards_count > 0:
                parts.append(f"{missing_standards_count} item(s) missing Indian Standards")
            if non_compliant_count > 0:
                parts.append(f"{non_compliant_count} non-compliant item(s)")
            if unverified_count > 0:
                parts.append(f"{unverified_count} unverified item(s) requiring manual review")
            if missing_hallmarks_count > 0:
                parts.append(f"{missing_hallmarks_count} item(s) missing mandatory BIS 6-Digit HUID Hallmarking")
            if missing_isi_count > 0:
                parts.append(f"{missing_isi_count} item(s) missing mandatory BIS ISI Mark under QCO")
            

            summary_message = f"Found compliance gaps: {', '.join(parts)}."

        return {
            "all_compliant": all_compliant,
            "overall_verdict": overall_verdict,
            "summary_message": summary_message,
            "total_items": total,
            "fine_count": fine_count,
            "missing_count": missing_count,
            "compliant_count": compliant_count,
            "non_compliant_count": non_compliant_count,
            "unverified_count": unverified_count,
            "not_applicable_count": not_applicable_count,
            "missing_standards_count": missing_standards_count,
            "missing_hallmarks_count": missing_hallmarks_count,
            "missing_isi_count": missing_isi_count,
        }
