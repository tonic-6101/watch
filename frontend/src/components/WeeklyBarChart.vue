<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { __ } from '@/composables/useTranslate'

// ── Types ────────────────────────────────────────────────────────────────

export interface DailyBar {
  day:         string
  label:       string
  hours:       number
  is_work_day: boolean
}

// ── Props / emits ────────────────────────────────────────────────────────

const props = defineProps<{
  daily:           DailyBar[]
  targetHoursPerDay?: number   // dashed target line (Feature 18); undefined = no line
}>()

const emit = defineEmits<{ clickDay: [day: string] }>()

// ── Chart geometry ───────────────────────────────────────────────────────

const W      = 280   // viewBox width
const H      = 150   // viewBox height
const PAD_L  = 28    // left padding for Y-axis labels
const PAD_B  = 20    // bottom for X-axis labels
const PAD_T  = 8     // top padding
const PAD_R  = 8

const chartW = W - PAD_L - PAD_R
const chartH = H - PAD_B - PAD_T

const BAR_GAP = 4   // px between bars

// ── Y scale ──────────────────────────────────────────────────────────────

const maxHours = computed(() => {
  const maxData = Math.max(0, ...props.daily.map(d => d.hours))
  return Math.max(4, Math.ceil(maxData))   // minimum ceiling 4h
})

function yPx(hours: number): number {
  return chartH - (hours / maxHours.value) * chartH
}

// Y-axis tick values (0, maxHours/2, maxHours)
const yTicks = computed(() => [
  maxHours.value,
  Math.round(maxHours.value / 2),
  0,
])

// ── Bar geometry ─────────────────────────────────────────────────────────

const barWidth = computed(() =>
  Math.max(4, (chartW - BAR_GAP * (props.daily.length - 1)) / props.daily.length)
)

function barX(idx: number): number {
  return PAD_L + idx * (barWidth.value + BAR_GAP)
}

function barY(hours: number): number {
  return PAD_T + yPx(hours)
}

function barH(hours: number): number {
  return chartH - yPx(hours)
}

// ── Hover / tooltip ──────────────────────────────────────────────────────

const hoveredIdx = ref<number | null>(null)

function tooltipLabel(d: DailyBar): string {
  if (!d.hours) return __('No entries')
  const h = Math.floor(d.hours)
  const m = Math.round((d.hours - h) * 60)
  return m > 0 ? `${h}h ${m}m` : `${h}h`
}

// Tooltip X position: clamp so it doesn't go outside the SVG
function tipX(idx: number): number {
  const x = barX(idx) + barWidth.value / 2
  return Math.min(W - 40, Math.max(20, x))
}
</script>

<template>
  <div class="relative">
    <svg
      :viewBox="`0 0 ${W} ${H}`"
      :width="W"
      :height="H"
      class="w-full"
      overflow="visible"
      aria-hidden="true"
    >
      <!-- Y-axis gridlines + labels -->
      <g v-for="tick in yTicks" :key="tick">
        <line
          :x1="PAD_L"
          :y1="PAD_T + yPx(tick)"
          :x2="W - PAD_R"
          :y2="PAD_T + yPx(tick)"
          stroke="#e5e7eb"
          stroke-width="0.5"
        />
        <text
          :x="PAD_L - 4"
          :y="PAD_T + yPx(tick) + 3"
          text-anchor="end"
          font-size="8"
          fill="#6b7280"
        >{{ tick }}</text>
      </g>

      <!-- Daily target line (Feature 18 — only when target is set) -->
      <line
        v-if="targetHoursPerDay && targetHoursPerDay > 0 && targetHoursPerDay <= maxHours"
        :x1="PAD_L"
        :y1="PAD_T + yPx(targetHoursPerDay)"
        :x2="W - PAD_R"
        :y2="PAD_T + yPx(targetHoursPerDay)"
        stroke="var(--app-accent-500)"
        stroke-width="1"
        stroke-dasharray="4 3"
        opacity="0.6"
      />

      <!-- Bars -->
      <g
        v-for="(d, idx) in daily"
        :key="d.day"
        class="cursor-pointer"
        @mouseenter="hoveredIdx = idx"
        @mouseleave="hoveredIdx = null"
        @click="emit('clickDay', d.day)"
      >
        <!-- Hit area (full column height for easy hover) -->
        <rect
          :x="barX(idx)"
          :y="PAD_T"
          :width="barWidth"
          :height="chartH"
          fill="transparent"
        />

        <!-- Bar (only drawn when hours > 0) -->
        <rect
          v-if="d.hours > 0"
          :x="barX(idx)"
          :y="barY(d.hours)"
          :width="barWidth"
          :height="barH(d.hours)"
          :rx="2"
          :fill="d.is_work_day ? 'var(--app-accent-500)' : '#6b7280'"
          :opacity="hoveredIdx === idx ? 1 : 0.75"
          class="transition-opacity duration-100"
        />

        <!-- X-axis label -->
        <text
          :x="barX(idx) + barWidth / 2"
          :y="H - 4"
          text-anchor="middle"
          font-size="8"
          :fill="hoveredIdx === idx ? '#111827' : '#6b7280'"
        >{{ d.label }}</text>

        <!-- Tooltip -->
        <g v-if="hoveredIdx === idx">
          <rect
            :x="tipX(idx) - 18"
            :y="barY(Math.max(d.hours, 0.5)) - 20"
            width="36"
            height="14"
            rx="3"
            fill="#111827"
            opacity="0.88"
          />
          <text
            :x="tipX(idx)"
            :y="barY(Math.max(d.hours, 0.5)) - 9"
            text-anchor="middle"
            font-size="8"
            fill="#ffffff"
            font-weight="500"
          >{{ tooltipLabel(d) }}</text>
        </g>
      </g>
    </svg>
  </div>
</template>
