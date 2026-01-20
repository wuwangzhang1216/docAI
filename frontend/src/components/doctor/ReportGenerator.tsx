'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { FileText, Download, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

interface PreVisitSummary {
  id: string;
  patient_id: string;
  scheduled_visit?: string;
  chief_complaint?: string;
  phq9_score?: number;
  gad7_score?: number;
  created_at: string;
}

interface ReportGeneratorProps {
  patientId: string;
  patientName: string;
}

export default function ReportGenerator({ patientId, patientName }: ReportGeneratorProps) {
  const [summaries, setSummaries] = useState<PreVisitSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedSummary, setSelectedSummary] = useState<string | null>(null);

  const loadSummaries = async () => {
    try {
      setLoading(true);
      const data = await api.getPatientPreVisitSummaries(patientId);
      setSummaries(data);
      if (data.length > 0) {
        setSelectedSummary(data[0].id);
      }
    } catch (err) {
      console.error('Error loading summaries:', err);
      setError('Failed to load pre-visit summaries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummaries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  const handleGenerateReport = async () => {
    if (!selectedSummary) {
      setError('Please select a pre-visit summary');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      setSuccess(null);

      const result = await api.generatePreVisitReport(selectedSummary, {
        include_risk_events: true,
        include_checkin_trend: true,
        days_for_trend: 7,
      });

      // Open PDF in new tab
      window.open(result.pdf_url, '_blank');
      setSuccess('Report generated successfully!');
    } catch (err) {
      console.error('Error generating report:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-center py-4">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-border bg-indigo-500/10 dark:bg-indigo-500/5">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          <h3 className="font-medium text-foreground">Generate Pre-Visit Report</h3>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 text-red-700 dark:text-red-400 rounded-lg text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {success && (
          <div className="flex items-center gap-2 p-3 bg-green-500/10 text-green-700 dark:text-green-400 rounded-lg text-sm">
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
            {success}
          </div>
        )}

        {summaries.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-2 text-muted-foreground/50" />
            <p>No pre-visit summaries available for this patient.</p>
            <p className="text-sm mt-1">Pre-visit summaries are created during AI conversations.</p>
          </div>
        ) : (
          <>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Select Pre-Visit Summary
              </label>
              <select
                value={selectedSummary || ''}
                onChange={(e) => setSelectedSummary(e.target.value)}
                className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-lg focus:ring-2 focus:ring-ring focus:border-ring"
              >
                {summaries.map((summary) => (
                  <option key={summary.id} value={summary.id}>
                    {formatDate(summary.created_at)}
                    {summary.scheduled_visit && ` - Visit: ${summary.scheduled_visit}`}
                    {summary.phq9_score !== null && ` | PHQ-9: ${summary.phq9_score}`}
                    {summary.gad7_score !== null && ` | GAD-7: ${summary.gad7_score}`}
                  </option>
                ))}
              </select>
            </div>

            {selectedSummary && (
              <div className="bg-muted rounded-lg p-3 text-sm">
                <p className="font-medium text-foreground mb-1">Chief Complaint:</p>
                <p className="text-muted-foreground">
                  {summaries.find(s => s.id === selectedSummary)?.chief_complaint || 'Not specified'}
                </p>
              </div>
            )}

            <button
              onClick={handleGenerateReport}
              disabled={generating || !selectedSummary}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Generating PDF...
                </>
              ) : (
                <>
                  <Download className="w-5 h-5" />
                  Generate PDF Report
                </>
              )}
            </button>

            <p className="text-xs text-muted-foreground text-center">
              The report will include assessment results, risk alerts, and recent check-in trends.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
