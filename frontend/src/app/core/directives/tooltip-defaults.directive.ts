import { Directive, Input, OnInit } from '@angular/core';
import { Tooltip } from 'primeng/tooltip';

/**
 * Directive to set default tooltip position to 'left' to prevent
 * tooltips from being cut off at the edge of the viewport.
 * 
 * This directive automatically applies to all elements with pTooltip
 * and sets a sensible default position. Individual tooltips can still
 * override this by setting tooltipPosition explicitly.
 */
@Directive({
  selector: '[pTooltip]',
  standalone: true
})
export class TooltipDefaultsDirective implements OnInit {
  @Input() tooltipPosition?: string;

  constructor(private tooltip: Tooltip) {}

  ngOnInit() {
    // Only set default if position wasn't explicitly specified
    if (!this.tooltipPosition) {
      this.tooltip.tooltipPosition = 'left';
    }
  }
}
