import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TimelineModule } from 'primeng/timeline';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { TagModule } from 'primeng/tag';
import { TableModule } from 'primeng/table';
import { TooltipModule } from 'primeng/tooltip';
import { SkeletonModule } from 'primeng/skeleton';
import { InputTextModule } from 'primeng/inputtext';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { InventoryService, IRevisionListResult } from '../../services/inventory.service';
import {
  IItemRevision,
  IItemRevisionSummary,
  IRevisionCompare,
  RevisionType
} from '../../models/item-revision.model';

@Component({
  selector: 'app-revision-history',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TimelineModule,
    CardModule,
    ButtonModule,
    DialogModule,
    TagModule,
    TableModule,
    TooltipModule,
    SkeletonModule,
    InputTextModule,
    ConfirmDialogModule,
    ToastModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './revision-history.component.html',
  styleUrl: './revision-history.component.scss'
})
export class RevisionHistoryComponent implements OnInit, OnChanges {
  @Input() itemId: string = '';

  revisions: IItemRevisionSummary[] = [];
  loading: boolean = false;
  totalRevisions: number = 0;
  currentPage: number = 1;
  pageSize: number = 10;

  // Detail dialog
  displayDetailDialog: boolean = false;
  selectedRevision: IItemRevision | null = null;
  loadingDetail: boolean = false;

  // Compare dialog
  displayCompareDialog: boolean = false;
  compareResult: IRevisionCompare | null = null;
  loadingCompare: boolean = false;
  compareFromRev: number | null = null;
  compareToRev: number | null = null;

  // Restore dialog
  displayRestoreDialog: boolean = false;
  restoreReason: string = '';
  restoring: boolean = false;

  constructor(
    private inventoryService: InventoryService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    if (this.itemId) {
      this.loadRevisions();
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['itemId'] && !changes['itemId'].firstChange) {
      this.loadRevisions();
    }
  }

  loadRevisions() {
    if (!this.itemId) return;

    this.loading = true;
    this.inventoryService.getItemRevisions(this.itemId, this.currentPage, this.pageSize).subscribe({
      next: (result: IRevisionListResult) => {
        this.revisions = result.items;
        this.totalRevisions = result.pagination.totalItems;
        this.loading = false;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load revision history'
        });
        this.loading = false;
      }
    });
  }

  loadMore() {
    this.currentPage++;
    this.loading = true;
    this.inventoryService.getItemRevisions(this.itemId, this.currentPage, this.pageSize).subscribe({
      next: (result: IRevisionListResult) => {
        this.revisions = [...this.revisions, ...result.items];
        this.loading = false;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load more revisions'
        });
        this.currentPage--;
        this.loading = false;
      }
    });
  }

  viewRevisionDetail(revision: IItemRevisionSummary) {
    this.loadingDetail = true;
    this.displayDetailDialog = true;
    this.selectedRevision = null;

    this.inventoryService.getRevision(this.itemId, revision.revisionNumber).subscribe({
      next: (detail: IItemRevision) => {
        this.selectedRevision = detail;
        this.loadingDetail = false;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load revision details'
        });
        this.displayDetailDialog = false;
        this.loadingDetail = false;
      }
    });
  }

  openCompareDialog(revision: IItemRevisionSummary) {
    this.compareFromRev = revision.revisionNumber;
    this.compareToRev = null;
    this.compareResult = null;
    this.displayCompareDialog = true;
  }

  compareWithRevision(toRevisionNumber: number) {
    if (!this.compareFromRev) return;

    this.loadingCompare = true;
    this.inventoryService.compareRevisions(
      this.itemId,
      this.compareFromRev,
      toRevisionNumber
    ).subscribe({
      next: (result: IRevisionCompare) => {
        this.compareResult = result;
        this.compareToRev = toRevisionNumber;
        this.loadingCompare = false;
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to compare revisions'
        });
        this.loadingCompare = false;
      }
    });
  }

  openRestoreDialog(revision: IItemRevisionSummary) {
    this.selectedRevision = { revisionNumber: revision.revisionNumber } as IItemRevision;
    this.restoreReason = '';
    this.displayRestoreDialog = true;
  }

  confirmRestore() {
    if (!this.selectedRevision) return;

    this.confirmationService.confirm({
      message: `Are you sure you want to restore this item to revision ${this.selectedRevision.revisionNumber}? This will overwrite the current item data.`,
      header: 'Confirm Restore',
      icon: 'pi pi-exclamation-triangle',
      acceptButtonStyleClass: 'p-button-warning',
      accept: () => {
        this.executeRestore();
      }
    });
  }

  executeRestore() {
    if (!this.selectedRevision) return;

    this.restoring = true;
    this.inventoryService.restoreRevision(this.itemId, {
      revisionNumber: this.selectedRevision.revisionNumber,
      reason: this.restoreReason || undefined
    }).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: `Item restored to revision ${this.selectedRevision?.revisionNumber}`
        });
        this.displayRestoreDialog = false;
        this.restoring = false;
        this.loadRevisions(); // Reload to show new RESTORE revision
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to restore revision'
        });
        this.restoring = false;
      }
    });
  }

  // Helper methods
  getRevisionTypeIcon(type: RevisionType): string {
    const icons: Record<RevisionType, string> = {
      [RevisionType.CREATE]: 'pi pi-plus-circle',
      [RevisionType.UPDATE]: 'pi pi-pencil',
      [RevisionType.RESTORE]: 'pi pi-history'
    };
    return icons[type] || 'pi pi-circle';
  }

  getRevisionTypeColor(type: RevisionType): string {
    const colors: Record<RevisionType, string> = {
      [RevisionType.CREATE]: '#10B981',
      [RevisionType.UPDATE]: '#6366F1',
      [RevisionType.RESTORE]: '#F59E0B'
    };
    return colors[type] || '#64748B';
  }

  getRevisionTypeSeverity(type: RevisionType): 'success' | 'info' | 'warning' | 'danger' | 'secondary' {
    const severities: Record<RevisionType, 'success' | 'info' | 'warning' | 'danger' | 'secondary'> = {
      [RevisionType.CREATE]: 'success',
      [RevisionType.UPDATE]: 'info',
      [RevisionType.RESTORE]: 'warning'
    };
    return severities[type] || 'secondary';
  }

  getRevisionTypeLabel(type: RevisionType): string {
    const labels: Record<RevisionType, string> = {
      [RevisionType.CREATE]: 'Created',
      [RevisionType.UPDATE]: 'Updated',
      [RevisionType.RESTORE]: 'Restored'
    };
    return labels[type] || type;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  formatFieldName(field: string): string {
    // Convert camelCase or snake_case to Title Case
    return field
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .trim();
  }

  formatValue(value: any): string {
    if (value === null || value === undefined) {
      return '(empty)';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  }

  get hasMoreRevisions(): boolean {
    return this.revisions.length < this.totalRevisions;
  }

  getOtherRevisions(): IItemRevisionSummary[] {
    return this.revisions.filter(r => r.revisionNumber !== this.compareFromRev);
  }

  getChangedFields(): string[] {
    if (!this.compareResult?.differences) return [];
    return Object.keys(this.compareResult.differences);
  }
}
