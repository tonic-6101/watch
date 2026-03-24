import { h as Q, ref as i, defineComponent as fe, onMounted as me, computed as we, openBlock as c, createElementBlock as u, createElementVNode as e, toDisplayString as o, unref as a, Fragment as h, renderList as R, withDirectives as g, vModelText as k, createCommentVNode as y, normalizeClass as F, vModelSelect as Z, createTextVNode as se, createVNode as oe } from "/assets/dock/js/vendor/vue.esm.js";
const Se = (p) => p.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
var X = {
  xmlns: "http://www.w3.org/2000/svg",
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": 2,
  "stroke-linecap": "round",
  "stroke-linejoin": "round"
};
const Te = ({ size: p, strokeWidth: d = 2, absoluteStrokeWidth: v, color: x, iconNode: b, name: _, class: ee, ...Y }, { slots: U }) => Q(
  "svg",
  {
    ...X,
    width: p || X.width,
    height: p || X.height,
    stroke: x || X.stroke,
    "stroke-width": v ? Number(d) * 24 / Number(p) : d,
    class: ["lucide", `lucide-${Se(_ ?? "icon")}`],
    ...Y
  },
  [...b.map((B) => Q(...B)), ...U.default ? [U.default()] : []]
);
const re = (p, d) => (v, { slots: x }) => Q(
  Te,
  {
    ...v,
    iconNode: d,
    name: p
  },
  x
);
const Ce = re("ChevronDownIcon", [
  ["path", { d: "m6 9 6 6 6-6", key: "qrunsl" }]
]);
const Ee = re("DownloadIcon", [
  ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", key: "ih7n3h" }],
  ["polyline", { points: "7 10 12 15 17 10", key: "2ggqvy" }],
  ["line", { x1: "12", x2: "12", y1: "15", y2: "3", key: "1vk2je" }]
]);
function s(p, d) {
  let x = (window.__messages || {})[p] || p;
  if (d)
    if (Array.isArray(d))
      for (let b = 0; b < d.length; b++)
        x = x.replace(new RegExp(`\\{${b}\\}`, "g"), String(d[b]));
    else
      for (const [b, _] of Object.entries(d))
        x = x.replace(new RegExp(`\\{${b}\\}`, "g"), String(_));
  return x;
}
const S = i({
  weekly_hour_target: 0,
  enable_keyboard_shortcuts: 1,
  focus_work_minutes: 25,
  focus_break_minutes: 5,
  focus_sessions: 4,
  extension_token_active: 0
}), le = i(!1), D = i(!1);
async function Pe() {
  D.value = !0;
  try {
    const p = await fetch("/api/method/watch.api.user_settings.get_preferences", {
      headers: { "X-Frappe-CSRF-Token": window.csrf_token ?? "" }
    }), d = await p.json();
    if (!p.ok || d.exc) throw new Error(d.exc ?? "Load failed");
    return Object.assign(S.value, d.message), le.value = !0, S.value;
  } finally {
    D.value = !1;
  }
}
async function je(p) {
  D.value = !0;
  try {
    const d = await fetch("/api/method/watch.api.user_settings.save_preferences", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": window.csrf_token ?? ""
      },
      body: JSON.stringify(p)
    }), v = await d.json();
    if (!d.ok || v.exc) throw new Error(v.exc ?? "Save failed");
    return Object.assign(S.value, v.message), S.value;
  } finally {
    D.value = !1;
  }
}
async function Re() {
  const p = await fetch("/api/method/watch.api.user_settings.generate_extension_token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": window.csrf_token ?? ""
    }
  }), d = await p.json();
  if (!p.ok || d.exc) throw new Error(d.exc ?? "Token generation failed");
  return S.value.extension_token_active = 1, d.message.token;
}
async function Oe() {
  const p = await fetch("/api/method/watch.api.user_settings.revoke_extension_token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": window.csrf_token ?? ""
    }
  }), d = await p.json();
  if (!p.ok || d.exc) throw new Error(d.exc ?? "Token revocation failed");
  S.value.extension_token_active = 0;
}
function Ne() {
  return { prefs: S, loaded: le, loading: D, load: Pe, save: je, generateExtensionToken: Re, revokeExtensionToken: Oe };
}
const Ve = { class: "min-h-screen bg-gray-50 dark:bg-slate-800" }, Fe = { class: "max-w-2xl mx-auto px-4 py-6 space-y-4" }, De = { class: "text-lg font-semibold text-gray-900 dark:text-slate-100" }, Ue = {
  key: 1,
  class: "text-sm text-red-500 px-1"
}, Le = { class: "bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700" }, $e = { class: "px-4 py-3" }, Ie = { class: "text-sm font-semibold text-gray-900 dark:text-slate-100" }, Me = { class: "text-xs text-gray-500 dark:text-slate-500 mt-0.5" }, We = { class: "px-4 py-3 flex items-center gap-4" }, Ae = { class: "flex-1" }, Ge = { class: "text-sm text-gray-900 dark:text-slate-100" }, Xe = { class: "text-xs text-gray-500 dark:text-slate-500" }, Ye = { class: "flex items-center gap-1.5" }, Be = { class: "text-xs text-gray-500 dark:text-slate-500" }, He = { class: "px-4 py-3 flex items-center gap-4" }, Ke = { class: "text-sm text-gray-900 dark:text-slate-100 flex-1" }, qe = { class: "flex items-center gap-2 cursor-pointer shrink-0" }, Je = ["checked"], ze = { class: "text-sm text-gray-900 dark:text-slate-100" }, Ze = { class: "px-4 py-3 flex items-center gap-3 justify-end" }, Qe = {
  key: 0,
  class: "text-xs text-red-500 flex-1"
}, et = {
  key: 1,
  class: "text-xs text-green-600 dark:text-green-400 flex-1"
}, tt = ["disabled"], at = { class: "bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700" }, st = { class: "px-4 py-3" }, ot = { class: "text-sm font-semibold text-gray-900 dark:text-slate-100" }, rt = { class: "text-xs text-gray-500 dark:text-slate-500 mt-0.5" }, lt = { class: "px-4 py-3 space-y-3" }, nt = { class: "flex items-center gap-2" }, dt = { class: "text-sm text-gray-500 dark:text-slate-500" }, it = {
  key: 0,
  class: "space-y-2"
}, ct = { class: "flex items-center gap-2" }, ut = ["value"], pt = { class: "text-xs text-amber-600 dark:text-amber-400" }, xt = {
  key: 1,
  class: "text-xs text-red-500"
}, _t = { class: "flex items-center gap-2" }, gt = ["disabled"], vt = ["disabled"], bt = ["disabled"], yt = { class: "bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700" }, kt = { class: "px-4 py-3" }, ht = { class: "text-sm font-semibold text-gray-900 dark:text-slate-100" }, ft = { class: "px-4 py-3 flex items-center gap-4" }, mt = { class: "text-sm text-gray-900 dark:text-slate-100 flex-1" }, wt = ["value"], St = { class: "px-4 py-3 flex items-center gap-4" }, Tt = { class: "flex-1" }, Ct = { class: "text-sm text-gray-900 dark:text-slate-100" }, Et = { class: "text-xs text-gray-500 dark:text-slate-500" }, Pt = { class: "px-4 py-3 flex items-center gap-4" }, jt = { class: "flex-1" }, Rt = { class: "text-sm text-gray-900 dark:text-slate-100" }, Ot = { class: "text-xs text-gray-500 dark:text-slate-500" }, Nt = { class: "px-4 py-3 space-y-2" }, Vt = { class: "text-sm text-gray-900 dark:text-slate-100" }, Ft = { class: "flex gap-4" }, Dt = ["checked", "onChange"], Ut = { class: "text-xs text-gray-500 dark:text-slate-500 select-none" }, Lt = { class: "bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700" }, $t = { class: "px-4 py-3 flex items-center gap-4" }, It = { class: "flex-1" }, Mt = { class: "text-sm font-semibold text-gray-900 dark:text-slate-100" }, Wt = { class: "text-xs text-gray-500 dark:text-slate-500" }, At = { class: "flex items-center gap-2 cursor-pointer shrink-0" }, Gt = ["checked"], Xt = { class: "text-sm text-gray-900 dark:text-slate-100" }, Yt = { class: "px-4 py-3 flex items-center gap-4" }, Bt = { class: "text-sm text-gray-900 dark:text-slate-100 flex-1" }, Ht = { class: "px-4 py-3 flex items-center gap-4" }, Kt = { class: "text-sm text-gray-900 dark:text-slate-100 flex-1" }, qt = ["value"], Jt = {
  key: 0,
  class: "px-4 py-3 flex items-center gap-4"
}, zt = { class: "text-sm text-gray-900 dark:text-slate-100 flex-1" }, Zt = ["value"], Qt = { class: "px-4 py-3 flex items-center gap-4" }, ea = { class: "text-sm text-gray-900 dark:text-slate-100 flex-1" }, ta = { class: "px-4 py-3 flex items-center gap-4" }, aa = { class: "text-sm text-gray-900 dark:text-slate-100 flex-1" }, sa = ["checked"], oa = { class: "px-4 py-3 flex items-center gap-4" }, ra = { class: "text-sm text-gray-900 dark:text-slate-100 flex-1" }, la = ["checked"], na = { class: "bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700" }, da = { class: "px-4 py-3" }, ia = { class: "text-sm font-semibold text-gray-900 dark:text-slate-100" }, ca = { class: "text-xs text-gray-500 dark:text-slate-500 mt-0.5" }, ua = { class: "px-4 py-3 space-y-3" }, pa = { class: "text-xs font-semibold text-gray-500 dark:text-slate-500 uppercase tracking-wide" }, xa = { class: "flex items-center gap-3" }, _a = { class: "text-sm text-gray-900 dark:text-slate-100 w-32 shrink-0" }, ga = ["disabled"], va = { class: "flex items-center gap-4" }, ba = { class: "flex items-center gap-2 cursor-pointer" }, ya = ["checked"], ka = { class: "text-sm text-gray-900 dark:text-slate-100" }, ha = { class: "flex flex-col gap-1" }, fa = { class: "text-xs text-gray-500 dark:text-slate-500" }, ma = { class: "px-4 py-3 space-y-3" }, wa = { class: "text-xs font-semibold text-gray-500 dark:text-slate-500 uppercase tracking-wide" }, Sa = { class: "flex items-center gap-3" }, Ta = { class: "text-sm text-gray-900 dark:text-slate-100 w-32 shrink-0" }, Ca = ["disabled"], Ea = { class: "flex items-center gap-4" }, Pa = { class: "flex items-center gap-2 cursor-pointer" }, ja = ["checked"], Ra = { class: "text-sm text-gray-900 dark:text-slate-100" }, Oa = { class: "px-4 py-3 space-y-3" }, Na = { class: "text-xs font-semibold text-gray-500 dark:text-slate-500 uppercase tracking-wide" }, Va = { class: "flex items-center gap-3" }, Fa = { class: "text-sm text-gray-900 dark:text-slate-100 w-32 shrink-0" }, Da = ["disabled"], Ua = { class: "flex items-center gap-3" }, La = { class: "text-sm text-gray-900 dark:text-slate-100 w-32 shrink-0" }, $a = { class: "flex items-center gap-4" }, Ia = { class: "flex items-center gap-2 cursor-pointer" }, Ma = ["checked"], Wa = { class: "text-sm text-gray-900 dark:text-slate-100" }, Aa = { class: "bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden divide-y divide-gray-200 dark:divide-slate-700" }, Ga = { class: "px-4 py-3" }, Xa = { class: "text-sm font-semibold text-gray-900 dark:text-slate-100" }, Ya = { class: "text-xs text-gray-500 dark:text-slate-500 mt-0.5" }, Ba = { class: "px-4 py-3 flex flex-wrap items-center gap-2" }, Ha = { class: "relative" }, Ka = {
  key: 0,
  class: "absolute left-0 top-full mt-1 z-20 bg-white dark:bg-slate-950 border border-gray-200 dark:border-slate-700 rounded-xl shadow-lg py-1 min-w-[140px]"
}, qa = ["onClick"], Ja = ["max"], za = ["min"], Za = ["disabled"], Qa = {
  key: 0,
  class: "text-sm text-red-500 px-1"
}, es = {
  key: 1,
  class: "text-sm text-green-600 dark:text-green-400 px-1"
}, ts = { class: "flex justify-end" }, as = ["disabled"], os = /* @__PURE__ */ fe({
  __name: "Settings",
  setup(p) {
    const d = i(!0), v = i(!1), x = i(null), b = i(!1), {
      prefs: _,
      load: ee,
      save: Y,
      generateExtensionToken: U,
      revokeExtensionToken: B
    } = Ne(), L = i(!1), $ = i(!1), O = i(null), T = i(!1), I = i(!1), m = i(null), C = i(null), H = i(!1);
    async function te() {
      if (!(_.value.extension_token_active && !window.confirm(s("This will revoke the existing token. Continue?")))) {
        T.value = !0, C.value = null, m.value = null;
        try {
          const n = await U();
          m.value = n;
        } catch (n) {
          C.value = n.message;
        } finally {
          T.value = !1;
        }
      }
    }
    async function ne() {
      I.value = !0, C.value = null, m.value = null;
      try {
        await B();
      } catch (n) {
        C.value = n.message;
      } finally {
        I.value = !1;
      }
    }
    async function de() {
      if (m.value)
        try {
          await navigator.clipboard.writeText(m.value), H.value = !0, setTimeout(() => {
            H.value = !1;
          }, 2e3);
        } catch {
        }
    }
    async function ie() {
      L.value = !0, O.value = null, $.value = !1;
      try {
        await Y({
          weekly_hour_target: _.value.weekly_hour_target,
          enable_keyboard_shortcuts: _.value.enable_keyboard_shortcuts,
          focus_work_minutes: _.value.focus_work_minutes,
          focus_break_minutes: _.value.focus_break_minutes,
          focus_sessions: _.value.focus_sessions
        }), $.value = !0, setTimeout(() => {
          $.value = !1;
        }, 2500);
      } catch (n) {
        O.value = n.message;
      } finally {
        L.value = !1;
      }
    }
    const l = i({
      default_entry_type: "billable",
      lock_entries_older_than: 0,
      auto_stop_timer_after: 8,
      work_mon: 1,
      work_tue: 1,
      work_wed: 1,
      work_thu: 1,
      work_fri: 1,
      work_sat: 0,
      work_sun: 0,
      enable_erpnext_bridge: 0,
      sync_mode: "on_save",
      sync_interval: "",
      erpnext_site_url: "",
      default_activity_type: "",
      sync_billable_only: 0,
      map_project_tags: 0,
      slack_webhook_url: "",
      slack_notify_on_stop: 1,
      slack_message_template: "",
      linear_api_key: "",
      linear_post_comment: 0,
      github_token: "",
      github_default_repo: "",
      github_post_comment: 0
    });
    me(async () => {
      const [, n] = await Promise.allSettled([
        (async () => {
          try {
            const r = await fetch("/api/method/watch.api.settings.get_settings", {
              headers: { "X-Frappe-CSRF-Token": window.csrf_token ?? "" }
            }), t = await r.json();
            if (!r.ok || t.exc) throw new Error(t.exc ?? "Load failed");
            Object.assign(l.value, t.message);
          } catch (r) {
            x.value = r.message;
          } finally {
            d.value = !1;
          }
        })(),
        ee()
      ]);
      n.status === "rejected" && (O.value = n.reason?.message ?? "Failed to load preferences");
    });
    async function ce() {
      v.value = !0, x.value = null, b.value = !1;
      try {
        const n = await fetch("/api/method/watch.api.settings.save_settings", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Frappe-CSRF-Token": window.csrf_token ?? ""
          },
          body: JSON.stringify(l.value)
        }), r = await n.json();
        if (!n.ok || r.exc) throw new Error(r.exc ?? "Save failed");
        Object.assign(l.value, r.message), b.value = !0, setTimeout(() => {
          b.value = !1;
        }, 2500);
      } catch (n) {
        x.value = n.message;
      } finally {
        v.value = !1;
      }
    }
    const K = i(!1), M = i(null), q = i(!1), W = i(null), J = i(!1), A = i(null);
    async function z(n, r, t, f) {
      r.value = !0, t.value = null;
      try {
        const j = await fetch(`/api/method/${n}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Frappe-CSRF-Token": window.csrf_token ?? ""
          }
        }), w = await j.json();
        if (!j.ok || w.exc) throw new Error(w._server_messages || w.exc || "Test failed");
        t.value = f(w.message);
      } catch (j) {
        t.value = `Error: ${j.message}`;
      } finally {
        r.value = !1;
      }
    }
    function ue() {
      z("watch.api.integrations.test_slack", K, M, () => s("Connected"));
    }
    function pe() {
      z(
        "watch.api.integrations.test_linear",
        q,
        W,
        (n) => s("Connected") + (n?.workspace ? ` (${n.workspace})` : "")
      );
    }
    function xe() {
      z(
        "watch.api.integrations.test_github",
        J,
        A,
        (n) => s("Connected") + (n?.username ? ` (${n.username})` : "")
      );
    }
    const _e = [
      { value: "billable", label: "Billable" },
      { value: "non-billable", label: "Non-billable" },
      { value: "internal", label: "Internal" }
    ], ge = [
      { value: "on_save", label: "On save" },
      { value: "manual", label: "Manual" },
      { value: "scheduled", label: "Scheduled" }
    ], ve = [
      { value: "hourly", label: "Hourly" },
      { value: "every_6_hours", label: "Every 6 hours" },
      { value: "daily", label: "Daily" }
    ], be = [
      { key: "work_mon", label: "Mon" },
      { key: "work_tue", label: "Tue" },
      { key: "work_wed", label: "Wed" },
      { key: "work_thu", label: "Thu" },
      { key: "work_fri", label: "Fri" },
      { key: "work_sat", label: "Sat" },
      { key: "work_sun", label: "Sun" }
    ];
    function ye(n, r) {
      l.value[n] = r ? 1 : 0;
    }
    function E(n, r) {
      l.value[n] = r ? 1 : 0;
    }
    const ae = [
      { value: "all_time", label: "All time" },
      { value: "this_year", label: "This year" },
      { value: "last_year", label: "Last year" },
      { value: "custom", label: "Custom…" }
    ], P = i("all_time"), N = i(""), V = i(""), G = i(!1), ke = we(
      () => ae.find((n) => n.value === P.value)?.label ?? s("All time")
    );
    function he() {
      const n = /* @__PURE__ */ new Date(), r = n.toISOString().slice(0, 10);
      let t, f = r;
      switch (P.value) {
        case "this_year":
          t = `${n.getFullYear()}-01-01`;
          break;
        case "last_year": {
          const w = n.getFullYear() - 1;
          t = `${w}-01-01`, f = `${w}-12-31`;
          break;
        }
        case "custom":
          t = N.value, f = V.value;
          break;
        default:
          t = "2000-01-01";
      }
      const j = new URLSearchParams({ from_date: t, to_date: f });
      window.location.href = `/api/method/watch.api.time_entry.export_csv?${j}`;
    }
    return (n, r) => (c(), u("div", Ve, [
      e("div", Fe, [
        e("h1", De, o(a(s)("Settings")), 1),
        d.value ? (c(), u(h, { key: 0 }, R(4, (t) => e("div", {
          key: t,
          class: "bg-white dark:bg-slate-950 rounded-xl border border-gray-200 dark:border-slate-700 p-4 animate-pulse h-14"
        })), 64)) : x.value && !l.value ? (c(), u("p", Ue, o(x.value), 1)) : (c(), u(h, { key: 2 }, [
          e("div", Le, [
            e("div", $e, [
              e("h2", Ie, o(a(s)("My Preferences")), 1),
              e("p", Me, o(a(s)("Personal settings — only you can see these.")), 1)
            ]),
            e("div", We, [
              e("div", Ae, [
                e("div", Ge, o(a(s)("Weekly hour target")), 1),
                e("div", Xe, o(a(s)("0 = no target (progress bar hidden).")), 1)
              ]),
              e("div", Ye, [
                g(e("input", {
                  "onUpdate:modelValue": r[0] || (r[0] = (t) => a(_).weekly_hour_target = t),
                  type: "number",
                  min: "0",
                  step: "1",
                  class: "w-20 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 512), [
                  [
                    k,
                    a(_).weekly_hour_target,
                    void 0,
                    { number: !0 }
                  ]
                ]),
                e("span", Be, o(a(s)("hours")), 1)
              ])
            ]),
            e("div", He, [
              e("label", Ke, o(a(s)("Keyboard shortcuts")), 1),
              e("label", qe, [
                e("input", {
                  type: "checkbox",
                  checked: !!a(_).enable_keyboard_shortcuts,
                  class: "w-4 h-4 rounded accent-[var(--app-accent-500)]",
                  onChange: r[1] || (r[1] = (t) => a(_).enable_keyboard_shortcuts = t.target.checked ? 1 : 0)
                }, null, 40, Je),
                e("span", ze, o(a(s)("Enabled")), 1)
              ])
            ]),
            e("div", Ze, [
              O.value ? (c(), u("p", Qe, o(O.value), 1)) : y("", !0),
              $.value ? (c(), u("p", et, o(a(s)("Saved.")), 1)) : y("", !0),
              e("button", {
                type: "button",
                disabled: L.value,
                class: "px-4 py-1.5 rounded-lg bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)] text-white text-sm font-medium transition-colors disabled:opacity-50",
                onClick: ie
              }, o(L.value ? a(s)("Saving…") : a(s)("Save")), 9, tt)
            ])
          ]),
          e("div", at, [
            e("div", st, [
              e("h2", ot, o(a(s)("Browser Extension")), 1),
              e("p", rt, o(a(s)("Connect the Watch browser extension to this site.")), 1)
            ]),
            e("div", lt, [
              e("div", nt, [
                e("span", dt, o(a(s)("Status")) + ":", 1),
                e("span", {
                  class: F(["text-sm font-medium", a(_).extension_token_active ? "text-green-600 dark:text-green-400" : "text-gray-500 dark:text-slate-500"])
                }, o(a(_).extension_token_active ? a(s)("Token active") : a(s)("Not connected")), 3)
              ]),
              m.value ? (c(), u("div", it, [
                e("div", ct, [
                  e("input", {
                    type: "text",
                    value: m.value,
                    readonly: "",
                    class: "flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800 text-xs font-mono text-gray-900 dark:text-slate-100 outline-none select-all",
                    onFocus: r[2] || (r[2] = (t) => t.target.select())
                  }, null, 40, ut),
                  e("button", {
                    type: "button",
                    class: "px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-xs font-medium text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors",
                    onClick: de
                  }, o(H.value ? a(s)("Copied") : a(s)("Copy")), 1)
                ]),
                e("p", pt, o(a(s)("This token will not be shown again. Paste it into the extension setup screen.")), 1)
              ])) : y("", !0),
              C.value ? (c(), u("p", xt, o(C.value), 1)) : y("", !0),
              e("div", _t, [
                a(_).extension_token_active ? (c(), u(h, { key: 1 }, [
                  e("button", {
                    type: "button",
                    disabled: T.value,
                    class: "px-4 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-sm font-medium text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-50",
                    onClick: te
                  }, o(T.value ? a(s)("Generating…") : a(s)("Regenerate token")), 9, vt),
                  e("button", {
                    type: "button",
                    disabled: I.value,
                    class: "px-4 py-1.5 rounded-lg border border-red-300 dark:border-red-700 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50",
                    onClick: ne
                  }, o(I.value ? a(s)("Revoking…") : a(s)("Revoke access")), 9, bt)
                ], 64)) : (c(), u("button", {
                  key: 0,
                  type: "button",
                  disabled: T.value,
                  class: "px-4 py-1.5 rounded-lg bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)] text-white text-sm font-medium transition-colors disabled:opacity-50",
                  onClick: te
                }, o(T.value ? a(s)("Generating…") : a(s)("Generate extension token")), 9, gt))
              ])
            ])
          ]),
          e("div", yt, [
            e("div", kt, [
              e("h2", ht, o(a(s)("General")), 1)
            ]),
            e("div", ft, [
              e("label", mt, o(a(s)("Default entry type")), 1),
              g(e("select", {
                "onUpdate:modelValue": r[3] || (r[3] = (t) => l.value.default_entry_type = t),
                class: "px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              }, [
                (c(), u(h, null, R(_e, (t) => e("option", {
                  key: t.value,
                  value: t.value
                }, o(a(s)(t.label)), 9, wt)), 64))
              ], 512), [
                [Z, l.value.default_entry_type]
              ])
            ]),
            e("div", St, [
              e("div", Tt, [
                e("div", Ct, o(a(s)("Lock entries older than (days)")), 1),
                e("div", Et, o(a(s)("0 = disabled.")), 1)
              ]),
              g(e("input", {
                "onUpdate:modelValue": r[4] || (r[4] = (t) => l.value.lock_entries_older_than = t),
                type: "number",
                min: "0",
                class: "w-20 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              }, null, 512), [
                [
                  k,
                  l.value.lock_entries_older_than,
                  void 0,
                  { number: !0 }
                ]
              ])
            ]),
            e("div", Pt, [
              e("div", jt, [
                e("div", Rt, o(a(s)("Auto-stop timer after (hours)")), 1),
                e("div", Ot, o(a(s)("0 = disabled.")), 1)
              ]),
              g(e("input", {
                "onUpdate:modelValue": r[5] || (r[5] = (t) => l.value.auto_stop_timer_after = t),
                type: "number",
                min: "0",
                class: "w-20 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
              }, null, 512), [
                [
                  k,
                  l.value.auto_stop_timer_after,
                  void 0,
                  { number: !0 }
                ]
              ])
            ]),
            e("div", Nt, [
              e("div", Vt, o(a(s)("Work days")), 1),
              e("div", Ft, [
                (c(), u(h, null, R(be, (t) => e("label", {
                  key: t.key,
                  class: "flex flex-col items-center gap-1 cursor-pointer"
                }, [
                  e("input", {
                    type: "checkbox",
                    checked: !!l.value[t.key],
                    class: "w-4 h-4 rounded accent-[var(--app-accent-500)]",
                    onChange: (f) => ye(t.key, f.target.checked)
                  }, null, 40, Dt),
                  e("span", Ut, o(a(s)(t.label)), 1)
                ])), 64))
              ])
            ])
          ]),
          e("div", Lt, [
            e("div", $t, [
              e("div", It, [
                e("h2", Mt, o(a(s)("ERPNext Bridge")), 1),
                e("p", Wt, o(a(s)("One-way sync of billable entries to ERPNext Timesheets.")), 1)
              ]),
              e("label", At, [
                e("input", {
                  type: "checkbox",
                  checked: !!l.value.enable_erpnext_bridge,
                  class: "w-4 h-4 rounded accent-[var(--app-accent-500)]",
                  onChange: r[6] || (r[6] = (t) => E("enable_erpnext_bridge", t.target.checked))
                }, null, 40, Gt),
                e("span", Xt, o(a(s)("Enable")), 1)
              ])
            ]),
            l.value.enable_erpnext_bridge ? (c(), u(h, { key: 0 }, [
              e("div", Yt, [
                e("label", Bt, o(a(s)("ERPNext site URL")), 1),
                g(e("input", {
                  "onUpdate:modelValue": r[7] || (r[7] = (t) => l.value.erpnext_site_url = t),
                  type: "url",
                  placeholder: "https://erp.example.com",
                  class: "w-56 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 512), [
                  [k, l.value.erpnext_site_url]
                ])
              ]),
              e("div", Ht, [
                e("label", Kt, o(a(s)("Sync mode")), 1),
                g(e("select", {
                  "onUpdate:modelValue": r[8] || (r[8] = (t) => l.value.sync_mode = t),
                  class: "px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, [
                  (c(), u(h, null, R(ge, (t) => e("option", {
                    key: t.value,
                    value: t.value
                  }, o(a(s)(t.label)), 9, qt)), 64))
                ], 512), [
                  [Z, l.value.sync_mode]
                ])
              ]),
              l.value.sync_mode === "scheduled" ? (c(), u("div", Jt, [
                e("label", zt, o(a(s)("Sync interval")), 1),
                g(e("select", {
                  "onUpdate:modelValue": r[9] || (r[9] = (t) => l.value.sync_interval = t),
                  class: "px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, [
                  (c(), u(h, null, R(ve, (t) => e("option", {
                    key: t.value,
                    value: t.value
                  }, o(a(s)(t.label)), 9, Zt)), 64))
                ], 512), [
                  [Z, l.value.sync_interval]
                ])
              ])) : y("", !0),
              e("div", Qt, [
                e("label", ea, o(a(s)("Default activity type")), 1),
                g(e("input", {
                  "onUpdate:modelValue": r[10] || (r[10] = (t) => l.value.default_activity_type = t),
                  type: "text",
                  class: "w-40 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 512), [
                  [k, l.value.default_activity_type]
                ])
              ]),
              e("div", ta, [
                e("label", aa, o(a(s)("Sync billable entries only")), 1),
                e("input", {
                  type: "checkbox",
                  checked: !!l.value.sync_billable_only,
                  class: "w-4 h-4 rounded accent-[var(--app-accent-500)]",
                  onChange: r[11] || (r[11] = (t) => E("sync_billable_only", t.target.checked))
                }, null, 40, sa)
              ]),
              e("div", oa, [
                e("label", ra, o(a(s)("Map project tags to ERPNext projects")), 1),
                e("input", {
                  type: "checkbox",
                  checked: !!l.value.map_project_tags,
                  class: "w-4 h-4 rounded accent-[var(--app-accent-500)]",
                  onChange: r[12] || (r[12] = (t) => E("map_project_tags", t.target.checked))
                }, null, 40, la)
              ])
            ], 64)) : y("", !0)
          ]),
          e("div", na, [
            e("div", da, [
              e("h2", ia, o(a(s)("Integrations")), 1),
              e("p", ca, o(a(s)("Connect Watch to Slack, Linear, and GitHub.")), 1)
            ]),
            e("div", ua, [
              e("div", pa, o(a(s)("Slack")), 1),
              e("div", xa, [
                e("label", _a, o(a(s)("Webhook URL")), 1),
                g(e("input", {
                  "onUpdate:modelValue": r[13] || (r[13] = (t) => l.value.slack_webhook_url = t),
                  type: "password",
                  placeholder: "https://hooks.slack.com/...",
                  class: "flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 512), [
                  [k, l.value.slack_webhook_url]
                ]),
                e("button", {
                  type: "button",
                  disabled: K.value || !l.value.slack_webhook_url,
                  class: "px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-xs font-medium text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-40",
                  onClick: ue
                }, o(K.value ? a(s)("Testing…") : a(s)("Test")), 9, ga)
              ]),
              e("div", va, [
                e("label", ba, [
                  e("input", {
                    type: "checkbox",
                    checked: !!l.value.slack_notify_on_stop,
                    class: "w-4 h-4 rounded accent-[var(--app-accent-500)]",
                    onChange: r[14] || (r[14] = (t) => E("slack_notify_on_stop", t.target.checked))
                  }, null, 40, ya),
                  e("span", ka, o(a(s)("Notify on timer stop")), 1)
                ])
              ]),
              e("div", ha, [
                e("label", fa, o(a(s)("Message template (optional)")), 1),
                g(e("input", {
                  "onUpdate:modelValue": r[15] || (r[15] = (t) => l.value.slack_message_template = t),
                  type: "text",
                  placeholder: "⏱ {description} — {duration} logged{tag_part}",
                  class: "px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 512), [
                  [k, l.value.slack_message_template]
                ])
              ]),
              M.value ? (c(), u("p", {
                key: 0,
                class: F(["text-xs", M.value.startsWith("Error") ? "text-red-500" : "text-green-600 dark:text-green-400"])
              }, o(M.value), 3)) : y("", !0)
            ]),
            e("div", ma, [
              e("div", wa, o(a(s)("Linear")), 1),
              e("div", Sa, [
                e("label", Ta, o(a(s)("API Key")), 1),
                g(e("input", {
                  "onUpdate:modelValue": r[16] || (r[16] = (t) => l.value.linear_api_key = t),
                  type: "password",
                  placeholder: "lin_api_…",
                  class: "flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 512), [
                  [k, l.value.linear_api_key]
                ]),
                e("button", {
                  type: "button",
                  disabled: q.value || !l.value.linear_api_key,
                  class: "px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-xs font-medium text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-40",
                  onClick: pe
                }, o(q.value ? a(s)("Testing…") : a(s)("Test")), 9, Ca)
              ]),
              e("div", Ea, [
                e("label", Pa, [
                  e("input", {
                    type: "checkbox",
                    checked: !!l.value.linear_post_comment,
                    class: "w-4 h-4 rounded accent-[var(--app-accent-500)]",
                    onChange: r[17] || (r[17] = (t) => E("linear_post_comment", t.target.checked))
                  }, null, 40, ja),
                  e("span", Ra, o(a(s)("Post comment on save")), 1)
                ])
              ]),
              W.value ? (c(), u("p", {
                key: 0,
                class: F(["text-xs", W.value.startsWith("Error") ? "text-red-500" : "text-green-600 dark:text-green-400"])
              }, o(W.value), 3)) : y("", !0)
            ]),
            e("div", Oa, [
              e("div", Na, o(a(s)("GitHub")), 1),
              e("div", Va, [
                e("label", Fa, o(a(s)("Token")), 1),
                g(e("input", {
                  "onUpdate:modelValue": r[18] || (r[18] = (t) => l.value.github_token = t),
                  type: "password",
                  placeholder: "ghp_…",
                  class: "flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 512), [
                  [k, l.value.github_token]
                ]),
                e("button", {
                  type: "button",
                  disabled: J.value || !l.value.github_token,
                  class: "px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-xs font-medium text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-40",
                  onClick: xe
                }, o(J.value ? a(s)("Testing…") : a(s)("Test")), 9, Da)
              ]),
              e("div", Ua, [
                e("label", La, o(a(s)("Default repo")), 1),
                g(e("input", {
                  "onUpdate:modelValue": r[19] || (r[19] = (t) => l.value.github_default_repo = t),
                  type: "text",
                  placeholder: "owner/repo",
                  class: "flex-1 px-2 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-sm text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 512), [
                  [k, l.value.github_default_repo]
                ])
              ]),
              e("div", $a, [
                e("label", Ia, [
                  e("input", {
                    type: "checkbox",
                    checked: !!l.value.github_post_comment,
                    class: "w-4 h-4 rounded accent-[var(--app-accent-500)]",
                    onChange: r[20] || (r[20] = (t) => E("github_post_comment", t.target.checked))
                  }, null, 40, Ma),
                  e("span", Wa, o(a(s)("Post comment on save")), 1)
                ])
              ]),
              A.value ? (c(), u("p", {
                key: 0,
                class: F(["text-xs", A.value.startsWith("Error") ? "text-red-500" : "text-green-600 dark:text-green-400"])
              }, o(A.value), 3)) : y("", !0)
            ])
          ]),
          e("div", Aa, [
            e("div", Ga, [
              e("h2", Xa, o(a(s)("Export my data")), 1),
              e("p", Ya, o(a(s)("Download all your time entries as CSV.")), 1)
            ]),
            e("div", Ba, [
              e("div", Ha, [
                e("button", {
                  type: "button",
                  class: "flex items-center gap-1 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-sm text-gray-900 dark:text-slate-100 hover:border-[var(--app-accent-500)]/50 transition-colors",
                  onClick: r[21] || (r[21] = (t) => G.value = !G.value)
                }, [
                  se(o(a(s)(ke.value)) + " ", 1),
                  oe(a(Ce), {
                    class: "w-3.5 h-3.5",
                    "aria-hidden": "true"
                  })
                ]),
                G.value ? (c(), u("div", Ka, [
                  (c(), u(h, null, R(ae, (t) => e("button", {
                    key: t.value,
                    type: "button",
                    class: F([
                      "w-full text-left px-3 py-1.5 text-sm transition-colors",
                      P.value === t.value ? "text-[var(--app-accent-500)] font-medium" : "text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800"
                    ]),
                    onClick: (f) => {
                      P.value = t.value, G.value = !1;
                    }
                  }, o(a(s)(t.label)), 11, qa)), 64))
                ])) : y("", !0)
              ]),
              P.value === "custom" ? (c(), u(h, { key: 0 }, [
                g(e("input", {
                  "onUpdate:modelValue": r[22] || (r[22] = (t) => N.value = t),
                  type: "date",
                  max: V.value || void 0,
                  class: "px-2 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 8, Ja), [
                  [k, N.value]
                ]),
                r[24] || (r[24] = e("span", { class: "text-gray-500 dark:text-slate-500 text-sm" }, "→", -1)),
                g(e("input", {
                  "onUpdate:modelValue": r[23] || (r[23] = (t) => V.value = t),
                  type: "date",
                  min: N.value || void 0,
                  class: "px-2 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-gray-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-[var(--app-accent-500)]/30 focus:border-[var(--app-accent-500)]"
                }, null, 8, za), [
                  [k, V.value]
                ])
              ], 64)) : y("", !0),
              e("button", {
                type: "button",
                disabled: P.value === "custom" && (!N.value || !V.value),
                class: "flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 dark:border-slate-700 text-sm text-gray-900 dark:text-slate-100 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-40",
                onClick: he
              }, [
                oe(a(Ee), {
                  class: "w-3.5 h-3.5",
                  "aria-hidden": "true"
                }),
                se(" " + o(a(s)("Download CSV")), 1)
              ], 8, Za)
            ])
          ]),
          x.value ? (c(), u("p", Qa, o(x.value), 1)) : y("", !0),
          b.value ? (c(), u("p", es, o(a(s)("Settings saved.")), 1)) : y("", !0),
          e("div", ts, [
            e("button", {
              type: "button",
              disabled: v.value,
              class: "px-5 py-2 rounded-lg bg-[var(--app-accent-500)] hover:bg-[var(--app-accent-700)] text-white text-sm font-medium transition-colors disabled:opacity-50",
              onClick: ce
            }, o(v.value ? a(s)("Saving…") : a(s)("Save settings")), 9, as)
          ])
        ], 64))
      ])
    ]));
  }
});
export {
  os as WatchSettings
};
