<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { X } from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'

const props = defineProps<{
  modelValue: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [tags: string[]]
}>()

const query        = ref('')
const suggestions  = ref<string[]>([])
const showDropdown = ref(false)
const activeIndex  = ref(-1)   // -1 = nothing highlighted
const inputRef     = ref<HTMLInputElement | null>(null)
const listRef      = ref<HTMLUListElement | null>(null)

// Show "Create …" option when typed text doesn't exactly match any suggestion
const trimmedQuery = computed(() => query.value.trim())
const showCreateOption = computed(() => {
  if (!trimmedQuery.value) return false
  // Don't show if exact match already exists in suggestions
  const lower = trimmedQuery.value.toLowerCase()
  return !suggestions.value.some(s => s.toLowerCase() === lower)
})

// Total selectable items: suggestions + optional "create" row
const totalItems = computed(() => suggestions.value.length + (showCreateOption.value ? 1 : 0))
// The "create" row sits at this index
const createIndex = computed(() => showCreateOption.value ? suggestions.value.length : -1)

async function fetchSuggestions(q: string) {
  if (!q.trim()) { suggestions.value = []; return }
  try {
    const res = await fetch(
      `/api/method/watch.api.tags.get_tags?search=${encodeURIComponent(q)}`,
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
  activeIndex.value = -1   // reset selection on every keystroke
  fetchSuggestions(q)
  showDropdown.value = q.trim().length > 0
})

function addTag(tag: string) {
  const t = tag.trim()
  if (!t) return
  if (!props.modelValue.includes(t)) {
    emit('update:modelValue', [...props.modelValue, t])
  }
  query.value        = ''
  suggestions.value  = []
  showDropdown.value = false
  activeIndex.value  = -1
  inputRef.value?.focus()
}

function removeTag(tag: string) {
  emit('update:modelValue', props.modelValue.filter(t => t !== tag))
}

function onBlur() {
  setTimeout(() => {
    showDropdown.value = false
    activeIndex.value  = -1
  }, 150)
}

function scrollToActive() {
  if (!listRef.value || activeIndex.value < 0) return
  const item = listRef.value.children[activeIndex.value] as HTMLElement | undefined
  item?.scrollIntoView({ block: 'nearest' })
}

function onKeydown(e: KeyboardEvent) {
  // Backspace removes last tag when input is empty
  if (e.key === 'Backspace' && !query.value && props.modelValue.length) {
    removeTag(props.modelValue[props.modelValue.length - 1])
    return
  }

  // Arrow down
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (!showDropdown.value && trimmedQuery.value) {
      showDropdown.value = true
      return
    }
    if (totalItems.value > 0) {
      activeIndex.value = activeIndex.value < totalItems.value - 1 ? activeIndex.value + 1 : 0
      scrollToActive()
    }
    return
  }

  // Arrow up
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (totalItems.value > 0) {
      activeIndex.value = activeIndex.value > 0 ? activeIndex.value - 1 : totalItems.value - 1
      scrollToActive()
    }
    return
  }

  // Enter — add highlighted item, or create from input if nothing highlighted
  if (e.key === 'Enter') {
    e.preventDefault()
    if (activeIndex.value >= 0 && activeIndex.value < suggestions.value.length) {
      // User explicitly navigated to a suggestion → use it
      addTag(suggestions.value[activeIndex.value])
    } else if (activeIndex.value === createIndex.value && createIndex.value >= 0) {
      // User navigated to "Create …" row
      addTag(trimmedQuery.value)
    } else {
      // Nothing highlighted → create what the user typed
      addTag(trimmedQuery.value)
    }
    return
  }

  // Tab — accept highlighted suggestion if any, otherwise let browser handle
  if (e.key === 'Tab' && showDropdown.value && activeIndex.value >= 0) {
    e.preventDefault()
    if (activeIndex.value < suggestions.value.length) {
      addTag(suggestions.value[activeIndex.value])
    } else if (activeIndex.value === createIndex.value) {
      addTag(trimmedQuery.value)
    }
    return
  }

  if (e.key === 'Escape') {
    showDropdown.value = false
    activeIndex.value  = -1
    query.value        = ''
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
        @blur="onBlur"
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
        v-if="showDropdown && (suggestions.length || showCreateOption)"
        ref="listRef"
        class="absolute top-full left-0 right-0 mt-1 rounded-lg shadow-lg z-20
               border border-[var(--watch-border)] bg-[var(--watch-bg)]
               max-h-48 overflow-y-auto py-1"
        role="listbox"
      >
        <li
          v-for="(suggestion, idx) in suggestions"
          :key="suggestion"
          :class="[
            'px-3 py-2 text-sm text-[var(--watch-text)] cursor-pointer transition-colors',
            idx === activeIndex
              ? 'bg-[var(--watch-primary-light)] text-[var(--watch-primary)]'
              : 'hover:bg-[var(--watch-bg-secondary)]',
          ]"
          role="option"
          :aria-selected="idx === activeIndex"
          @mousedown.prevent="addTag(suggestion)"
          @mouseenter="activeIndex = idx"
        >
          {{ suggestion }}
        </li>
        <!-- "Create new tag" option -->
        <li
          v-if="showCreateOption"
          :class="[
            'px-3 py-2 text-sm cursor-pointer transition-colors border-t border-[var(--watch-border)] flex items-center gap-1.5',
            activeIndex === createIndex
              ? 'bg-[var(--watch-primary-light)] text-[var(--watch-primary)]'
              : 'text-[var(--watch-text-muted)] hover:bg-[var(--watch-bg-secondary)] hover:text-[var(--watch-text)]',
          ]"
          role="option"
          :aria-selected="activeIndex === createIndex"
          @mousedown.prevent="addTag(trimmedQuery)"
          @mouseenter="activeIndex = createIndex"
        >
          <span class="text-xs">+</span>
          {{ __('Create') }} "<span class="font-medium text-[var(--watch-text)]">{{ trimmedQuery }}</span>"
        </li>
      </ul>
    </Transition>
  </div>
</template>
