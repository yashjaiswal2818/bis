"""Verification test for DoCA Certification, CRS, Hallmarking, and Allied Taxonomy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.retrieval.hybrid_search_orchestrator import HybridSearchOrchestrator
from src.compliance.qco_mandatory_engine import QCOMandatoryEngine
from src.procurement.gem_specification_generator import GeMSpecificationGenerator

def test():
    orchestrator = HybridSearchOrchestrator()
    gem_gen = GeMSpecificationGenerator()

    # 1. Test DoCA Hallmarking
    print("\n=== TEST 1: DoCA Hallmarking ===")
    recs = orchestrator.search("Mandatory gold jewellery purity marking and 6-digit HUID hallmarking requirements.", top_k=3)
    for r in recs:
        print(f"Rank {r.rank}: {r.is_code} | {r.title} | Reaffirmed: {r.reaffirmation_year} | Amendments: {r.amendments_count}")
        if r.qco_rules:
            print(f"   QCO Scheme: {r.qco_rules[0]['scheme_type']} | Ministry: {r.qco_rules[0]['issuing_ministry']}")
        print("   Allied Standards:", [(a['target_is_code'], a.get('relation_type'), a.get('label')) for a in r.allied_standards[:3]])

    # 2. Test Scheme-II CRS
    print("\n=== TEST 2: Scheme-II CRS Electronics ===")
    recs = orchestrator.search("Safety requirements for secondary lithium cells and batteries under compulsory registration scheme.", top_k=3)
    for r in recs:
        print(f"Rank {r.rank}: {r.is_code} | {r.title}")
        if r.qco_rules:
            print(f"   QCO Scheme: {r.qco_rules[0]['scheme_type']} | Ministry: {r.qco_rules[0]['issuing_ministry']}")

    # 3. Test Scheme-I Cement & Allied Test Methods
    print("\n=== TEST 3: Scheme-I Cement & Allied Test Methods ===")
    recs = orchestrator.search("43 Grade Ordinary Portland Cement", top_k=3)
    for r in recs:
        print(f"Rank {r.rank}: {r.is_code} | {r.title}")
        print("   Allied Taxonomy:", [(a['target_is_code'], a.get('relation_type'), a.get('label')) for a in r.allied_standards[:4]])

    # 4. Test GeM Clause for Gold Hallmarking
    print("\n=== TEST 4: GeM Clause for Gold Hallmarking ===")
    clause = gem_gen.generate_clause("IS 1417: 2016")
    print(clause.qco_compliance_clause)

if __name__ == "__main__":
    test()
