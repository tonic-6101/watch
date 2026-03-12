// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

// ── Currency ─────────────────────────────────────────────────────────────
// Reads the site currency from frappe.boot.sysdefaults.currency (set at
// page load by Frappe).  Falls back to EUR so the UI is never broken.

function getSiteCurrency(): string {
  return (window as any).frappe?.boot?.sysdefaults?.currency ?? 'EUR'
}

/** ISO 4217 currency code for this site (e.g. "EUR", "CHF", "GBP"). */
export function useCurrency() {
  const code = getSiteCurrency()

  /**
   * Format a numeric amount with the site currency.
   * Uses the browser's Intl.NumberFormat to place the symbol correctly
   * for the current locale and currency (e.g. "1,234.00 €", "£1,234.00").
   */
  function formatAmount(amount: number): string {
    try {
      return new Intl.NumberFormat(undefined, {
        style:                 'currency',
        currency:              code,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(amount)
    } catch {
      // Unknown currency code — fall back to raw number + code
      return `${amount.toFixed(2)} ${code}`
    }
  }

  /**
   * Currency symbol only (e.g. "€", "£", "CHF").
   * Derived by formatting zero and extracting the currency part.
   */
  function currencySymbol(): string {
    try {
      const parts = new Intl.NumberFormat(undefined, {
        style:    'currency',
        currency: code,
      }).formatToParts(0)
      return parts.find(p => p.type === 'currency')?.value ?? code
    } catch {
      return code
    }
  }

  return { code, formatAmount, currencySymbol }
}
