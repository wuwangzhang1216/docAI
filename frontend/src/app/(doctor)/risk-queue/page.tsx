'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useI18n } from '@/lib/i18n';
import { api, type RiskEvent, type RiskQueueParams } from '@/lib/api';
import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from '@/components/ui/dialog';
import { SearchInput } from '@/components/ui/search-input';
import { Pagination, PaginationInfo } from '@/components/ui/pagination';
import { Button } from '@/components/ui/button';
import { Loader2Icon } from '@/components/ui/icons';

const PAGE_SIZE = 20;
type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export default function RiskQueuePage() {
  const [riskEvents, setRiskEvents] = useState<RiskEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<RiskEvent | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewing, setReviewing] = useState(false);

  // Pagination & filter state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [riskLevelFilter, setRiskLevelFilter] = useState<RiskLevel | ''>('');

  const t = useTranslations('doctor.riskQueue');
  const common = useTranslations('common');
  const { locale } = useI18n();

  const fetchRiskEvents = useCallback(async () => {
    setLoading(true);
    try {
      const params: RiskQueueParams = {
        limit: PAGE_SIZE,
        offset: (currentPage - 1) * PAGE_SIZE,
      };
      if (searchQuery) params.search = searchQuery;
      if (riskLevelFilter) params.risk_level = riskLevelFilter;

      const data = await api.getRiskQueue(params);
      setRiskEvents(data.items);
      setTotalItems(data.total);
    } catch (error) {
      console.error('Error fetching risk events:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, searchQuery, riskLevelFilter]);

  useEffect(() => {
    fetchRiskEvents();
  }, [fetchRiskEvents]);

  // Reset to page 1 when search or filter changes
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
  };

  const handleRiskLevelFilter = (level: RiskLevel | '') => {
    setRiskLevelFilter(level);
    setCurrentPage(1);
  };

  const totalPages = Math.ceil(totalItems / PAGE_SIZE);

  const handleReview = async () => {
    if (!selectedEvent) return;

    setReviewing(true);
    try {
      await api.reviewRiskEvent(selectedEvent.id, reviewNotes || undefined);
      // Remove from list and update total
      setRiskEvents((prev) => prev.filter((e) => e.id !== selectedEvent.id));
      setTotalItems((prev) => Math.max(0, prev - 1));
      setSelectedEvent(null);
      setReviewNotes('');
    } catch (error) {
      console.error('Error reviewing event:', error);
      alert(common('error'));
    } finally {
      setReviewing(false);
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-red-600 text-white';
      case 'HIGH':
        return 'bg-red-500 text-white';
      case 'MEDIUM':
        return 'bg-orange-500 text-white';
      default:
        return 'bg-yellow-500 text-white';
    }
  };

  const getRiskTypeLabel = (type?: string) => {
    switch (type) {
      case 'SUICIDAL':
        return t('riskTypes.suicidal');
      case 'SELF_HARM':
        return t('riskTypes.selfHarm');
      case 'VIOLENCE':
        return t('riskTypes.violence');
      default:
        return t('riskTypes.other');
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString(locale === 'zh' ? 'zh-CN' : 'en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const riskLevels: RiskLevel[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

  // Initial loading state
  const isInitialLoading = loading && riskEvents.length === 0 && !searchQuery && !riskLevelFilter;

  if (isInitialLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-foreground">{t('title')}</h2>
        <span className="text-sm text-muted-foreground">
          {t('pending', { count: totalItems })}
        </span>
      </div>

      {/* Search and Filters */}
      <div className="bg-card rounded-xl border border-border p-4 flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-[200px] max-w-sm">
          <SearchInput
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder={t('searchPlaceholder', { defaultValue: 'Search trigger text...' })}
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">{t('filterByLevel', { defaultValue: 'Filter by level' })}:</span>
          <div className="flex gap-1">
            <Button
              variant={riskLevelFilter === '' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleRiskLevelFilter('')}
            >
              {common('all')}
            </Button>
            {riskLevels.map((level) => (
              <Button
                key={level}
                variant={riskLevelFilter === level ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleRiskLevelFilter(level)}
                className={riskLevelFilter === level ? getRiskLevelColor(level) : ''}
              >
                {level}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Content with loading overlay */}
      <div className="relative">
        {loading && (
          <div className="absolute inset-0 bg-background/50 flex items-center justify-center z-10 rounded-xl">
            <Loader2Icon className="w-6 h-6 animate-spin text-primary" />
          </div>
        )}

        {riskEvents.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-8 text-center">
            <div className="text-4xl mb-2">✅</div>
            <p className="text-muted-foreground">
              {searchQuery || riskLevelFilter ? common('noResults') : t('allClear')}
            </p>
            {(searchQuery || riskLevelFilter) && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setRiskLevelFilter('');
                  setCurrentPage(1);
                }}
                className="mt-2 text-sm text-primary hover:underline"
              >
                {common('clearFilters')}
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {riskEvents.map((event) => (
              <div
                key={event.id}
                className="bg-card border border-border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => setSelectedEvent(event)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${getRiskLevelColor(
                          event.risk_level
                        )}`}
                      >
                        {event.risk_level}
                      </span>
                      {event.risk_type && (
                        <span className="text-sm text-muted-foreground">
                          {getRiskTypeLabel(event.risk_type)}
                        </span>
                      )}
                      {event.ai_confidence && (
                        <span className="text-xs text-muted-foreground">
                          {t('confidence')}: {Math.round(event.ai_confidence * 100)}%
                        </span>
                      )}
                    </div>
                    <p className="font-medium text-foreground">{event.patient_name || t('unknownPatient')}</p>
                    {event.trigger_text && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        "{event.trigger_text}"
                      </p>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDate(event.created_at)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalItems > 0 && (
        <div className="bg-card rounded-xl border border-border px-6 py-4 flex flex-wrap items-center justify-between gap-4">
          <PaginationInfo
            currentPage={currentPage}
            pageSize={PAGE_SIZE}
            totalItems={totalItems}
          />
          {totalPages > 1 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          )}
        </div>
      )}

      {/* Review Modal */}
      <Dialog
        open={!!selectedEvent}
        onClose={() => {
          setSelectedEvent(null);
          setReviewNotes('');
        }}
      >
        <DialogBackdrop />
        <DialogPanel className="max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogTitle>{t('modalTitle')}</DialogTitle>

          {selectedEvent && (
            <>
              <div className="space-y-4">
                {/* Event Info */}
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-0.5 rounded text-sm font-medium ${getRiskLevelColor(
                      selectedEvent.risk_level
                    )}`}
                  >
                    {selectedEvent.risk_level}
                  </span>
                  {selectedEvent.risk_type && (
                    <span className="text-muted-foreground">
                      {getRiskTypeLabel(selectedEvent.risk_type)}
                    </span>
                  )}
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">{t('patient')}</p>
                  <p className="font-medium text-foreground">
                    {selectedEvent.patient_name || common('unknown')}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground">{t('time')}</p>
                  <p className="text-foreground">{formatDate(selectedEvent.created_at)}</p>
                </div>

                {selectedEvent.trigger_text && (
                  <div>
                    <p className="text-sm text-muted-foreground">{t('triggerText')}</p>
                    <p className="bg-red-500/10 p-3 rounded-lg text-red-600 dark:text-red-400 mt-1">
                      "{selectedEvent.trigger_text}"
                    </p>
                  </div>
                )}

                {/* Review Notes */}
                <div>
                  <label className="text-sm text-muted-foreground">{t('reviewNotes')}</label>
                  <textarea
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    placeholder={t('reviewPlaceholder')}
                    rows={3}
                    className="w-full border border-input bg-background rounded-lg px-3 py-2 mt-1 focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
              </div>

              {/* Actions */}
              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => {
                    setSelectedEvent(null);
                    setReviewNotes('');
                  }}
                  className="flex-1 py-2 border border-border rounded-lg hover:bg-muted text-muted-foreground transition-colors"
                >
                  {common('cancel')}
                </button>
                <button
                  onClick={handleReview}
                  disabled={reviewing}
                  className="flex-1 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {reviewing ? t('processing') : t('markReviewed')}
                </button>
              </div>
            </>
          )}
        </DialogPanel>
      </Dialog>
    </div>
  );
}
