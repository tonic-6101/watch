<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { __ } from '@/composables/useTranslate'
import { formatHours } from '@/composables/useEntries'

// ── Types ────────────────────────────────────────────────────────────────

export interface TagSegment {
  tag_name: string | null
  color:    string | null
  hours:    number
  pct:      number
}

// ── Props / emits ────────────────────────────────────────────────────────

const props = defineProps<{
  tags:        TagSegment[]
  totalHours:  number
}>()

const emit = defineEmits<{ clickTag: [tagName: string | null] }>()

// ── Donut geometry ───────────────────────────────────────────────────────

const CX = 80
const CY = 80
const R  = 54    // ring mid-radius
const SW = 22    // stroke-width → ring from R-SW/2 to R+SW/2
const CIRC = 2 * Math.PI * R  // ≈ 339.3

// Fallback palette when tag has no color
const PALETTE = [
  '#6366f1', '#f59e0b', '#10b981', '#ef4444',
  '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6',
]

function segmentColor(tag: TagSegment, idx: number): string {
  return tag.color || PALETTE[idx % PALETTE.length]
}

interface Segment {
  tag:          TagSegment
  color:        string
  dashArray:    string
  dashOffset:   number
}

const segments = computed<Segment[]>(() => {
  if (!props.totalHours) return []
  let offset = 0   // starts at 12-o-clock (we rotate SVG -90deg)
  return props.tags.map((tag, idx) => {
    const arc = (tag.hours / props.totalHours) * CIRC
    const seg: Segment = {
      tag,
      color:      segmentColor(tag, idx),
      dashArray:  `${arc.toFixed(2)} ${(CIRC - arc).toFixed(2)}`,
      dashOffset: -offset,
    }
    offset += arc
    return seg
  })
})

// ── Hover state ──────────────────────────────────────────────────────────

const hoveredIdx = ref<number | null>(null)
</script>

<template>
  <div class="flex items-start gap-4">

    <!-- SVG Donut -->
    <div class="relative shrink-0">
      <svg
        :viewBox="`0 0 ${CX * 2} ${CY * 2}`"
        width="160"
        height="160"
        class="rotate-[-90deg]"
        aria-hidden="true"
      >
        <!-- Background ring -->
        <circle
          :cx="CX" :cy="CY" :r="R"
          fill="none"
          stroke="#e5e7eb"
          :stroke-width="SW"
        />

        <!-- Empty state: single grey ring -->
        <template v-if="!totalHours">
          <circle
            :cx="CX" :cy="CY" :r="R"
            fill="none"
            stroke="#e5e7eb"
            :stroke-width="SW"
          />
        </template>

        <!-- Segments -->
        <circle
          v-for="(seg, idx) in segments"
          :key="idx"
          :cx="CX" :cy="CY" :r="R"
          fill="none"
          :stroke="seg.color"
          :stroke-width="hoveredIdx === idx ? SW + 4 : SW"
          :stroke-dasharray="seg.dashArray"
          :stroke-dashoffset="seg.dashOffset"
          class="cursor-pointer transition-all duration-150"
          @mouseenter="hoveredIdx = idx"
          @mouseleave="hoveredIdx = null"
          @click="emit('clickTag', seg.tag.tag_name)"
        >
          <title>{{ seg.tag.tag_name ?? __('Untagged') }}: {{ formatHours(seg.tag.hours) }}</title>
        </circle>
      </svg>

      <!-- Center label (not rotated) -->
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <span class="text-sm font-semibold text-gray-900 dark:text-slate-100 rotate-0">
          {{ totalHours ? formatHours(totalHours) : '—' }}
        </span>
      </div>
    </div>

    <!-- Legend -->
    <div class="flex-1 min-w-0 space-y-1.5 pt-1">
      <div
        v-if="!tags.length"
        class="text-xs text-gray-500 dark:text-slate-500 italic"
      >
        {{ __('No entries this week') }}
      </div>

      <button
        v-for="(seg, idx) in segments"
        :key="idx"
        type="button"
        class="w-full flex items-center gap-2 text-left group rounded px-1 py-0.5 transition-colors"
        :class="hoveredIdx === idx ? 'bg-gray-50 dark:bg-slate-800' : 'hover:bg-gray-50 dark:hover:bg-slate-800'"
        @mouseenter="hoveredIdx = idx"
        @mouseleave="hoveredIdx = null"
        @click="emit('clickTag', seg.tag.tag_name)"
      >
        <span
          class="w-2.5 h-2.5 rounded-full shrink-0"
          :style="{ backgroundColor: seg.color }"
        />
        <span class="flex-1 min-w-0 truncate text-xs text-gray-600 dark:text-slate-400">
          {{ seg.tag.tag_name ?? __('Untagged') }}
        </span>
        <span class="text-xs tabular-nums text-gray-500 dark:text-slate-500 shrink-0">
          {{ formatHours(seg.tag.hours) }}
        </span>
        <span class="text-xs tabular-nums text-gray-500 dark:text-slate-500 shrink-0 w-9 text-right">
          {{ seg.tag.pct }}%
        </span>
      </button>
    </div>

  </div>
</template>
