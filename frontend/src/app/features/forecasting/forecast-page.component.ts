import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

// PrimeNG
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { InputNumberModule } from 'primeng/inputnumber';
import { DropdownModule } from 'primeng/dropdown';
import { TableModule } from 'primeng/table';
import { AutoCompleteModule, AutoCompleteCompleteEvent } from 'primeng/autocomplete';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

import { ForecastingService, IDailyForecast } from '../../services/forecasting.service';
import { InventoryService } from '../../services/inventory.service';
import { IInventoryItem } from '../../models/inventory-item.model';
import { ReorderSuggestionsComponent } from './reorder-suggestions.component';

@Component({
  selector: 'app-forecast-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    InputNumberModule,
    DropdownModule,
    TableModule,
    AutoCompleteModule,
    ProgressSpinnerModule,
    ToastModule,
    ReorderSuggestionsComponent,
  ],
  providers: [MessageService],
  templateUrl: './forecast-page.component.html',
  styleUrls: ['./forecast-page.component.scss'],
})
export class ForecastPageComponent {
  // Item selection
  selectedItem: IInventoryItem | null = null;
  itemResults: IInventoryItem[] = [];

  // Forecast parameters
  method: 'moving_average' | 'exp_smoothing' = 'moving_average';
  windowSize = 7;
  periods = 14;
  alpha = 0.3;

  // State
  forecasts = signal<IDailyForecast[] | null>(null);
  loading = signal(false);

  methodOptions = [
    { label: 'Moving Average', value: 'moving_average' },
    { label: 'Exponential Smoothing', value: 'exp_smoothing' },
  ];

  constructor(
    private forecastingService: ForecastingService,
    private inventoryService: InventoryService,
    private messageService: MessageService
  ) {}

  searchItems(event: AutoCompleteCompleteEvent): void {
    const query = (event.query || '').trim();
    if (!query) {
      this.itemResults = [];
      return;
    }
    this.inventoryService.getItems(1, 10, { search: query }).subscribe({
      next: (res) => (this.itemResults = res.items),
      error: () => (this.itemResults = []),
    });
  }

  runForecast(): void {
    if (!this.selectedItem) {
      this.messageService.add({ severity: 'warn', summary: 'Select Item', detail: 'Choose an item to forecast.' });
      return;
    }
    this.loading.set(true);
    const itemId = this.selectedItem.id;
    const done = () => this.loading.set(false);
    if (this.method === 'moving_average') {
      this.forecastingService.runMovingAverage(itemId, this.windowSize, this.periods).subscribe({
        next: (data) => {
          this.forecasts.set(data);
          done();
        },
        error: () => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to compute forecast' });
          done();
        },
      });
    } else {
      this.forecastingService.runExpSmoothing(itemId, this.windowSize, this.periods, this.alpha).subscribe({
        next: (data) => {
          this.forecasts.set(data);
          done();
        },
        error: () => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to compute forecast' });
          done();
        },
      });
    }
  }
}
