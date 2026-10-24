import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FEATURES, Feature, MODEL_VERSION, SAMPLE_RECORD } from './feature-schema';
import { PredictionService, PredictionResponse } from './prediction.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  readonly fields = FEATURES;
  readonly modelVersion = MODEL_VERSION;
  readonly groups = [...new Set(FEATURES.map(f => f.group))]
    .map(name => ({ name, fields: FEATURES.filter(f => f.group === name) }));
  readonly deployedStatic = !['localhost', '127.0.0.1']
    .includes(window.location.hostname);
  values: Record<string, string | number | null> = {};
  // Signals so the zoneless Angular 22 app re-renders when the HTTP response arrives
  readonly loading = signal(false);
  readonly error = signal('');
  readonly result = signal<PredictionResponse | null>(null);
  private api = inject(PredictionService);

  constructor() {
    this.clear();
  }

  clear() {
    for (const field of this.fields) this.values[field.name] = null;
    this.error.set(''); this.result.set(null);
  }

  loadSample() {
    this.values = { ...SAMPLE_RECORD };
    this.error.set(''); this.result.set(null);
  }

  hint(field: Feature) {
    if (field.kind === 'category') return `${field.options?.length ?? 0} options`;
    return field.max !== undefined ? `${field.min ?? 0} – ${field.max}` : `≥ ${field.min ?? 0}`;
  }

  percent(p: number) { return `${(p * 100).toFixed(1)}%`; }

  submit() {
    this.error.set(''); this.result.set(null);
    if (this.deployedStatic) {
      this.error.set('Static GitHub Pages demo: start Angular + Flask locally for predictions.');
      return;
    }
    const payload: Record<string, string | number> = {};
    for (const field of this.fields) {
      const value = this.values[field.name];
      if (value === null || value === undefined || value === '') {
        this.error.set(`Enter a value for ${field.label}`); return;
      }
      if (field.kind === 'number') {
        const numeric = Number(value);
        if (!Number.isFinite(numeric)) {
          this.error.set(`Invalid number for ${field.label}`); return;
        }
        if ((field.min !== undefined && numeric < field.min) ||
            (field.max !== undefined && numeric > field.max)) {
          this.error.set(`Out-of-range value for ${field.label} (${this.hint(field)})`); return;
        }
        payload[field.name] = numeric;
      } else {
        if (!field.options?.includes(String(value))) {
          this.error.set(`Choose a valid option for ${field.label}`); return;
        }
        payload[field.name] = String(value);
      }
    }
    this.loading.set(true);
    this.api.predict(payload).subscribe({
      next: result => { this.result.set(result); this.loading.set(false); },
      error: err => {
        const detail = err.error?.detail;
        this.error.set(`API error ${err.status || ''}: ` +
          (err.error?.error || err.message || 'Check Flask terminal') +
          (Array.isArray(detail) ? ` — ${detail.join('; ')}` : ''));
        this.loading.set(false);
      },
    });
  }
}
