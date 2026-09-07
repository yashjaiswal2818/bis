import React, { useState, useEffect } from 'react';
import { Search, FileSpreadsheet, Award } from 'lucide-react';
import Header from './components/Header';
import SpecSearch from './components/SpecSearch';
import TenderAuditor from './components/TenderAuditor';
import BenchmarkSandbox from './components/BenchmarkSandbox';
import GeMClauseModal from './components/GeMClauseModal';
import { checkHealth, searchStandards, generateGeMClause } from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [isOnline, setIsOnline] = useState(false);
  const [engineLatency, setEngineLatency] = useState(null);

  // Search State
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);

  // GeM Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedISCode, setSelectedISCode] = useState('');
  const [clauseData, setClauseData] = useState(null);
  const [isClauseLoading, setIsClauseLoading] = useState(false);
  const [clauseError, setClauseError] = useState(null);

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
      const data = await searchStandards(query, 5);
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
    setIsModalOpen(true);
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

  return (
    <div className="app-container">
      <Header isOnline={isOnline} latency={engineLatency} />

      {/* Navigation Tabs */}
      <nav className="nav-bar">
        <div className="nav-inner">
          <button
            className={`nav-tab-btn ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            <Search size={15} />
            <span>Tender Specification Search</span>
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'tender' ? 'active' : ''}`}
            onClick={() => setActiveTab('tender')}
          >
            <FileSpreadsheet size={15} />
            <span>Tender Document & BoQ Auditor</span>
          </button>
          <button
            className={`nav-tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
            onClick={() => setActiveTab('benchmark')}
          >
            <Award size={15} />
            <span>Model Evaluation Sandbox</span>
          </button>
        </div>
      </nav>

      {/* Main Workspace */}
      <main className="main-wrapper">
        {activeTab === 'search' && (
          <SpecSearch
            onOpenGeMClause={handleOpenGeMClause}
            onSearch={handleSearch}
            searchResults={searchResults}
            isSearching={isSearching}
            searchError={searchError}
          />
        )}

        {activeTab === 'tender' && (
          <TenderAuditor onOpenGeMClause={handleOpenGeMClause} />
        )}

        {activeTab === 'benchmark' && (
          <BenchmarkSandbox />
        )}
      </main>

      {/* GeM Tender Specification Clause Modal */}
      <GeMClauseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        isCode={selectedISCode}
        clauseData={clauseData}
        isLoading={isClauseLoading}
        error={clauseError}
      />
    </div>
  );
}
