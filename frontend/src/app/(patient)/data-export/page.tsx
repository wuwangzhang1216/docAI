'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { api, ExportRequestListItem, ExportRequestResponse, ExportFormat, ExportStatus } from '@/lib/api';
import {
  Download,
  FileJson,
  FileSpreadsheet,
  FileText,
  Loader2,
  ArrowLeft,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  RefreshCw,
  Calendar,
  MessageSquare,
  ClipboardList,
  User,
  Mail,
  Info,
  Shield,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type ExportSection = 'profile' | 'checkins' | 'assessments' | 'conversations' | 'messages';

interface ExportFormState {
  export_format: ExportFormat;
  include_profile: boolean;
  include_checkins: boolean;
  include_assessments: boolean;
  include_conversations: boolean;
  include_messages: boolean;
  date_from?: string;
  date_to?: string;
}

const formatIcons: Record<ExportFormat, typeof FileJson> = {
  JSON: FileJson,
  CSV: FileSpreadsheet,
  PDF_SUMMARY: FileText,
};

const statusConfig: Record<ExportStatus, { icon: typeof Clock; color: string; bgColor: string }> = {
  PENDING: { icon: Clock, color: 'text-yellow-600 dark:text-yellow-400', bgColor: 'bg-yellow-100 dark:bg-yellow-900/30' },
  PROCESSING: { icon: Loader2, color: 'text-blue-600 dark:text-blue-400', bgColor: 'bg-blue-100 dark:bg-blue-900/30' },
  COMPLETED: { icon: CheckCircle2, color: 'text-emerald-600 dark:text-emerald-400', bgColor: 'bg-emerald-100 dark:bg-emerald-900/30' },
  FAILED: { icon: XCircle, color: 'text-red-600 dark:text-red-400', bgColor: 'bg-red-100 dark:bg-red-900/30' },
  EXPIRED: { icon: AlertCircle, color: 'text-gray-600 dark:text-gray-400', bgColor: 'bg-gray-100 dark:bg-gray-900/30' },
  DOWNLOADED: { icon: CheckCircle2, color: 'text-emerald-600 dark:text-emerald-400', bgColor: 'bg-emerald-100 dark:bg-emerald-900/30' },
};

const sectionConfig: Record<ExportSection, { icon: typeof User; label: string }> = {
  profile: { icon: User, label: 'Profile' },
  checkins: { icon: ClipboardList, label: 'Daily Check-ins' },
  assessments: { icon: ClipboardList, label: 'Assessments' },
  conversations: { icon: MessageSquare, label: 'AI Conversations' },
  messages: { icon: Mail, label: 'Doctor Messages' },
};

export default function DataExportPage() {
  const t = useTranslations('patient.dataExport');
  const common = useTranslations('common');

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [exportRequests, setExportRequests] = useState<ExportRequestListItem[]>([]);
  const [currentExport, setCurrentExport] = useState<ExportRequestResponse | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const [formState, setFormState] = useState<ExportFormState>({
    export_format: 'JSON',
    include_profile: true,
    include_checkins: true,
    include_assessments: true,
    include_conversations: true,
    include_messages: true,
  });

  const fetchExportRequests = useCallback(async () => {
    try {
      const data = await api.getExportRequests(10);
      setExportRequests(data);

      // Check if there's a processing export
      const processingExport = data.find(
        (e) => e.status === 'PENDING' || e.status === 'PROCESSING'
      );
      if (processingExport) {
        const detail = await api.getExportRequestDetail(processingExport.id);
        setCurrentExport(detail);
      }
    } catch (err) {
      console.error('Error fetching export requests:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExportRequests();
  }, [fetchExportRequests]);

  // Poll for progress if there's a processing export
  useEffect(() => {
    if (!currentExport || !['PENDING', 'PROCESSING'].includes(currentExport.status)) {
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const progress = await api.getExportProgress(currentExport.id);
        setCurrentExport((prev) =>
          prev
            ? {
                ...prev,
                status: progress.status,
                progress_percent: progress.progress_percent,
                error_message: progress.error_message,
              }
            : null
        );

        if (!['PENDING', 'PROCESSING'].includes(progress.status)) {
          clearInterval(pollInterval);
          fetchExportRequests();
        }
      } catch (err) {
        console.error('Error polling progress:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [currentExport, fetchExportRequests]);

  const handleFormatChange = (format: ExportFormat) => {
    setFormState((prev) => ({ ...prev, export_format: format }));
  };

  const handleSectionToggle = (section: ExportSection) => {
    const key = `include_${section}` as keyof ExportFormState;
    setFormState((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    setSuccess(false);

    try {
      const response = await api.requestDataExport({
        export_format: formState.export_format,
        include_profile: formState.include_profile,
        include_checkins: formState.include_checkins,
        include_assessments: formState.include_assessments,
        include_conversations: formState.include_conversations,
        include_messages: formState.include_messages,
        date_from: formState.date_from,
        date_to: formState.date_to,
      });

      setCurrentExport(response);
      setSuccess(true);
      fetchExportRequests();
    } catch (err: unknown) {
      console.error('Error requesting export:', err);
      const errorMessage = err instanceof Error ? err.message : common('error');
      if (errorMessage.includes('429') || errorMessage.includes('rate')) {
        setError(t('rateLimitError', { defaultValue: 'You can only request one export per 24 hours. Please try again later.' }));
      } else {
        setError(errorMessage);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownload = (token: string) => {
    const url = api.getExportDownloadUrl(token);
    window.open(url, '_blank');
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const hasProcessingExport = currentExport && ['PENDING', 'PROCESSING'].includes(currentExport.status);
  const canRequestNew = !hasProcessingExport;

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="space-y-4 max-w-2xl mx-auto pb-20">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <Link
            href="/profile"
            className="p-2 hover:bg-muted rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-muted-foreground" />
          </Link>
          <div>
            <h1 className="text-xl font-bold">{t('title', { defaultValue: 'Export My Data' })}</h1>
            <p className="text-sm text-muted-foreground">
              {t('subtitle', { defaultValue: 'Download a copy of your personal data' })}
            </p>
          </div>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
          <div className="flex gap-3">
            <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800 dark:text-blue-300">
              <p className="font-medium mb-1">{t('infoTitle', { defaultValue: 'Your Data Rights' })}</p>
              <p>{t('infoDesc', { defaultValue: 'You have the right to receive a copy of your personal data. Exports are available once every 24 hours and download links expire after 7 days.' })}</p>
            </div>
          </div>
        </div>

        {/* Processing Export Banner */}
        {hasProcessingExport && currentExport && (
          <div className="bg-primary/5 border border-primary/20 rounded-xl p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="animate-spin">
                <Loader2 className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="font-medium text-foreground">
                  {t('processingTitle', { defaultValue: 'Export in Progress' })}
                </p>
                <p className="text-sm text-muted-foreground">
                  {t('processingDesc', { defaultValue: 'Your data is being prepared...' })}
                </p>
              </div>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${currentExport.progress_percent}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1 text-right">
              {currentExport.progress_percent}%
            </p>
          </div>
        )}

        {/* Success Message */}
        {success && !hasProcessingExport && (
          <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl p-4 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <p className="text-sm text-emerald-800 dark:text-emerald-300">
              {t('exportComplete', { defaultValue: 'Your export is ready for download!' })}
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
            <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
          </div>
        )}

        {/* New Export Form */}
        {canRequestNew && (
          <div className="bg-card border border-border rounded-xl p-4 space-y-4">
            <h2 className="font-semibold text-foreground flex items-center gap-2">
              <Download className="w-5 h-5 text-primary" />
              {t('newExport', { defaultValue: 'Request New Export' })}
            </h2>

            {/* Format Selection */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                {t('formatLabel', { defaultValue: 'Export Format' })}
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['JSON', 'CSV', 'PDF_SUMMARY'] as ExportFormat[]).map((format) => {
                  const Icon = formatIcons[format];
                  const isSelected = formState.export_format === format;
                  return (
                    <button
                      key={format}
                      onClick={() => handleFormatChange(format)}
                      className={cn(
                        'p-3 rounded-lg border-2 transition-all flex flex-col items-center gap-1',
                        isSelected
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      )}
                    >
                      <Icon className={cn('w-6 h-6', isSelected ? 'text-primary' : 'text-muted-foreground')} />
                      <span className={cn('text-xs font-medium', isSelected ? 'text-primary' : 'text-muted-foreground')}>
                        {format === 'PDF_SUMMARY' ? 'PDF' : format}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                {formState.export_format === 'JSON' && t('formatJsonDesc', { defaultValue: 'Complete structured data in JSON format' })}
                {formState.export_format === 'CSV' && t('formatCsvDesc', { defaultValue: 'Spreadsheet-compatible CSV files in ZIP archive' })}
                {formState.export_format === 'PDF_SUMMARY' && t('formatPdfDesc', { defaultValue: 'Human-readable summary report' })}
              </p>
            </div>

            {/* Data Sections */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                {t('sectionsLabel', { defaultValue: 'Include Data' })}
              </label>
              <div className="space-y-2">
                {(Object.keys(sectionConfig) as ExportSection[]).map((section) => {
                  const { icon: Icon, label } = sectionConfig[section];
                  const key = `include_${section}` as keyof ExportFormState;
                  const isChecked = formState[key] as boolean;
                  return (
                    <label
                      key={section}
                      className={cn(
                        'flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all',
                        isChecked
                          ? 'border-primary/50 bg-primary/5'
                          : 'border-border hover:border-primary/30'
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleSectionToggle(section)}
                        className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                      />
                      <Icon className={cn('w-4 h-4', isChecked ? 'text-primary' : 'text-muted-foreground')} />
                      <span className={cn('text-sm', isChecked ? 'text-foreground' : 'text-muted-foreground')}>
                        {t(`section.${section}`, { defaultValue: label })}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Date Range (Optional) */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                {t('dateRangeLabel', { defaultValue: 'Date Range (Optional)' })}
              </label>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    {t('dateFrom', { defaultValue: 'From' })}
                  </label>
                  <input
                    type="date"
                    value={formState.date_from || ''}
                    onChange={(e) => setFormState((prev) => ({ ...prev, date_from: e.target.value || undefined }))}
                    className="w-full border border-input bg-background text-foreground rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">
                    {t('dateTo', { defaultValue: 'To' })}
                  </label>
                  <input
                    type="date"
                    value={formState.date_to || ''}
                    onChange={(e) => setFormState((prev) => ({ ...prev, date_to: e.target.value || undefined }))}
                    className="w-full border border-input bg-background text-foreground rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {t('dateRangeHint', { defaultValue: 'Leave empty to export all data' })}
              </p>
            </div>

            {/* Security Notice */}
            <div className="flex items-start gap-2 text-xs text-muted-foreground bg-muted/50 p-3 rounded-lg">
              <Shield className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <p>
                {t('securityNotice', { defaultValue: 'Your export will be encrypted and available for 7 days. Download links can only be used 3 times.' })}
              </p>
            </div>

            {/* Submit Button */}
            <Button
              onClick={handleSubmit}
              disabled={submitting || !Object.values(formState).some((v) => v === true && typeof v === 'boolean')}
              className="w-full py-5"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {t('requesting', { defaultValue: 'Requesting Export...' })}
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  {t('requestExport', { defaultValue: 'Request Export' })}
                </>
              )}
            </Button>
          </div>
        )}

        {/* Export History */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-foreground">
              {t('historyTitle', { defaultValue: 'Export History' })}
            </h2>
            <button
              onClick={fetchExportRequests}
              className="p-2 hover:bg-muted rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4 text-muted-foreground" />
            </button>
          </div>

          {exportRequests.length === 0 ? (
            <div className="bg-card border border-border rounded-xl p-8 text-center">
              <Download className="w-12 h-12 mx-auto text-muted-foreground mb-3" />
              <p className="text-muted-foreground">
                {t('noExports', { defaultValue: 'No export history yet' })}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {exportRequests.map((request) => {
                const StatusIcon = statusConfig[request.status].icon;
                const FormatIcon = formatIcons[request.export_format];
                const canDownload = request.can_download && !request.is_expired;

                return (
                  <div
                    key={request.id}
                    className="bg-card border border-border rounded-xl p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={cn('p-2 rounded-lg', statusConfig[request.status].bgColor)}>
                          <StatusIcon
                            className={cn(
                              'w-4 h-4',
                              statusConfig[request.status].color,
                              request.status === 'PROCESSING' && 'animate-spin'
                            )}
                          />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <FormatIcon className="w-4 h-4 text-muted-foreground" />
                            <span className="font-medium text-foreground">
                              {request.export_format === 'PDF_SUMMARY' ? 'PDF Summary' : request.export_format}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(request.created_at)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {request.file_size_bytes && (
                          <span className="text-xs text-muted-foreground">
                            {formatFileSize(request.file_size_bytes)}
                          </span>
                        )}
                        {canDownload && request.download_token && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDownload(request.download_token!)}
                          >
                            <Download className="w-4 h-4 mr-1" />
                            {t('download', { defaultValue: 'Download' })}
                          </Button>
                        )}
                        {request.is_expired && (
                          <span className="text-xs text-muted-foreground">
                            {t('expired', { defaultValue: 'Expired' })}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Progress bar for processing */}
                    {['PENDING', 'PROCESSING'].includes(request.status) && (
                      <div className="mt-3">
                        <div className="w-full bg-muted rounded-full h-1.5">
                          <div
                            className="bg-primary h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${request.progress_percent}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
