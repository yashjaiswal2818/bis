import fitz

doc = fitz.open()
page = doc.new_page()

text = """GOVERNMENT OF INDIA
MINISTRY OF DEFENCE
ORDNANCE FACTORY BADMAL
BALANGIR, ODISHA - 767070

NOTICE INVITING E-TENDER
Tender No: 3012/OFBL/TE-09/2026-27

1. Name of Work: Replacement of Defective 415Volt LT Main Distribution Panel & 415 V LT Main Distribution Board, Street Light Incoming Cables, Main Incoming Power Cables and circuit Wirings at Officers Club of Ordnance Factory Badmal.

2. Technical Specifications:
The contractor shall supply and install PVC insulated electrical power cables suitable for up to 1100 Volts. The cables must be of heavy-duty grade and suitable for underground trench installation.

3. Testing and Certification:
All supplied materials must comply with the relevant Bureau of Indian Standards. The vendor must provide the manufacturer's test certificate along with the supply.

4. Eligibility Criteria:
Experience of having successfully completed Similar nature of Electrical works i.e. low Tension Electric Works (up to 1100 volts) in Central Govt./ State Govt./PSUs having an annual turnover of Rs 100 crore.
"""

page.insert_text(fitz.Point(50, 50), text, fontsize=12)
doc.save("Demo_Tender_Badmal.pdf")
print("PDF created successfully at Demo_Tender_Badmal.pdf")
