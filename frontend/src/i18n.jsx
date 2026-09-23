import React, { createContext, useCallback, useContext, useState } from 'react';

/**
 * Site-wide UI string translations. Separate from `hit.translations[lang]`,
 * which is backend-sourced translated content for specific standards' titles
 * and scope text -- that stays as-is. This dictionary covers everything else:
 * every static label, button, heading and message in the app chrome, so the
 * EN/HI toggle actually changes the whole site, not just the search-result
 * cards that happen to have a server-provided translation.
 */
const STRINGS = {
  // -- shared / nav --
  nav_find_standards: { en: 'Find Standards', hi: 'मानक खोजें' },
  nav_tender_auditor: { en: 'Tender & BoQ Auditor', hi: 'निविदा एवं BoQ ऑडिटर' },
  nav_evaluation_sandbox: { en: 'Evaluation Sandbox', hi: 'मूल्यांकन सैंडबॉक्स' },
  common_search: { en: 'Search', hi: 'खोजें' },
  common_copied: { en: 'Copied', hi: 'कॉपी हो गया' },
  common_loading: { en: 'Loading…', hi: 'लोड हो रहा है…' },

  // -- header --
  header_tagline: { en: 'Indian Standards identification, QCO verification & GeM clause drafting', hi: 'भारतीय मानक पहचान, QCO सत्यापन एवं GeM क्लॉज़ निर्माण' },
  header_engine_active: { en: 'Engine Active', hi: 'इंजन सक्रिय' },
  header_connecting: { en: 'Connecting…', hi: 'कनेक्ट हो रहा है…' },
  header_skip_link: { en: 'Skip to main content', hi: 'मुख्य सामग्री पर जाएँ' },

  // -- footer --
  footer_desc: { en: 'Automating standard identification and tender compliance verification.', hi: 'मानक पहचान एवं निविदा अनुपालन सत्यापन का स्वचालन।' },
  footer_col_engine: { en: 'The engine', hi: 'इंजन' },
  footer_col_data: { en: 'Data & provenance', hi: 'डेटा एवं स्रोत' },
  footer_registry_snapshot: { en: 'Registry Snapshot: {{date}}', hi: 'रजिस्ट्री स्नैपशॉट: {{date}}' },
  footer_qco_source: { en: 'QCO Source: bis.gov.in', hi: 'QCO स्रोत: bis.gov.in' },
  footer_known_limitations: { en: 'Known Limitations', hi: 'ज्ञात सीमाएँ' },
  footer_col_resources: { en: 'Resources', hi: 'संसाधन' },

  // -- search landing: modes / placeholders --
  mode_product: { en: 'Product Description', hi: 'उत्पाद विवरण' },
  mode_spec: { en: 'Technical Specification', hi: 'तकनीकी विनिर्देश' },
  mode_multilingual: { en: 'हिन्दी / Hinglish', hi: 'हिन्दी / Hinglish' },
  mode_natural: { en: 'Natural Language', hi: 'सामान्य भाषा' },
  placeholder_product: { en: 'Describe a product, material, or equipment…', hi: 'किसी उत्पाद, सामग्री, या उपकरण का वर्णन करें…' },
  placeholder_spec: { en: 'Paste a tender clause, BoQ line item, or technical specification…', hi: 'निविदा क्लॉज़, BoQ लाइन-आइटम, या तकनीकी विनिर्देश पेस्ट करें…' },
  placeholder_multilingual: { en: 'अपनी भाषा में खोजें — हिन्दी या Hinglish…', hi: 'अपनी भाषा में खोजें — हिन्दी या Hinglish…' },
  placeholder_natural: { en: 'Ask a question about standards, testing, or compliance…', hi: 'मानकों, परीक्षण, या अनुपालन के बारे में प्रश्न पूछें…' },
  placeholder_results_search: { en: 'Search Indian Standards…', hi: 'भारतीय मानक खोजें…' },

  // -- hero --
  hero_title_pre: { en: 'Find the right ', hi: 'सही ' },
  hero_title_accent: { en: 'Indian Standard', hi: 'भारतीय मानक' },
  hero_title_post: { en: ' for every procurement line item', hi: ' खोजें — हर खरीद लाइन-आइटम के लिए' },
  hero_sub: { en: 'Semantic search across 33,500+ BIS standards with automatic Quality Control Order verification, edition mapping, and allied-standard discovery.', hi: '33,500+ BIS मानकों में सिमैंटिक खोज, साथ में स्वचालित गुणवत्ता नियंत्रण आदेश (QCO) सत्यापन, संस्करण मानचित्रण एवं संबद्ध मानक खोज।' },
  chip_try: { en: 'Try:', hi: 'आज़माएँ:' },
  cta_audit_tender: { en: 'Audit a tender document', hi: 'निविदा दस्तावेज़ ऑडिट करें' },

  // -- trust card --
  trust_title: { en: 'Live registry', hi: 'लाइव रजिस्ट्री' },
  trust_sub: { en: 'Struck fresh from the running backend', hi: 'चालू बैकएंड से सीधे प्राप्त' },
  trust_standards_indexed: { en: 'Standards indexed', hi: 'सूचीबद्ध मानक' },
  trust_qco_notified: { en: 'QCO-notified products', hi: 'QCO-अधिसूचित उत्पाद' },
  trust_cert_schemes: { en: 'Certification schemes', hi: 'प्रमाणन योजनाएँ' },
  trust_edition_links: { en: 'Edition links', hi: 'संस्करण लिंक' },
  trust_source: { en: 'Source: {{source}}', hi: 'स्रोत: {{source}}' },
  trust_snapshot: { en: 'Snapshot: {{date}}', hi: 'स्नैपशॉट: {{date}}' },

  // -- capability cards --
  cap_heading: { en: 'What can this engine do?', hi: 'यह इंजन क्या कर सकता है?' },
  cap1_title: { en: 'Find applicable standards', hi: 'लागू मानक खोजें' },
  cap1_desc: { en: 'Search by product name, technical specification, or natural-language question.', hi: 'उत्पाद के नाम, तकनीकी विवरण, या सामान्य भाषा में प्रश्न द्वारा खोजें।' },
  cap2_title: { en: 'Audit a tender or BoQ', hi: 'निविदा या BoQ ऑडिट करें' },
  cap2_desc: { en: 'Upload a PDF or CSV and verify every line item for standard compliance.', hi: 'PDF या CSV अपलोड करें और हर लाइन-आइटम की मानक अनुरूपता जाँचें।' },
  cap3_title: { en: 'Check mandatory certification', hi: 'अनिवार्य प्रमाणन जाँचें' },
  cap3_desc: { en: 'Verify ISI, CRS, and Hallmarking QCO enforcement for any product.', hi: 'किसी भी उत्पाद के लिए ISI, CRS एवं हॉलमार्किंग QCO प्रवर्तन सत्यापित करें।' },
  cap4_title: { en: 'Check edition currency', hi: 'संस्करण की वैधता जाँचें' },
  cap4_desc: { en: 'Amber badges flag superseded editions and link to the current version.', hi: 'एम्बर बैज पुराने संस्करणों को चिह्नित करते हैं और वर्तमान संस्करण से जोड़ते हैं।' },

  // -- recent searches / QCO watch / external resources --
  recent_searches: { en: 'Recent searches', hi: 'हाल की खोजें' },
  tbl_query: { en: 'Query', hi: 'प्रश्न' },
  tbl_top_result: { en: 'Top result', hi: 'शीर्ष परिणाम' },
  tbl_confidence: { en: 'Confidence', hi: 'विश्वास स्तर' },
  tbl_time: { en: 'Time', hi: 'समय' },
  recent_empty: { en: 'Your searches will appear here', hi: 'आपकी खोजें यहाँ दिखाई देंगी' },
  qco_watch_title: { en: 'Mandatory certification watch', hi: 'अनिवार्य प्रमाणन सूची' },
  ext_resources: { en: 'External resources', hi: 'बाहरी संसाधन' },

  // -- results page --
  back: { en: '← Back', hi: '← वापस' },
  most_relevant: { en: 'Most relevant standards', hi: 'सबसे प्रासंगिक मानक' },
  related_allied: { en: 'Related & allied standards', hi: 'संबंधित एवं संबद्ध मानक' },
  no_match_title: { en: 'No matching Indian Standard found', hi: 'कोई मिलान भारतीय मानक नहीं मिला' },
  no_match_desc: { en: 'Try describing the product, material, or technical requirement in more detail.', hi: 'उत्पाद, सामग्री, या तकनीकी आवश्यकता का अधिक विस्तार से वर्णन करें।' },
  edition_disclosure_pre: { en: 'Edition as recorded in registry snapshot. Verify current edition at ', hi: 'संस्करण रजिस्ट्री स्नैपशॉट में दर्ज अनुसार है। निविदा दस्तावेज़ों में उपयोग से पहले ' },
  edition_disclosure_post: { en: ' before use in tender documents.', hi: ' पर वर्तमान संस्करण सत्यापित करें।' },

  // -- standard card --
  match_high: { en: 'High semantic match', hi: 'उच्च सिमैंटिक मिलान' },
  match_medium: { en: 'Moderate semantic match', hi: 'मध्यम सिमैंटिक मिलान' },
  match_related: { en: 'Related parameter match', hi: 'संबंधित पैरामीटर मिलान' },
  official_english: { en: 'Official English', hi: 'आधिकारिक अंग्रेज़ी' },
  lang_toggle_title: { en: 'Toggle between localized regional text and official English', hi: 'क्षेत्रीय भाषा एवं आधिकारिक अंग्रेज़ी के बीच स्विच करें' },
  badge_in_registry: { en: 'In registry', hi: 'रजिस्ट्री में मौजूद' },
  badge_in_registry_title: { en: 'Present in the registry snapshot.', hi: 'रजिस्ट्री स्नैपशॉट में मौजूद।' },
  edition_provenance_title: { en: 'Derived from editions present in the registry snapshot. Not a BIS currency determination — confirm at standardsbis.bsbedge.com.', hi: 'रजिस्ट्री स्नैपशॉट में मौजूद संस्करणों से लिया गया। यह BIS की आधिकारिक वैधता पुष्टि नहीं है — standardsbis.bsbedge.com पर सत्यापित करें।' },
  later_edition: { en: 'Later edition in registry', hi: 'रजिस्ट्री में नया संस्करण' },
  restructured_as: { en: 'Restructured as', hi: 'इस रूप में पुनर्गठित' },
  latest_in_registry: { en: 'Latest edition in registry', hi: 'रजिस्ट्री में नवीनतम संस्करण' },
  edition_not_recorded: { en: 'Edition not recorded', hi: 'संस्करण दर्ज नहीं' },
  amendment_not_recorded: { en: 'Amendment status not recorded', hi: 'संशोधन स्थिति दर्ज नहीं' },
  amendment_not_recorded_title: { en: 'The registry snapshot carries no verified amendment source. Check the BIS portal for gazetted amendments.', hi: 'रजिस्ट्री स्नैपशॉट में कोई सत्यापित संशोधन स्रोत नहीं है। राजपत्रित संशोधनों हेतु BIS पोर्टल देखें।' },
  superseded: { en: 'Superseded', hi: 'अधिक्रमित' },
  superseded_title: { en: 'Recorded as superseded in the registry snapshot', hi: 'रजिस्ट्री स्नैपशॉट में अधिक्रमित के रूप में दर्ज' },
  by_paren_pre: { en: '(by ', hi: '(द्वारा ' },
  by_paren_post: { en: ')', hi: ')' },
  card_historical_label: { en: 'Historical / superseded standard:', hi: 'ऐतिहासिक / अधिक्रमित मानक:' },
  card_historical_text: { en: 'superseded by {{by}}. Public tenders should cite the latest active version.', hi: '{{by}} द्वारा अधिक्रमित। सार्वजनिक निविदाओं में नवीनतम सक्रिय संस्करण का हवाला दें।' },
  card_historical_fallback: { en: 'an updated standard', hi: 'एक अद्यतन मानक' },
  schedule_verified: { en: 'CPWD / GeM schedule verified:', hi: 'CPWD / GeM अनुसूची सत्यापित:' },
  schedule_fallback: { en: 'Matches public procurement specification', hi: 'सार्वजनिक खरीद विनिर्देश से मेल खाता है' },
  schedule_fallback_modal: { en: 'Government procurement schedule match', hi: 'सरकारी खरीद अनुसूची मिलान' },
  grade_label: { en: 'Grade: {{grade}}', hi: 'ग्रेड: {{grade}}' },
  qco_hallmark_label: { en: 'Mandatory BIS Hallmarking (Scheme-IV, 6-digit HUID):', hi: 'अनिवार्य BIS हॉलमार्किंग (स्कीम-IV, 6-अंकीय HUID):' },
  qco_crs_label: { en: 'Mandatory Compulsory Registration Scheme (Scheme-II CRS):', hi: 'अनिवार्य कम्पल्सरी रजिस्ट्रेशन स्कीम (स्कीम-II CRS):' },
  qco_isi_label: { en: 'Mandatory BIS product certification (Scheme-I ISI Mark):', hi: 'अनिवार्य BIS उत्पाद प्रमाणन (स्कीम-I ISI मार्क):' },
  qco_hallmark_label_modal: { en: 'Mandatory BIS Hallmarking (Scheme-IV, 6-digit HUID)', hi: 'अनिवार्य BIS हॉलमार्किंग (स्कीम-IV, 6-अंकीय HUID)' },
  qco_crs_label_modal: { en: 'Mandatory Compulsory Registration Scheme (Scheme-II CRS)', hi: 'अनिवार्य कम्पल्सरी रजिस्ट्रेशन स्कीम (स्कीम-II CRS)' },
  qco_isi_label_modal: { en: 'Mandatory BIS product certification (Scheme-I ISI Mark)', hi: 'अनिवार्य BIS उत्पाद प्रमाणन (स्कीम-I ISI मार्क)' },
  qco_compliance_fallback: { en: 'Mandatory certification under {{scheme}} per BIS Act, 2016.', hi: 'BIS अधिनियम, 2016 के अंतर्गत {{scheme}} के तहत अनिवार्य प्रमाणन।' },
  qco_compliance_fallback_modal: { en: 'This standard is notified under a mandatory Quality Control Order (QCO) issued under Section 16 of the BIS Act, 2016. Supply of uncertified goods is prohibited by law.', hi: 'यह मानक BIS अधिनियम, 2016 की धारा 16 के तहत जारी अनिवार्य गुणवत्ता नियंत्रण आदेश (QCO) के अंतर्गत अधिसूचित है। असत्यापित वस्तुओं की आपूर्ति कानूनन प्रतिबंधित है।' },
  voluntary_label: { en: 'Voluntary BIS conformance:', hi: 'स्वैच्छिक BIS अनुरूपता:' },
  voluntary_text: { en: 'No mandatory QCO notified. Quality compliance verifiable via manufacturer test certificates (GFR 2017 Rule 144).', hi: 'कोई अनिवार्य QCO अधिसूचित नहीं। गुणवत्ता अनुरूपता निर्माता परीक्षण प्रमाणपत्रों (GFR 2017 नियम 144) से सत्यापित की जा सकती है।' },
  semantic_heading: { en: 'Semantic understanding & scope match', hi: 'अर्थबोध एवं कार्यक्षेत्र सुसंगतता' },
  allied_test: { en: 'Test methods', hi: 'परीक्षण विधियाँ' },
  allied_safety: { en: 'Safety norms', hi: 'सुरक्षा मानदंड' },
  allied_install: { en: 'Installation', hi: 'स्थापना' },
  allied_terms: { en: 'Terminology', hi: 'शब्दावली' },
  allied_related: { en: 'Related standards', hi: 'संबंधित मानक' },
  allied_self_contained: { en: 'Self-contained specification — no separate normative references required', hi: 'स्वतः-पूर्ण विनिर्देश — अलग संदर्भ मानकों की आवश्यकता नहीं' },
  more_count: { en: '+{{n}} more', hi: '+{{n}} और' },
  copy_code: { en: 'Copy code', hi: 'कोड कॉपी करें' },
  view_details: { en: 'View details', hi: 'विवरण देखें' },
  gem_clause_btn: { en: 'GeM clause', hi: 'GeM क्लॉज़' },
  copy_code_title: { en: 'Copy standard code to clipboard', hi: 'मानक कोड क्लिपबोर्ड पर कॉपी करें' },
  view_details_title: { en: 'View full standard scope, amendments, and allied standards tree', hi: 'पूर्ण मानक कार्यक्षेत्र, संशोधन एवं संबद्ध मानक ट्री देखें' },
  gem_clause_title: { en: 'Generate ready-to-paste GeM specification clause', hi: 'तैयार GeM विनिर्देश क्लॉज़ बनाएं' },

  // -- standard details modal --
  tab_overview: { en: 'Overview & edition', hi: 'अवलोकन एवं संस्करण' },
  tab_rationale: { en: 'Semantic scope match', hi: 'सिमैंटिक कार्यक्षेत्र मिलान' },
  tab_qco: { en: 'Mandatory certification', hi: 'अनिवार्य प्रमाणन' },
  tab_allied: { en: 'Allied standards ({{n}})', hi: 'संबद्ध मानक ({{n}})' },
  close_details: { en: 'Close standard details', hi: 'मानक विवरण बंद करें' },
  active_status: { en: 'ACTIVE', hi: 'सक्रिय' },
  reaffirmed_paren: { en: '(reaffirmed {{year}})', hi: '(पुनः पुष्टि {{year}})' },
  superseded_status: { en: 'SUPERSEDED', hi: 'अधिक्रमित' },
  advisory_label: { en: 'Advisory:', hi: 'सूचना:' },
  advisory_superseded_by: { en: 'It has been formally superseded by {{by}}. Public procurement tenders must cite the updated standard.', hi: 'इसे औपचारिक रूप से {{by}} द्वारा अधिक्रमित किया गया है। सार्वजनिक खरीद निविदाओं में अद्यतन मानक का हवाला देना अनिवार्य है।' },
  advisory_verify: { en: 'this is a historical or superseded standard in the national archive.', hi: 'यह राष्ट्रीय संग्रह में एक ऐतिहासिक या अधिक्रमित मानक है।' },
  advisory_no_successor: { en: 'Please verify whether an updated revision or amendment has been gazetted.', hi: 'कृपया सत्यापित करें कि कोई अद्यतन संशोधन राजपत्रित हुआ है या नहीं।' },
  division_label: { en: 'Division: {{cat}}', hi: 'विभाग: {{cat}}' },
  published_edition: { en: 'Published edition:', hi: 'प्रकाशित संस्करण:' },
  reaffirmed_year: { en: 'Reaffirmed year: {{year}}', hi: 'पुनः पुष्टि वर्ष: {{year}}' },
  scope_heading: { en: 'Standard scope & technical coverage', hi: 'मानक कार्यक्षेत्र एवं तकनीकी कवरेज' },
  scope_fallback: { en: 'Covers materials, physical requirements, manufacturing methods, testing procedures, sampling guidelines and compliance criteria under Bureau of Indian Standards.', hi: 'भारतीय मानक ब्यूरो के अंतर्गत सामग्री, भौतिक आवश्यकताएँ, निर्माण विधियाँ, परीक्षण प्रक्रियाएँ, नमूनाकरण दिशानिर्देश एवं अनुरूपता मानदंड शामिल हैं।' },
  rationale_heading: { en: 'Semantic neural match rationale', hi: 'सिमैंटिक न्यूरल मिलान का आधार' },
  gfr_heading: { en: 'GFR 2017, Rule 144 conformance', hi: 'GFR 2017, नियम 144 अनुरूपता' },
  gfr_text_pre: { en: 'Under Rule 144 of the General Financial Rules (2017), government entities must base technical specifications on national standards (BIS). Citing ', hi: 'सामान्य वित्तीय नियम (2017) के नियम 144 के तहत, सरकारी संस्थाओं को तकनीकी विनिर्देश राष्ट्रीय मानकों (BIS) पर आधारित करने होंगे। ' },
  gfr_text_post: { en: ' ensures non-restrictive competitive bidding while legally securing certified quality.', hi: ' का हवाला देने से गैर-प्रतिबंधात्मक प्रतिस्पर्धी बोली सुनिश्चित होती है और प्रमाणित गुणवत्ता कानूनी रूप से सुरक्षित रहती है।' },
  scheme_label: { en: 'Scheme:', hi: 'योजना:' },
  ministry_label: { en: 'Ministry:', hi: 'मंत्रालय:' },
  order_label: { en: 'Order:', hi: 'आदेश:' },
  voluntary_modal_heading: { en: 'Voluntary BIS conformance (GFR 2017, Rule 144)', hi: 'स्वैच्छिक BIS अनुरूपता (GFR 2017, नियम 144)' },
  voluntary_modal_text: { en: 'No mandatory Quality Control Order (QCO) is currently enforced for this specific standard. Conformity may still be required in tender specifications to guarantee standardised engineering performance.', hi: 'इस विशिष्ट मानक के लिए वर्तमान में कोई अनिवार्य गुणवत्ता नियंत्रण आदेश (QCO) लागू नहीं है। मानकीकृत इंजीनियरिंग प्रदर्शन सुनिश्चित करने हेतु निविदा विनिर्देशों में अनुरूपता फिर भी आवश्यक हो सकती है।' },
  allied_heading: { en: 'Allied & normative reference standards ({{n}})', hi: 'संबद्ध एवं मानक संदर्भ मानक ({{n}})' },
  allied_none: { en: 'This is a self-contained standard specification without separate normative references.', hi: 'यह एक स्वतः-पूर्ण मानक विनिर्देश है जिसमें अलग संदर्भ मानकों की आवश्यकता नहीं है।' },
  allied_test_full: { en: 'Normative test methods & sampling procedures', hi: 'मानक परीक्षण विधियाँ एवं नमूनाकरण प्रक्रियाएँ' },
  allied_safety_full: { en: 'Safety & protection standards', hi: 'सुरक्षा एवं संरक्षण मानक' },
  allied_install_full: { en: 'Installation & workmanship standards', hi: 'स्थापना एवं कारीगरी मानक' },
  allied_terms_full: { en: 'Terminology & nomenclature standards', hi: 'शब्दावली एवं नामकरण मानक' },
  allied_related_full: { en: 'Related product & raw material standards', hi: 'संबंधित उत्पाद एवं कच्चे माल के मानक' },
  tag_test: { en: 'Test method', hi: 'परीक्षण विधि' },
  tag_safety: { en: 'Safety standard', hi: 'सुरक्षा मानक' },
  tag_install: { en: 'Installation', hi: 'स्थापना' },
  tag_terms: { en: 'Terminology', hi: 'शब्दावली' },
  tag_related: { en: 'Related product', hi: 'संबंधित उत्पाद' },
  is_spec_fallback: { en: 'Indian Standard specification', hi: 'भारतीय मानक विनिर्देश' },
  copy_is_code: { en: 'Copy IS code', hi: 'IS कोड कॉपी करें' },
  draft_gem_clause: { en: 'Draft GeM clause', hi: 'GeM क्लॉज़ तैयार करें' },

  // -- GeM clause modal --
  gem_title_prefix: { en: 'GeM technical specification clause: ', hi: 'GeM तकनीकी विनिर्देश क्लॉज़: ' },
  close_modal: { en: 'Close modal', hi: 'मोडल बंद करें' },
  gem_drafting: { en: 'Drafting official GeM & GFR 2017 compliant specification clause for {{code}}…', hi: '{{code}} के लिए आधिकारिक GeM एवं GFR 2017 अनुरूप विनिर्देश क्लॉज़ तैयार किया जा रहा है…' },
  gem_guidance_label: { en: 'Procurement guidance (GFR 2017, Rule 144):', hi: 'खरीद मार्गदर्शन (GFR 2017, नियम 144):' },
  gem_guidance_text: { en: 'this clause specifies standard compliance without proprietary vendor lock-in. Paste directly into your GeM Custom Bid Additional Terms & Conditions (ATC) or Tender Specification Schedule.', hi: 'यह क्लॉज़ बिना किसी वेंडर-विशिष्ट लॉक-इन के मानक अनुरूपता निर्दिष्ट करता है। इसे सीधे अपने GeM कस्टम बिड अतिरिक्त नियम एवं शर्तें (ATC) या निविदा विनिर्देश अनुसूची में जोड़ें।' },
  gem_compliance_footer: { en: 'Compliance: Bureau of Indian Standards Act, 2016 & GeM Procurement Manual', hi: 'अनुपालन: भारतीय मानक ब्यूरो अधिनियम, 2016 एवं GeM खरीद मैनुअल' },
  download_txt: { en: 'Download (.txt)', hi: 'डाउनलोड (.txt)' },
  copy_clause_gem: { en: 'Copy clause for GeM', hi: 'GeM हेतु क्लॉज़ कॉपी करें' },
  copied_clipboard: { en: 'Copied to clipboard', hi: 'क्लिपबोर्ड पर कॉपी हुआ' },

  // -- tender auditor --
  tender_banner_title: { en: 'Tender document & Bill of Quantities (BoQ) auditor', hi: 'निविदा दस्तावेज़ एवं मात्रा विवरण (BoQ) ऑडिटर' },
  tender_banner_desc: { en: 'Upload your Notice Inviting Tender (NIT) PDF, technical specifications document, or Schedule of Quantities (CSV) from CPWD/MES/GeM/CPPP. The engine isolates the scope of work, audits technical line items against BIS standards, and flags mandatory ISI/CRS certification rules under the BIS Act, 2016.', hi: 'CPWD/MES/GeM/CPPP से अपनी निविदा सूचना (NIT) PDF, तकनीकी विनिर्देश दस्तावेज़, या मात्रा अनुसूची (CSV) अपलोड करें। यह इंजन कार्यक्षेत्र को अलग करता है, तकनीकी लाइन-आइटम को BIS मानकों के विरुद्ध ऑडिट करता है, एवं BIS अधिनियम, 2016 के तहत अनिवार्य ISI/CRS प्रमाणन नियमों को चिह्नित करता है।' },
  dropzone_title: { en: 'Upload draft tender PDF or BoQ schedule (CSV)', hi: 'निविदा PDF या BoQ अनुसूची (CSV) अपलोड करें' },
  dropzone_sub: { en: 'Drag & drop a tender document here, or click to browse — supports .pdf NIT notices, technical specs, and .csv BoQs', hi: 'निविदा दस्तावेज़ यहाँ खींचकर छोड़ें, या ब्राउज़ करने हेतु क्लिक करें — .pdf NIT सूचनाएँ, तकनीकी विनिर्देश, एवं .csv BoQ समर्थित हैं' },
  audit_loading_title: { en: 'Reading selected BIS sources and auditing {{file}} against QCO mandates…', hi: 'चयनित BIS स्रोत पढ़े जा रहे हैं एवं {{file}} को QCO अनिवार्यताओं के विरुद्ध ऑडिट किया जा रहा है…' },
  audit_loading_sub: { en: 'Parsing engineering clauses, decomposing work scope & matching authentic IS codes', hi: 'इंजीनियरिंग क्लॉज़ पार्स किए जा रहे हैं, कार्यक्षेत्र विश्लेषित किया जा रहा है एवं प्रामाणिक IS कोड मिलाए जा रहे हैं' },
  audit_results_title: { en: 'Audit results: {{file}}', hi: 'ऑडिट परिणाम: {{file}}' },
  audit_meta: { en: 'Document format: {{fmt}} · Line items assessed: {{n}}', hi: 'दस्तावेज़ प्रारूप: {{fmt}} · मूल्यांकित लाइन-आइटम: {{n}}' },
  audit_meta_of_parsed: { en: ' of {{total}} parsed', hi: ' में से {{total}} पार्स किए गए' },
  generating: { en: 'Generating…', hi: 'तैयार किया जा रहा है…' },
  export_pdf: { en: 'Export audit report (PDF)', hi: 'ऑडिट रिपोर्ट निर्यात करें (PDF)' },
  export_csv: { en: 'Export audited schedule (.csv)', hi: 'ऑडिट अनुसूची निर्यात करें (.csv)' },
  notice_label: { en: 'Notice:', hi: 'सूचना:' },
  audit_state_compliant: { en: 'Compliant', hi: 'अनुरूप' },
  audit_state_compliant_hint: { en: 'Matched at HIGH confidence, no unmet certification', hi: 'उच्च विश्वास स्तर पर मिलान, कोई अपूर्ण प्रमाणन नहीं' },
  audit_state_qco: { en: 'QCO required', hi: 'QCO आवश्यक' },
  audit_state_qco_hint: { en: 'Mandatory ISI / CRS / Hallmark not referenced', hi: 'अनिवार्य ISI / CRS / हॉलमार्क संदर्भित नहीं' },
  audit_state_suggested: { en: 'Standard suggested', hi: 'मानक सुझाया गया' },
  audit_state_suggested_hint: { en: 'No IS code in the item text; one matched at HIGH', hi: 'आइटम टेक्स्ट में कोई IS कोड नहीं; उच्च विश्वास स्तर पर एक मिला' },
  audit_state_none: { en: 'Not assessed', hi: 'मूल्यांकित नहीं' },
  audit_state_none_hint: { en: 'Confidence below HIGH, or no match found', hi: 'विश्वास स्तर उच्च से कम, या कोई मिलान नहीं मिला' },
  audit_cap_notice: { en: 'Showing first {{n}} of {{m}} parsed line items. Each item runs a full hybrid search, so the audit is capped at {{cap}} per upload.', hi: '{{m}} पार्स किए गए लाइन-आइटम में से पहले {{n}} दिखाए जा रहे हैं। प्रत्येक आइटम पूर्ण हाइब्रिड खोज चलाता है, इसलिए प्रति अपलोड ऑडिट {{cap}} तक सीमित है।' },
  tbl_item_spec: { en: 'Tender item / specification clause', hi: 'निविदा आइटम / विनिर्देश क्लॉज़' },
  tbl_status: { en: 'Status', hi: 'स्थिति' },
  tbl_quantity: { en: 'Quantity', hi: 'मात्रा' },
  tbl_recommended: { en: 'Recommended Indian Standards', hi: 'अनुशंसित भारतीय मानक' },
  tbl_actions: { en: 'Actions', hi: 'कार्रवाई' },
  no_items_found: { en: 'No technical line items identified in this document.', hi: 'इस दस्तावेज़ में कोई तकनीकी लाइन-आइटम नहीं मिला।' },
  clause_fallback: { en: 'Clause', hi: 'क्लॉज़' },
  row_gem: { en: 'GeM', hi: 'GeM' },
  row_details: { en: 'Details', hi: 'विवरण' },
  audit_fine_title: { en: 'No unmet certification obligations', hi: 'कोई अपूर्ण प्रमाणन दायित्व नहीं' },
  audit_fine_text: { en: 'No assessed line item carries a mandatory ISI, CRS or Hallmark requirement that the tender text fails to reference. Per-item status for every row is in the table above — items marked Not assessed were not checked and still need manual review.', hi: 'किसी भी मूल्यांकित लाइन-आइटम में ऐसी अनिवार्य ISI, CRS या हॉलमार्क आवश्यकता नहीं है जिसका निविदा पाठ में संदर्भ न हो। प्रत्येक पंक्ति की स्थिति ऊपर तालिका में है — "मूल्यांकित नहीं" चिह्नित आइटम की जाँच नहीं हुई है एवं उन्हें मैन्युअल समीक्षा की आवश्यकता है।' },
  audit_warning_title: { en: 'Audit findings: missing Indian Standards & hallmarks', hi: 'ऑडिट निष्कर्ष: अनुपस्थित भारतीय मानक एवं हॉलमार्क' },
  audit_warning_meta: { en: 'Statutory compliance under BIS Act 2016 & line ministry QCOs', hi: 'BIS अधिनियम 2016 एवं संबंधित मंत्रालय के QCO के अंतर्गत सांविधिक अनुपालन' },
  missing_is_title: { en: 'Missing Indian Standards (IS codes) in tender clauses:', hi: 'निविदा क्लॉज़ में अनुपस्थित भारतीय मानक (IS कोड):' },
  missing_item_num: { en: 'Item #{{n}}:', hi: 'आइटम #{{n}}:' },
  missing_is_badge: { en: 'Missing IS code: {{code}}', hi: 'अनुपस्थित IS कोड: {{code}}' },
  missing_mark_title: { en: 'Missing mandatory hallmarks & quality certifications:', hi: 'अनुपस्थित अनिवार्य हॉलमार्क एवं गुणवत्ता प्रमाणन:' },
  missing_mark_badge: { en: 'Missing hallmark / mark: {{mark}}', hi: 'अनुपस्थित हॉलमार्क / मार्क: {{mark}}' },
  mark_hallmark_fallback: { en: 'Mandatory BIS Hallmark with 6-digit HUID (Scheme-IV)', hi: '6-अंकीय HUID सहित अनिवार्य BIS हॉलमार्क (स्कीम-IV)' },
  mark_isi_fallback: { en: 'Mandatory BIS ISI Mark (Scheme-I under QCO)', hi: 'अनिवार्य BIS ISI मार्क (QCO के अंतर्गत स्कीम-I)' },
  mark_crs_fallback: { en: 'Mandatory BIS CRS Registration (Scheme-II)', hi: 'अनिवार्य BIS CRS पंजीकरण (स्कीम-II)' },

  // -- benchmark sandbox --
  bench_banner_title: { en: 'Information retrieval & evaluation benchmark', hi: 'सूचना पुनर्प्राप्ति एवं मूल्यांकन बेंचमार्क' },
  bench_banner_desc: { en: 'Evaluates the offline hybrid retrieval pipeline (BM25 lexical search + BGE-M3 1024-d dense vector index + cross-encoder reranking) against curated government procurement benchmark queries.', hi: 'यह चयनित सरकारी खरीद बेंचमार्क प्रश्नों के विरुद्ध ऑफ़लाइन हाइब्रिड पुनर्प्राप्ति पाइपलाइन (BM25 लेक्सिकल खोज + BGE-M3 1024-आयामी डेंस वेक्टर इंडेक्स + क्रॉस-एन्कोडर रीरैंकिंग) का मूल्यांकन करता है।' },
  bench_running: { en: 'Running benchmark ({{n}} queries)…', hi: 'बेंचमार्क चल रहा है ({{n}} प्रश्न)…' },
  bench_execute: { en: 'Execute evaluation suite', hi: 'मूल्यांकन सूट चलाएँ' },
  bench_download: { en: 'Download team_results.json', hi: 'team_results.json डाउनलोड करें' },
  bench_hit_rate: { en: 'Hit rate @ 3', hi: 'हिट रेट @ 3' },
  bench_target_80: { en: 'Target: >80.0%', hi: 'लक्ष्य: >80.0%' },
  bench_mrr: { en: 'MRR @ 5', hi: 'MRR @ 5' },
  bench_mrr_sub: { en: 'Mean reciprocal rank', hi: 'औसत व्युत्क्रम रैंक' },
  bench_avg_latency: { en: 'Avg search latency', hi: 'औसत खोज विलंब' },
  bench_latency_target: { en: 'Hardware-adaptive target: <5s', hi: 'हार्डवेयर-अनुकूली लक्ष्य: <5 सेकंड' },
  bench_standby: { en: '> Standby. Click "Execute Evaluation Suite" to run public test queries…', hi: '> स्टैंडबाय। सार्वजनिक परीक्षण प्रश्न चलाने हेतु "मूल्यांकन सूट चलाएँ" पर क्लिक करें…' },

  // -- loading steps --
  load_step1: { en: 'Extracting technical concepts & specifications', hi: 'तकनीकी अवधारणाएँ एवं विनिर्देश निकाले जा रहे हैं' },
  load_step2: { en: 'Searching 33,553+ authentic Indian Standards catalog', hi: '33,553+ प्रामाणिक भारतीय मानक सूची में खोजा जा रहा है' },
  load_step3: { en: 'Applying hardware-adaptive cross-encoder reranking', hi: 'हार्डवेयर-अनुकूली क्रॉस-एन्कोडर रीरैंकिंग लागू की जा रही है' },
  load_step4: { en: 'Auditing mandatory Quality Control Orders (QCOs)', hi: 'अनिवार्य गुणवत्ता नियंत्रण आदेश (QCO) ऑडिट किए जा रहे हैं' },
  load_step5: { en: 'Checking allied testing & safety standards', hi: 'संबद्ध परीक्षण एवं सुरक्षा मानक जाँचे जा रहे हैं' },
  loading_title: { en: 'Reading selected BIS sources and preparing an evidence-backed analysis', hi: 'चयनित BIS स्रोत पढ़े जा रहे हैं एवं साक्ष्य-आधारित विश्लेषण तैयार किया जा रहा है' },
  loading_subtitle: { en: 'Analyzing "{{query}}" against national standards…', hi: '"{{query}}" का राष्ट्रीय मानकों के विरुद्ध विश्लेषण किया जा रहा है…' },
};

export function translate(lang, key, vars) {
  const entry = STRINGS[key];
  let str = (entry && (entry[lang] || entry.en)) || key;
  if (vars) {
    Object.keys(vars).forEach((k) => {
      str = str.replace(new RegExp(`\\{\\{${k}\\}\\}`, 'g'), vars[k]);
    });
  }
  return str;
}

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try { return localStorage.getItem('is_display_language') || 'en'; }
    catch { return 'en'; }
  });

  const setLang = useCallback((l) => {
    setLangState(l);
    try { localStorage.setItem('is_display_language', l); } catch {}
  }, []);

  const t = useCallback((key, vars) => translate(lang, key, vars), [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within a LanguageProvider');
  return ctx;
}
