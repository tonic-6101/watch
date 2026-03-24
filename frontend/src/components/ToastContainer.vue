<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { X } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'

const { toasts, dismiss } = useToast()
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none"
      aria-live="polite"
    >
      <TransitionGroup
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0 translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0 translate-y-2"
      >
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="pointer-events-auto flex items-center gap-3
                 bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-700
                 rounded-xl shadow-lg px-4 py-3 max-w-sm"
        >
          <span class="text-sm text-gray-900 dark:text-slate-100 flex-1">
            {{ toast.message }}
          </span>
          <button
            v-if="toast.action"
            type="button"
            class="text-xs text-[var(--app-accent-500)] hover:underline shrink-0 font-medium"
            @click="toast.action.handler(); dismiss(toast.id)"
          >
            {{ toast.action.label }}
          </button>
          <button
            type="button"
            class="p-0.5 rounded text-gray-500 dark:text-slate-500 hover:text-gray-900 dark:hover:text-slate-100
                   transition-colors shrink-0"
            @click="dismiss(toast.id)"
          >
            <X class="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
