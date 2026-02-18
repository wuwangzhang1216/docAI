'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { useTranslations } from 'next-intl'
import { useI18n } from '@/lib/i18n'
import { api, type ConnectionRequestResponse, type ConnectionRequestParams } from '@/lib/api'
import {
  ArrowLeftIcon,
  ClockIcon,
  XMarkIcon,
  CheckIcon,
  Loader2Icon,
  MailIcon,
} from '@/components/ui/icons'
import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from '@/components/ui/dialog'
import { SearchInput } from '@/components/ui/search-input'
import { Pagination, PaginationInfo } from '@/components/ui/pagination'
import { cn } from '@/lib/utils'

const PAGE_SIZE = 20
type RequestStatus = 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED'

export default function PendingRequestsPage() {
  const [requests, setRequests] = useState<ConnectionRequestResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedRequest, setSelectedRequest] = useState<ConnectionRequestResponse | null>(null)
  const [cancelling, setCancelling] = useState(false)
  const [statusFilter, setStatusFilter] = useState<'all' | RequestStatus>('all')

  // Pagination & search state
  const [currentPage, setCurrentPage] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')

  const t = useTranslations('doctor.pendingRequests')
  const common = useTranslations('common')
  const { locale } = useI18n()

  const fetchRequests = useCallback(async () => {
    setLoading(true)
    try {
      const params: ConnectionRequestParams = {
        limit: PAGE_SIZE,
        offset: (currentPage - 1) * PAGE_SIZE,
      }
      if (searchQuery) params.search = searchQuery
      if (statusFilter !== 'all') params.status = statusFilter

      const data = await api.getConnectionRequests(params)
      setRequests(data.items)
      setTotalItems(data.total)
    } catch (error) {
      console.error('Error fetching requests:', error)
    } finally {
      setLoading(false)
    }
  }, [currentPage, searchQuery, statusFilter])

  useEffect(() => {
    fetchRequests()
  }, [fetchRequests])

  // Reset to page 1 when search or filter changes
  const handleSearchChange = (value: string) => {
    setSearchQuery(value)
    setCurrentPage(1)
  }

  const handleStatusFilter = (status: 'all' | RequestStatus) => {
    setStatusFilter(status)
    setCurrentPage(1)
  }

  const totalPages = Math.ceil(totalItems / PAGE_SIZE)

  const handleCancelRequest = async () => {
    if (!selectedRequest) return

    setCancelling(true)
    try {
      await api.cancelConnectionRequest(selectedRequest.id)
      // Update request status in place
      setRequests((prev) =>
        prev.map((r) => (r.id === selectedRequest.id ? { ...r, status: 'CANCELLED' as const } : r))
      )
      setSelectedRequest(null)
    } catch (error) {
      console.error('Error cancelling request:', error)
      alert(common('error'))
    } finally {
      setCancelling(false)
    }
  }

  // Initial loading state
  const isInitialLoading =
    loading && requests.length === 0 && !searchQuery && statusFilter === 'all'

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString(locale === 'zh' ? 'zh-CN' : 'en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-warning/10 text-warning border border-warning/20">
            <ClockIcon className="w-3 h-3 mr-1" />
            {t('status.pending')}
          </span>
        )
      case 'ACCEPTED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-success/10 text-success border border-success/20">
            <CheckIcon className="w-3 h-3 mr-1" />
            {t('status.accepted')}
          </span>
        )
      case 'REJECTED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-destructive/10 text-destructive border border-destructive/20">
            <XMarkIcon className="w-3 h-3 mr-1" />
            {t('status.rejected')}
          </span>
        )
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
            {t('status.cancelled')}
          </span>
        )
      default:
        return null
    }
  }

  if (isInitialLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <Loader2Icon className="w-8 h-8 text-primary animate-spin mb-3" />
        <p className="text-muted-foreground text-sm">{common('loading')}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="flex justify-between items-center bg-card p-4 rounded-xl border border-border shadow-sm">
        <div className="flex items-center space-x-4">
          <Link href="/patients" className="p-2 hover:bg-muted rounded-lg transition-colors">
            <ArrowLeftIcon className="w-5 h-5 text-muted-foreground" />
          </Link>
          <div>
            <h2 className="text-xl font-bold text-foreground">{t('title')}</h2>
            <p className="text-sm text-muted-foreground mt-1">
              {t('subtitle')} ({totalItems})
            </p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-card rounded-xl border border-border p-4 flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-[200px] max-w-sm">
          <SearchInput
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder={t('searchPlaceholder', { defaultValue: 'Search by name or email...' })}
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">{common('filter')}:</span>
          <div className="flex gap-1 flex-wrap">
            {(['all', 'PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED'] as const).map((status) => (
              <button
                key={status}
                onClick={() => handleStatusFilter(status)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                  statusFilter === status
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                {status === 'all' ? common('all') : t(`status.${status.toLowerCase()}`)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Requests List */}
      <div className="relative">
        {/* Loading overlay */}
        {loading && (
          <div className="absolute inset-0 bg-background/50 flex items-center justify-center z-10 rounded-xl">
            <Loader2Icon className="w-6 h-6 animate-spin text-primary" />
          </div>
        )}

        {requests.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 bg-card/50 rounded-2xl border border-dashed border-border">
            <div className="bg-muted p-4 rounded-full mb-4">
              <MailIcon className="w-8 h-8 text-muted-foreground/50" />
            </div>
            <p className="text-foreground font-medium mb-1">
              {searchQuery || statusFilter !== 'all' ? common('noResults') : t('empty.title')}
            </p>
            <p className="text-sm text-muted-foreground">
              {searchQuery || statusFilter !== 'all' ? '' : t('empty.message')}
            </p>
            {(searchQuery || statusFilter !== 'all') && (
              <button
                onClick={() => {
                  setSearchQuery('')
                  setStatusFilter('all')
                  setCurrentPage(1)
                }}
                className="mt-2 text-sm text-primary hover:underline"
              >
                {common('clearFilters')}
              </button>
            )}
          </div>
        ) : (
          <div className="bg-card rounded-2xl shadow-sm border border-border overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-muted/50 border-b border-border">
                    <th className="text-left px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {t('columns.patient')}
                    </th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {t('columns.email')}
                    </th>
                    <th className="text-center px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {t('columns.status')}
                    </th>
                    <th className="text-left px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {t('columns.sentAt')}
                    </th>
                    <th className="text-right px-6 py-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {t('columns.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {requests.map((request) => (
                    <tr key={request.id} className="group hover:bg-muted/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold mr-3">
                            {request.patient_name[0]}
                          </div>
                          <span className="font-semibold text-foreground">
                            {request.patient_name}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground text-sm">
                        {request.patient_email}
                      </td>
                      <td className="text-center px-6 py-4">{getStatusBadge(request.status)}</td>
                      <td className="px-6 py-4 text-muted-foreground text-sm">
                        {formatDate(request.created_at)}
                      </td>
                      <td className="text-right px-6 py-4">
                        {request.status === 'PENDING' && (
                          <button
                            onClick={() => setSelectedRequest(request)}
                            className="text-destructive hover:text-destructive/80 font-medium text-sm"
                          >
                            {t('cancel')}
                          </button>
                        )}
                        {request.responded_at && (
                          <span className="text-muted-foreground text-xs">
                            {formatDate(request.responded_at)}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
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
        )}
      </div>

      {/* Cancel Confirmation Modal */}
      <Dialog open={!!selectedRequest} onClose={() => setSelectedRequest(null)}>
        <DialogBackdrop />
        <DialogPanel>
          <DialogTitle>{t('cancelModal.title')}</DialogTitle>

          {selectedRequest && (
            <>
              <p className="text-muted-foreground mb-4">
                {t('cancelModal.message', { name: selectedRequest.patient_name })}
              </p>

              <div className="bg-muted p-3 rounded-lg mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                    {selectedRequest.patient_name[0]}
                  </div>
                  <div>
                    <p className="font-medium text-foreground">{selectedRequest.patient_name}</p>
                    <p className="text-sm text-muted-foreground">{selectedRequest.patient_email}</p>
                  </div>
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setSelectedRequest(null)}
                  className="flex-1 px-4 py-2 border border-border text-muted-foreground rounded-lg hover:bg-muted transition-colors"
                >
                  {common('cancel')}
                </button>
                <button
                  onClick={handleCancelRequest}
                  disabled={cancelling}
                  className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {cancelling ? (
                    <Loader2Icon className="w-4 h-4 animate-spin" />
                  ) : (
                    t('cancelModal.confirm')
                  )}
                </button>
              </div>
            </>
          )}
        </DialogPanel>
      </Dialog>
    </div>
  )
}
