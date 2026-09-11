import React, { useState, useEffect } from 'react';
import { Search, FileSpreadsheet, Award } from 'lucide-react';
import Header from './components/Header';
import SpecSearch from './components/SpecSearch';
import TenderAuditor from './components/TenderAuditor';
import BenchmarkSandbox from './components/BenchmarkSandbox';
import GeMClauseModal from './components/GeMClauseModal';
import StandardDetailsModal from './components/StandardDetailsModal';
import { checkHealth, searchStandards, generateGeMClause, getStandardDetails } from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [isOnline, setIsOnline] = useState(false);
  const [engineLatency, setEngineLatency] = useState(null);

  // Search State
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);

  // GeM Modal State
  const [isGeMModalOpen, setIsGeMModalOpen] = useState(false);
  const [selectedISCode, setSelectedISCode] = useState('');
  const [clauseData, setClauseData] = useState(null);
  const [isClauseLoading, setIsClauseLoading] = useState(false);
  const [clauseError, setClauseError] = useState(null);

  // Standard Details Modal State (Requirement 7 & 8)
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [detailedStandard, setDetailedStandard] = useState(null);

  // Health Poll
  useEffect(() => {
    let isMounted = true;
    const pollHealth = async () => {
      const data = await checkHealth();
      if (isMounted) {
        setIsOnline(data.status === 'healthy');
      }
    };
    pollHealth();
    const interval = setInterval(pollHealth, 6000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleSearch = async (query) => {
    setIsSearching(true);
    setSearchError(null);
    try {
      const data = await searchStandards(query, 6);
      setSearchResults(data);
      setEngineLatency(data.latency_seconds);
    } catch (err) {
      setSearchError(err.message || 'Search execution failed');
      setSearchResults(null);
    } finally {
      setIsSearching(false);
    }
  };

  const handleOpenGeMClause = async (isCode) => {
    setSelectedISCode(isCode);
    setIsGeMModalOpen(true);
    setIsClauseLoading(true);
    setClauseError(null);
    setClauseData(null);
    try {
      const data = await generateGeMClause(isCode);
      setClauseData(data);
    } catch (err) {
      setClauseError(err.message || `Failed to draft specification clause for ${isCode}`);
    } finally {
      setIsClauseLoading(false);
    }
  };

  const handleViewDetails = async (standard) => {
    // Open immediately with existing hit data
    setDetailedStandard(standard);
    setIsDetailsOpen(true);

    // Optionally augment with full SQLite details if available
    try {
      const fullDetails = await getStandardDetails(standard.is_code);
      if (fullDetails) {
        setDetailedStandard((prev) => ({
          ...prev,
          ...fullDetails,
          // Preserve runtime rationale and confidence
          rationale: prev?.rationale || fullDetails.scope,
          confidence: prev?.confidence || 'HIGH',
        }));
      }
    } catch {
      // Fallback seamlessly to existing hit data
    }
  };

  return (
    <div className="app-container">
      <Header isOnline={isOnline} latency={engineLatency} />

      {/* Navigation Tabs */}
      <nav className="nav-bar" role="navigation" aria-label="Main Navigation">
        <div className="nav-inner">
          <button
            className={`nav-tab-btn ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            <Search size={15} />
            <span>Find Standards</span>
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'tender' ? 'active' : ''}`}
            onClick={() => setActiveTab('tender')}
          >
            <FileSpreadsheet size={15} />
            <span>Tender & BoQ Auditor</span>
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
            onClick={() => setActiveTab('benchmark')}
          >
            <Award size={15} />
            <span>Evaluation Sandbox</span>
          </button>
        </div>
      </nav>

      {/* Main Workspace */}
      <main className="main-wrapper">
        {activeTab === 'search' && (
          <SpecSearch
            onOpenGeMClause={handleOpenGeMClause}
            onViewDetails={handleViewDetails}
            onSearch={handleSearch}
            searchResults={searchResults}
            isSearching={isSearching}
            searchError={searchError}
            onSwitchToTender={() => setActiveTab('tender')}
          />
        )}

        {activeTab === 'tender' && (
          <TenderAuditor
            onOpenGeMClause={handleOpenGeMClause}
            onViewDetails={handleViewDetails}
          />
        )}

        {activeTab === 'benchmark' && (
          <BenchmarkSandbox />
        )}
      </main>

      {/* Standard Details Modal (Requirement 7 & 8) */}
      <StandardDetailsModal
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        standard={detailedStandard}
        onOpenGeMClause={handleOpenGeMClause}
      />

      {/* GeM Tender Specification Clause Modal */}
      <GeMClauseModal
        isOpen={isGeMModalOpen}
        onClose={() => setIsGeMModalOpen(false)}
        isCode={selectedISCode}
        clauseData={clauseData}
        isLoading={isClauseLoading}
        error={clauseError}
      />
    </div>
  );
}
