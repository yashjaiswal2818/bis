"""GeM & Public Procurement Specification Clause Generator.

Generates standardized, legally compliant technical specification clauses
ready to be copy-pasted into GeM (Government e-Marketplace) and CPPP tenders.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.compliance.qco_mandatory_engine import QCOMandatoryEngine
from src.compliance.standards_lifecycle_tracker import StandardsLifecycleTracker
from src.graph.allied_standards_classifier import AlliedStandardsClassifier


@dataclass
class GeMSpecificationClause:
    is_code: str
    title: str
    product_clause: str
    qco_compliance_clause: str
    testing_and_sampling_clause: str
    full_tender_specification_text: str


class GeMSpecificationGenerator:
    def __init__(self):
        self.qco_engine = QCOMandatoryEngine()
        self.lifecycle_tracker = StandardsLifecycleTracker()
        self.allied_classifier = AlliedStandardsClassifier()

    def generate_clause(self, is_code: str) -> GeMSpecificationClause:
        """Generates a complete technical specification clause for a recommended standard."""
        lifecycle = self.lifecycle_tracker.evaluate_standard_currency(is_code)
        active_code = lifecycle.latest_active_code
        qco_report = self.qco_engine.check_compliance(active_code)
        allied_data = self.allied_classifier.get_classified_allied_standards(active_code)

        # 1. Product Conformance Clause
        revision_text = f" (incorporating {lifecycle.amendments_count} amendments)" if lifecycle.amendments_count else ""
        product_clause = (
            f"1. PRODUCT SPECIFICATION & CONFORMANCE:\n"
            f"   The supplied item shall strictly conform to Indian Standard {active_code}{revision_text}. "
            f"   Any supply deviating from the physical, chemical, or mechanical requirements of this standard "
            f"   shall be summarily rejected at the consignee's end."
        )

        # 2. Mandatory Certification & QCO Clause
        if qco_report and qco_report.is_mandatory:
            qco_clause = (
                f"2. MANDATORY REGULATORY COMPLIANCE ({qco_report.scheme_type.upper()}):\n"
                f"   Under the {qco_report.order_name} issued by {qco_report.issuing_ministry}, "
                f"   the offered product MUST bear the valid Standard Mark (ISI / CRS Mark). "
                f"   Bidders MUST upload a copy of their valid BIS License (CML Number or R-Number) "
                f"   active as on the date of bid submission. Offers without valid BIS certification shall be rejected."
            )
        else:
            qco_clause = (
                f"2. QUALITY ASSURANCE:\n"
                f"   The manufacturer must submit internal test certificates and ISO 9001 quality conformance "
                f"   guaranteeing adherence to {active_code}."
            )

        # 3. Normative Testing & Sampling Clause
        test_standards = [t["is_code"] for t in allied_data.normative_tests[:4]]
        if test_standards:
            test_str = ", ".join(test_standards)
            testing_clause = (
                f"3. SAMPLING, TESTING & ACCEPTANCE CRITERIA:\n"
                f"   Batch sampling, routine tests, and acceptance tests shall be carried out strictly "
                f"   in accordance with relevant normative test codes: {test_str}. "
                f"   The supplier shall furnish Manufacturer's Test Certificate (MTC) for each consignment."
            )
        else:
            testing_clause = (
                "3. SAMPLING & TESTING:\n"
                "   Sampling and testing shall be carried out in accordance with standard BIS sampling guidelines. "
                "   Third-party testing from a NABL-accredited laboratory may be required by the buyer."
            )

        full_text = f"{product_clause}\n\n{qco_clause}\n\n{testing_clause}"

        return GeMSpecificationClause(
            is_code=active_code,
            title=f"Technical Specification for {active_code}",
            product_clause=product_clause,
            qco_compliance_clause=qco_clause,
            testing_and_sampling_clause=testing_clause,
            full_tender_specification_text=full_text,
        )
