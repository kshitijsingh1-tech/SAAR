import React, { useState } from 'react';
import {
  Plus, MessageSquare, Search, Trash2,
  Sprout, Construction, Orbit, PanelLeftClose,
  Zap, Activity
} from 'lucide-react';

export function ChatSidebar({
  isOpen,
  onClose,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  theme = 'light'
}) {
  const [searchFilter, setSearchFilter] = useState('');

  if (!isOpen) return null;

  const filteredSessions = sessions.filter((s) =>
    s.query.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const getDomainIcon = (domain) => {
    switch (domain) {
      case 'agriculture':
        return <Sprout size={13} className="text-emerald" />;
      case 'infrastructure':
        return <Construction size={13} className="text-amber" />;
      case 'astronomy':
        return <Orbit size={13} className="text-purple" />;
      default:
        return <MessageSquare size={13} className="text-primary" />;
    }
  };

  const logoSrc = theme === 'dark' ? '/saar-logo-white.png' : '/saar-logo-dark.png';
  const wordmarkSrc = theme === 'dark' ? '/saar-wordmark-white.png' : '/saar-wordmark-dark.png';

  return (
    <aside className="chatgpt-sidebar">
      {/* Sidebar Header */}
      <div className="sidebar-header-bar">
        <div className="brand-logo-mini">
          <img
            src={logoSrc}
            alt="Saar Logo"
            className="saar-brand-emblem-img"
          />
          <img
            src={wordmarkSrc}
            alt="SAAR"
            className="saar-brand-wordmark-img"
          />
        </div>

        <button className="sidebar-close-btn" onClick={onClose} title="Close sidebar">
          <PanelLeftClose size={17} />
        </button>
      </div>

      {/* + New Investigation Button */}
      <div className="sidebar-new-chat-wrapper">
        <button className="btn-new-chat" onClick={onNewSession}>
          <Plus size={16} />
          <span>New Investigation</span>
        </button>
      </div>

      {/* Search Input */}
      <div className="sidebar-search-box">
        <Search size={14} className="search-icon-mini" />
        <input
          type="text"
          placeholder="Search investigations..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          className="search-input-mini"
        />
      </div>

      {/* Sessions List */}
      <div className="sidebar-history-list">
        <div className="history-group-label">Recent Investigations</div>
        {filteredSessions.map((session) => (
          <div
            key={session.id}
            className={`session-row ${activeSessionId === session.id ? 'active-session' : ''}`}
            onClick={() => onSelectSession(session.id)}
          >
            <div className="session-icon">
              {getDomainIcon(session.domain)}
            </div>
            <div className="session-title-text" title={session.query}>
              {session.query}
            </div>
            <button
              className="btn-delete-session"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteSession(session.id);
              }}
              title="Delete session"
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
