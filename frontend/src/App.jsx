import React, { useState, useEffect } from 'react';
import { Search, FileSpreadsheet, Award } from 'lucide-react';
import Header from './components/Header';
import Footer from './components/Footer';
import SpecSearch from './components/SpecSearch';
import TenderAuditor from './components/TenderAuditor';
import BenchmarkSandbox from './components/BenchmarkSandbox';
import GeMClauseModal from './components/GeMClauseModal';
import StandardDetailsModal from './components/StandardDetailsModal';
import { checkHealth, searchStandards, generateGeMClause, getStandardDetails } from './api/client';
import { LanguageProvider } from './i18n';

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

  // Standard Details Modal State
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
    // null/empty query = clear results and return to landing
    if (!query) {
      setSearchResults(null);
      setSearchError(null);
      return;
    }
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
    setDetailedStandard(standard);
    setIsDetailsOpen(true);
    try {
      const fullDetails = await getStandardDetails(standard.is_code);
      if (fullDetails) {
        setDetailedStandard((prev) => ({
          ...prev,
          ...fullDetails,
          rationale: prev?.rationale || fullDetails.scope,
          confidence: prev?.confidence || 'HIGH',
        }));
      }
    } catch {
      // Fallback seamlessly to existing hit data
    }
  };

  return (
    <LanguageProvider>
      <div className="app-container">
        <Header
          isOnline={isOnline}
          latency={engineLatency}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />

        <main className="main-wrapper" id="main-content">
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

        <StandardDetailsModal
          isOpen={isDetailsOpen}
          onClose={() => setIsDetailsOpen(false)}
          standard={detailedStandard}
          onOpenGeMClause={handleOpenGeMClause}
        />

        <GeMClauseModal
          isOpen={isGeMModalOpen}
          onClose={() => setIsGeMModalOpen(false)}
          isCode={selectedISCode}
          clauseData={clauseData}
          isLoading={isClauseLoading}
          error={clauseError}
        />

        <Footer />
      </div>
    </LanguageProvider>
  );
}
