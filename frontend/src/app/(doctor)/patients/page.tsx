'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { api, type PatientOverview } from '@/lib/api';
import {
  AlertTriangleIcon,
  UsersIcon,
  ArrowRightIcon,
  Loader2Icon,
  UserPlusIcon,
  XMarkIcon,
  ClockIcon,
  MessageSquareIcon,
  ArrowUpDownIcon,
  SparklesIcon,
} from '@/components/ui/icons';
import { cn } from '@/lib/utils';
import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from '@/components/ui/dialog';
import { PatientTableSkeleton } from '@/components/ui/skeleton';
import { SearchInput } from '@/components/ui/search-input';
import { Pagination, PaginationInfo } from '@/components/ui/pagination';
import { Button } from '@/components/ui/button';

const PAGE_SIZE = 10;

export default function PatientsPage() {
  const [patients, setPatients] = useState<PatientOverview[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [patientEmail, setPatientEmail] = useState('');
  const [requestMessage, setRequestMessage] = useState('');
  const [sendingRequest, setSendingRequest] = useState(false);
  const [requestError, setRequestError] = useState('');
  const [requestSuccess, setRequestSuccess] = useState('');
  const [pendingRequestsCount, setPendingRequestsCount] = useState(0);

  // Pagination & search state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'risk' | 'name' | 'mood'>('risk');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const t = useTranslations('doctor.patients');
  const common = useTranslations('common');

  const fetchPatients = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getDoctorPatients({
        limit: PAGE_SIZE,
        offset: (currentPage - 1) * PAGE_SIZE,
        search: searchQuery || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setPatients(data.items);
      setTotalItems(data.total);
    } catch (error) {
      console.error('Error fetching patients:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, searchQuery, sortBy, sortOrder]);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  useEffect(() => {
    const fetchPendingRequests = async () => {
      try {
        const response = await api.getConnectionRequests({ status: 'PENDING', limit: 1 });
        setPendingRequestsCount(response.total);
      } catch (error) {
        console.error('Error fetching pending requests:', error);
      }
    };
    fetchPendingRequests();
  }, []);

  // Reset to page 1 when search or sort changes
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
  };

  const handleSortChange = (newSortBy: 'risk' | 'name' | 'mood') => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
    setCurrentPage(1);
  };

  const totalPages = Math.ceil(totalItems / PAGE_SIZE);

  const handleSendRequest = async () => {
    if (!patientEmail.trim()) {
      setRequestError(t('addPatient.emailRequired'));
      return;
    }

    setSendingRequest(true);
    setRequestError('');
    setRequestSuccess('');

    try {
      await api.sendConnectionRequest(patientEmail.trim(), requestMessage.trim() || undefined);
      setRequestSuccess(t('addPatient.success'));
      setPatientEmail('');
      setRequestMessage('');
      setPendingRequestsCount(prev => prev + 1);
      setTimeout(() => {
        setShowAddModal(false);
        setRequestSuccess('');
      }, 2000);
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : t('addPatient.error'));
    } finally {
      setSendingRequest(false);
    }
  };

  const handleCloseModal = () => {
    setShowAddModal(false);
    setPatientEmail('');
    setRequestMessage('');
    setRequestError('');
    setRequestSuccess('');
  };

  const getSeverityBadge = (score: number | null) => {
    if (score === null) return <span className="bg-muted text-muted-foreground px-2.5 py-1 rounded-md text-xs font-medium">{t('notAssessed')}</span>;
    if (score <= 4) return <span className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-md text-xs font-medium">{t('severity.normal')}</span>;
    if (score <= 9) return <span className="bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border border-yellow-500/20 px-2.5 py-1 rounded-md text-xs font-medium">{t('severity.mild')}</span>;
    if (score <= 14) return <span className="bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 px-2.5 py-1 rounded-md text-xs font-medium">{t('severity.moderate')}</span>;
    return <span className="bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 px-2.5 py-1 rounded-md text-xs font-medium">{t('severity.severe')}</span>;
  };

  const getMoodColor = (mood: number | null) => {
    if (mood === null) return 'text-muted-foreground';
    if (mood < 4) return 'text-red-500 font-medium';
    if (mood < 6) return 'text-yellow-500 font-medium';
    return 'text-emerald-500 font-medium';
  };

  // Show initial loading skeleton only on first load
  const isInitialLoading = loading && patients.length === 0 && !searchQuery;

  // Calculate risk count from current page patients
  const riskCount = patients.reduce((sum, p) => sum + p.unreviewed_risks, 0);

  if (isInitialLoading) {
    return (
      <div className="space-y-6 animate-in fade-in duration-300">
        {/* Header skeleton */}
        <div className="flex justify-between items-center bg-card p-4 rounded-xl border border-border shadow-sm">
          <div>
            <h2 className="text-xl font-bold text-foreground">{t('title')}</h2>
            <p className="text-sm text-muted-foreground mt-1">{t('subtitle')}</p>
          </div>
        </div>
        {/* Table skeleton */}
        <div className="bg-card rounded-2xl shadow-sm border border-border overflow-hidden p-4">
          <PatientTableSkeleton rows={5} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-center bg-card p-4 rounded-xl border border-border shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-foreground">{t('title')}</h2>
          <p className="text-sm text-muted-foreground mt-1">{t('subtitle')}</p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/patients/create"
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all shadow-sm bg-emerald-600 text-white hover:bg-emerald-700 hover:shadow-md"
          >
            <UserPlusIcon className="w-4 h-4" />
            <span>Create Patient</span>
          </Link>

          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all shadow-sm bg-primary text-primary-foreground hover:bg-primary/90 hover:shadow-md"
          >
            <UserPlusIcon className="w-4 h-4" />
            <span>{t('addPatient.button')}</span>
          </button>

          <Link
            href="/pending-requests"
            className={cn(
              "flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all shadow-sm",
              pendingRequestsCount > 0
                ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 hover:bg-amber-500/20"
                : "bg-card text-muted-foreground border border-border hover:bg-muted"
            )}
          >
            <ClockIcon className="w-4 h-4" />
            <span>{t('pendingRequests')}</span>
            {pendingRequestsCount > 0 && (
              <span className="bg-amber-500 text-white px-2 py-0.5 rounded-full text-xs font-bold leading-none min-w-[20px] text-center">
                {pendingRequestsCount}
              </span>
            )}
          </Link>

          <Link
            href="/risk-queue"
            className={cn(
              "flex items-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all shadow-sm",
              riskCount > 0
                ? "bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 hover:bg-red-500/20"
                : "bg-card text-muted-foreground border border-border hover:bg-muted"
            )}
          >
            <AlertTriangleIcon className={cn("w-4 h-4", riskCount > 0 && "fill-current")} />
            <span>{t('riskQueue')}</span>
            {riskCount > 0 && (
              <span className="bg-red-600 text-white px-2 py-0.5 rounded-full text-xs font-bold leading-none min-w-[20px] text-center">
                {riskCount}
              </span>
            )}
          </Link>
        </div>
      </div>

      {/* Search and Sort Controls */}
      <div className="bg-card rounded-xl border border-border p-4 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex-1 min-w-[200px] max-w-sm">
          <SearchInput
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder={t('searchPlaceholder')}
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">{common('sortBy')}:</span>
          <div className="flex gap-1">
            <Button
              variant={sortBy === 'risk' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleSortChange('risk')}
              className="gap-1"
            >
              {t('sortOptions.risk')}
              {sortBy === 'risk' && <ArrowUpDownIcon className="w-3 h-3" />}
            </Button>
            <Button
              variant={sortBy === 'name' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleSortChange('name')}
              className="gap-1"
            >
              {t('sortOptions.name')}
              {sortBy === 'name' && <ArrowUpDownIcon className="w-3 h-3" />}
            </Button>
            <Button
              variant={sortBy === 'mood' ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleSortChange('mood')}
              className="gap-1"
            >
              {t('sortOptions.mood')}
              {sortBy === 'mood' && <ArrowUpDownIcon className="w-3 h-3" />}
            </Button>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-2xl shadow-sm border border-border overflow-hidden relative">
        {/* Loading overlay for pagination/search */}
        {loading && (
          <div className="absolute inset-0 bg-background/50 flex items-center justify-center z-10">
            <Loader2Icon className="w-6 h-6 animate-spin text-primary" />
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/50 border-b border-border">
                <th className="text-left px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {t('columns.patientName')}
                </th>
                <th className="text-center px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {t('columns.moodAvg')}
                </th>
                <th className="text-center px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {t('columns.phq9')}
                </th>
                <th className="text-center px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {t('columns.gad7')}
                </th>
                <th className="text-center px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {t('columns.pendingRisks')}
                </th>
                <th className="text-right px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {t('columns.actions')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {patients.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center">
                      <UsersIcon className="w-8 h-8 text-muted-foreground mb-2" />
                      <p className="text-muted-foreground">{common('noResults')}</p>
                      {searchQuery && (
                        <button
                          onClick={() => handleSearchChange('')}
                          className="mt-2 text-sm text-primary hover:underline"
                        >
                          {common('clearFilters')}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                patients.map((patient) => (
                  <tr key={patient.patient_id} className="group hover:bg-muted/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold mr-3">
                          {patient.patient_name[0]}
                        </div>
                        <span className="font-semibold text-foreground">{patient.patient_name}</span>
                      </div>
                    </td>
                    <td className="text-center px-6 py-4">
                      {patient.recent_mood_avg !== null ? (
                        <span className={cn("text-lg font-bold", getMoodColor(patient.recent_mood_avg))}>
                          {patient.recent_mood_avg.toFixed(1)}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </td>
                    <td className="text-center px-6 py-4">
                      <div className="flex justify-center flex-col items-center space-y-1">
                        {patient.latest_phq9 !== null ? (
                          <>
                            <span className="font-mono font-medium text-foreground">{patient.latest_phq9}</span>
                            {getSeverityBadge(patient.latest_phq9)}
                          </>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </div>
                    </td>
                    <td className="text-center px-6 py-4">
                      <div className="flex justify-center flex-col items-center space-y-1">
                        {patient.latest_gad7 !== null ? (
                          <>
                            <span className="font-mono font-medium text-foreground">{patient.latest_gad7}</span>
                            {getSeverityBadge(patient.latest_gad7)}
                          </>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </div>
                    </td>
                    <td className="text-center px-6 py-4">
                      {patient.unreviewed_risks > 0 ? (
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-600 dark:text-red-400 animate-pulse">
                          {t('pendingItems', { count: patient.unreviewed_risks })}
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-sm">{common('none')}</span>
                      )}
                    </td>
                    <td className="text-right px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/patients/${patient.patient_id}/ai-assistant`}
                          className="inline-flex items-center text-primary hover:text-primary/80 font-medium text-sm transition-colors"
                          title={t('aiAssistant', { defaultValue: 'AI Assistant' })}
                        >
                          <SparklesIcon className="w-4 h-4" />
                        </Link>
                        <Link
                          href={`/doctor-messages?patient=${patient.patient_id}`}
                          className="inline-flex items-center text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 font-medium text-sm transition-colors"
                          title={t('sendMessage', { defaultValue: 'Send message' })}
                        >
                          <MessageSquareIcon className="w-4 h-4" />
                        </Link>
                        <Link
                          href={`/patients/${patient.patient_id}`}
                          className="inline-flex items-center text-primary hover:text-primary/80 font-medium text-sm group-hover:translate-x-1 transition-transform"
                        >
                          {common('view')}
                          <ArrowRightIcon className="w-4 h-4 ml-1" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalItems > 0 && (
          <div className="border-t border-border px-6 py-4 flex flex-wrap items-center justify-between gap-4">
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
      </div>

      {/* Legend - Updated to be cleaner */}
      <div className="bg-muted/50 p-4 rounded-xl border border-border/50">
        <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">{t('legend')}</p>
        <div className="flex flex-wrap gap-3 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span className="text-muted-foreground">{t('legendNormal')}</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-yellow-400"></span>
            <span className="text-muted-foreground">{t('legendMild')}</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-orange-500"></span>
            <span className="text-muted-foreground">{t('legendModerate')}</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500"></span>
            <span className="text-muted-foreground">{t('legendSevere')}</span>
          </div>
        </div>
      </div>

      {/* Add Patient Modal */}
      <Dialog open={showAddModal} onClose={handleCloseModal}>
        <DialogBackdrop />
        <DialogPanel>
          <div className="flex items-center justify-between mb-4">
            <DialogTitle className="mb-0">{t('addPatient.title')}</DialogTitle>
            <button
              onClick={handleCloseModal}
              className="p-1 hover:bg-muted rounded-lg transition-colors"
            >
              <XMarkIcon className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>

          <p className="text-sm text-muted-foreground mb-4">
            {t('addPatient.description')}
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                {t('addPatient.emailLabel')}
              </label>
              <input
                type="email"
                value={patientEmail}
                onChange={(e) => setPatientEmail(e.target.value)}
                placeholder={t('addPatient.emailPlaceholder')}
                className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                {t('addPatient.messageLabel')}
              </label>
              <textarea
                value={requestMessage}
                onChange={(e) => setRequestMessage(e.target.value)}
                placeholder={t('addPatient.messagePlaceholder')}
                rows={3}
                className="w-full px-3 py-2 border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent resize-none"
              />
            </div>

            {requestError && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-sm text-destructive">
                {requestError}
              </div>
            )}

            {requestSuccess && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-sm text-emerald-600 dark:text-emerald-400">
                {requestSuccess}
              </div>
            )}

            <div className="flex space-x-3 pt-2">
              <button
                onClick={handleCloseModal}
                className="flex-1 px-4 py-2 border border-border text-muted-foreground rounded-lg hover:bg-muted transition-colors"
              >
                {common('cancel')}
              </button>
              <button
                onClick={handleSendRequest}
                disabled={sendingRequest}
                className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {sendingRequest ? (
                  <Loader2Icon className="w-4 h-4 animate-spin" />
                ) : (
                  t('addPatient.send')
                )}
              </button>
            </div>
          </div>
        </DialogPanel>
      </Dialog>
    </div>
  );
}
