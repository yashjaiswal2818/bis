-- =========================================================================
-- Indian Standards Recommendation Engine: Master Database Schema
-- Embedded SQLite database for standards catalog, QCOs, and allied graph
-- =========================================================================

-- 1. Master Standards Registry Table
CREATE TABLE IF NOT EXISTS standards_registry (
    is_code TEXT PRIMARY KEY,               -- e.g. "IS 269: 1989" or "IS 269: 2015"
    is_code_norm TEXT NOT NULL UNIQUE,     -- e.g. "is269:1989" (normalized for fast matching)
    title TEXT NOT NULL,                   -- e.g. "ORDINARY PORTLAND CEMENT"
    revision TEXT,                         -- e.g. "Fifth Revision"
    scope TEXT,                            -- Extracted standard scope
    full_text TEXT,                        -- Full body text of the standard
    division TEXT DEFAULT 'Civil Engineering (CED)', -- BIS Division
    status TEXT DEFAULT 'ACTIVE',          -- 'ACTIVE', 'SUPERSEDED', 'WITHDRAWN'
    superseded_by TEXT,                    -- e.g. "IS 269: 2015" (if an older version)
    reaffirmation_year INTEGER,            -- e.g. 2021
    amendments_count INTEGER DEFAULT 0,    -- Number of published amendments
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_standards_norm ON standards_registry(is_code_norm);
CREATE INDEX IF NOT EXISTS idx_standards_status ON standards_registry(status);

-- 2. Mandatory Certification & Quality Control Orders (QCO) Table
CREATE TABLE IF NOT EXISTS qco_compliance_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    is_code TEXT NOT NULL,                 -- Target standard (e.g. "IS 269: 1989")
    product_category TEXT NOT NULL,        -- e.g. "Cement & Cementitious Products"
    scheme_type TEXT NOT NULL,             -- 'Scheme-I (Mandatory ISI Mark)', 'Scheme-II (CRS)', 'Scheme-IV (Hallmarking)'
    is_mandatory BOOLEAN DEFAULT 1,        -- 1 = Mandatory by Law under BIS Act 2016
    issuing_ministry TEXT NOT NULL,        -- e.g. "DPIIT", "Ministry of Steel", "MeitY"
    order_name TEXT NOT NULL,              -- e.g. "Cement (Quality Control) Order, 2023"
    effective_date TEXT,                   -- Notification / Effective Date
    compliance_warning TEXT NOT NULL,      -- Warning message inserted into tender review
    FOREIGN KEY (is_code) REFERENCES standards_registry(is_code)
);

CREATE INDEX IF NOT EXISTS idx_qco_is_code ON qco_compliance_rules(is_code);
CREATE INDEX IF NOT EXISTS idx_qco_mandatory ON qco_compliance_rules(is_mandatory);

-- 3. Allied & Normative Standards Knowledge Graph Table
CREATE TABLE IF NOT EXISTS allied_standards_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_is_code TEXT NOT NULL,          -- e.g. "IS 456: 2000" (Core Concrete Standard)
    target_is_code TEXT NOT NULL,          -- e.g. "IS 516: 1959" (Compressive test)
    relation_type TEXT NOT NULL,           -- 'NORM_TEST', 'RAW_MATERIAL', 'SAFETY', 'INSTALLATION', 'TERMINOLOGY'
    relation_label TEXT NOT NULL,          -- Human readable description
    is_normative BOOLEAN DEFAULT 1,        -- 1 = Normative (must comply), 0 = Informative
    FOREIGN KEY (source_is_code) REFERENCES standards_registry(is_code)
);

CREATE INDEX IF NOT EXISTS idx_allied_source ON allied_standards_edges(source_is_code);
CREATE INDEX IF NOT EXISTS idx_allied_type ON allied_standards_edges(relation_type);
