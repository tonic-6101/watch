<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'

const props = defineProps<{
  modelValue: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [tags: string[]]
}>()

const query      = ref('')
const suggestions = ref<string[]>([])
const showDropdown = ref(false)
const inputRef   = ref<HTMLInputElement | null>(null)

async function fetchSuggestions(q: string) {
  if (!q.trim()) { suggestions.value = []; return }
  try {
    const res = await fetch(
      `/api/method/watch.api.tag.get_tags?query=${encodeURIComponent(q)}`,
      { headers: { 'X-Frappe-CSRF-Token': (window as any).csrf_token ?? '' } },
    )
    const data = await res.json()
    const all: string[] = (data.message ?? []).map((t: any) => t.tag_name ?? t.name ?? t)
    suggestions.value = all.filter(t => !props.modelValue.includes(t))
  } catch {
    suggestions.value = []
  }
}

watch(query, (q) => {
  fetchSuggestions(q)
  showDropdown.value = q.length > 0
})

function addTag(tag: string) {
  if (!props.modelValue.includes(tag)) {
    emit('update:modelValue', [...props.modelValue, tag])
  }
  query.value       = ''
  suggestions.value = []
  showDropdown.value = false
  inputRef.value?.focus()
}

function addFromInput() {
  const t = query.value.trim()
  if (t) addTag(t)
}

function removeTag(tag: string) {
  emit('update:modelValue', props.modelValue.filter(t => t !== tag))
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Backspace' && !query.value && props.modelValue.length) {
    removeTag(props.modelValue[props.modelValue.length - 1])
  }
  if (e.key === 'Enter') {
    e.preventDefault()
    if (suggestions.value.length) addTag(suggestions.value[0])
    else addFromInput()
  }
  if (e.key === 'Escape') {
    showDropdown.value = false
    query.value = ''
  }
}
</script>

<template>
  <div class="relative">
    <!-- Chip row -->
    <div
      class="flex flex-wrap gap-1.5 items-center min-h-9 px-2 py-1.5 rounded-lg border
             border-[var(--watch-border)] bg-[var(--watch-bg)] cursor-text
             focus-within:ring-2 focus-within:ring-[var(--watch-primary)]/30
             focus-within:border-[var(--watch-primary)]"
      @click="inputRef?.focus()"
    >
      <!-- Existing tags -->
      <span
        v-for="tag in modelValue"
        :key="tag"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium
               bg-[var(--watch-primary-light)] text-[var(--watch-primary)]"
      >
        {{ tag }}
        <button
          type="button"
          class="flex items-center hover:opacity-70 transition-opacity"
          :aria-label="`${__('Remove')} ${tag}`"
          @click.stop="removeTag(tag)"
        >
          <X class="w-3 h-3" aria-hidden="true" />
        </button>
      </span>

      <!-- Input -->
      <input
        ref="inputRef"
        v-model="query"
        type="text"
        :placeholder="modelValue.length ? '' : __('Add tags…')"
        class="flex-1 min-w-[120px] bg-transparent text-sm outline-none
               text-[var(--watch-text)] placeholder-[var(--watch-text-muted)]"
        @keydown="onKeydown"
        @blur="() => setTimeout(() => { showDropdown = false }, 150)"
        @focus="() => { if (query) showDropdown = true }"
      />
    </div>

    <!-- Suggestions dropdown -->
    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <ul
        v-if="showDropdown && suggestions.length"
        class="absolute top-full left-0 right-0 mt-1 rounded-lg shadow-lg z-20
               border border-[var(--watch-border)] bg-[var(--watch-bg)]
               max-h-48 overflow-y-auto py-1"
        role="listbox"
      >
        <li
          v-for="suggestion in suggestions"
          :key="suggestion"
          class="px-3 py-2 text-sm text-[var(--watch-text)] cursor-pointer
                 hover:bg-[var(--watch-bg-secondary)] transition-colors"
          role="option"
          @mousedown.prevent="addTag(suggestion)"
        >
          {{ suggestion }}
        </li>
      </ul>
    </Transition>
  </div>
</template>
