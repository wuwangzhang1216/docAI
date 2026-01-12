'use client';

import * as React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  showPageNumbers?: boolean;
  showFirstLast?: boolean;
  className?: string;
  disabled?: boolean;
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  showPageNumbers = true,
  showFirstLast = false,
  className,
  disabled = false,
}: PaginationProps) {
  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  // Generate page numbers to show
  const getPageNumbers = React.useCallback(() => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      // Calculate start and end of visible range
      let start = Math.max(2, currentPage - 1);
      let end = Math.min(totalPages - 1, currentPage + 1);

      // Adjust if at the edges
      if (currentPage <= 3) {
        end = Math.min(4, totalPages - 1);
      } else if (currentPage >= totalPages - 2) {
        start = Math.max(2, totalPages - 3);
      }

      // Add ellipsis if needed before middle pages
      if (start > 2) {
        pages.push('ellipsis');
      }

      // Add middle pages
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      // Add ellipsis if needed after middle pages
      if (end < totalPages - 1) {
        pages.push('ellipsis');
      }

      // Always show last page
      if (totalPages > 1) {
        pages.push(totalPages);
      }
    }

    return pages;
  }, [currentPage, totalPages]);

  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav
      role="navigation"
      aria-label="Pagination"
      className={cn('flex items-center justify-center gap-1', className)}
    >
      {/* First page button */}
      {showFirstLast && (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onPageChange(1)}
          disabled={disabled || !canGoPrev}
          aria-label="Go to first page"
          className="h-8 w-8"
        >
          <ChevronsLeft className="h-4 w-4" />
        </Button>
      )}

      {/* Previous button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={disabled || !canGoPrev}
        aria-label="Go to previous page"
        className="h-8 w-8"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>

      {/* Page numbers */}
      {showPageNumbers && (
        <div className="flex items-center gap-1">
          {getPageNumbers().map((page, index) =>
            page === 'ellipsis' ? (
              <span
                key={`ellipsis-${index}`}
                className="px-2 text-muted-foreground"
                aria-hidden="true"
              >
                ...
              </span>
            ) : (
              <Button
                key={page}
                variant={page === currentPage ? 'default' : 'ghost'}
                size="icon"
                onClick={() => onPageChange(page)}
                disabled={disabled}
                aria-label={`Page ${page}`}
                aria-current={page === currentPage ? 'page' : undefined}
                className="h-8 w-8"
              >
                {page}
              </Button>
            )
          )}
        </div>
      )}

      {/* Next button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={disabled || !canGoNext}
        aria-label="Go to next page"
        className="h-8 w-8"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>

      {/* Last page button */}
      {showFirstLast && (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onPageChange(totalPages)}
          disabled={disabled || !canGoNext}
          aria-label="Go to last page"
          className="h-8 w-8"
        >
          <ChevronsRight className="h-4 w-4" />
        </Button>
      )}
    </nav>
  );
}

// Simple info component showing "Showing X to Y of Z results"
export interface PaginationInfoProps {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  className?: string;
  labels?: {
    showing?: string;
    to?: string;
    of?: string;
    results?: string;
  };
}

export function PaginationInfo({
  currentPage,
  pageSize,
  totalItems,
  className,
  labels = {},
}: PaginationInfoProps) {
  const { showing = 'Showing', to = 'to', of = 'of', results = 'results' } = labels;

  const start = Math.min((currentPage - 1) * pageSize + 1, totalItems);
  const end = Math.min(currentPage * pageSize, totalItems);

  if (totalItems === 0) {
    return null;
  }

  return (
    <p className={cn('text-sm text-muted-foreground', className)}>
      {showing} <span className="font-medium">{start}</span> {to}{' '}
      <span className="font-medium">{end}</span> {of}{' '}
      <span className="font-medium">{totalItems}</span> {results}
    </p>
  );
}
