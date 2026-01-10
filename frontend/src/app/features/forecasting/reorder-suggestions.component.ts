import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

import { ForecastingService, IReorderSuggestion } from '../../services/forecasting.service';

@Component({
  selector: 'app-reorder-suggestions',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    InputTextModule,
    DropdownModule,
    CardModule,
    TagModule,
    ProgressSpinnerModule,
    ToastModule,
  ],
  providers: [MessageService],
  templateUrl: './reorder-suggestions.component.html',
  styleUrls: ['./reorder-suggestions.component.scss'],
})
export class ReorderSuggestionsComponent implements OnInit {
  suggestions = signal<IReorderSuggestion[]>([]);
  isLoading = signal<boolean>(true);

  // Filters/controls
  leadTimeDays = 7;
  search = '';

  filtered = computed(() => {
    const q = this.search.trim().toLowerCase();
    const items = this.suggestions();
    if (!q) return items;
    return items.filter(
      (s) => s.sku.toLowerCase().includes(q) || (s.name || '').toLowerCase().includes(q)
    );
  });

  constructor(private forecastingService: ForecastingService, private messageService: MessageService) {}

  ngOnInit(): void {
    this.loadSuggestions();
  }

  loadSuggestions(): void {
    this.isLoading.set(true);
    this.forecastingService.getReorderSuggestions(this.leadTimeDays).subscribe({
      next: (data) => {
        this.suggestions.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to load suggestions' });
        this.isLoading.set(false);
      },
    });
  }

  refresh(): void {
    this.loadSuggestions();
  }
}
