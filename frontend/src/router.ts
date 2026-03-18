// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import DailyView from './pages/DailyView.vue'
import WeeklyView from './pages/WeeklyView.vue'
import PrepareSummary from './pages/PrepareSummary.vue'
import Tags from './pages/Tags.vue'
import Settings from './pages/Settings.vue'

const routes: RouteRecordRaw[] = [
  // Daily view — default landing and specific date
  { path: '/watch', component: DailyView, props: true },
  { path: '/watch/:date(\\d{4}-\\d{2}-\\d{2})', component: DailyView, props: true },

  // Weekly view
  { path: '/watch/week', component: WeeklyView, props: true },
  { path: '/watch/week/:week', component: WeeklyView, props: true },

  // Prepare summary (keyboard shortcut B)
  { path: '/watch/prepare', component: PrepareSummary },

  // Tag management
  { path: '/watch/tags', component: Tags },

  // Settings / preferences
  { path: '/watch/settings', component: Settings },

  // Fallback
  { path: '/:pathMatch(.*)*', redirect: '/watch' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
