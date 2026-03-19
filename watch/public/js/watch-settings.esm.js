import { h as Q, ref as i, defineComponent as ge, onMounted as fe, computed as ke, openBlock as d, createElementBlock as u, createElementVNode as e, toDisplayString as o, unref as a, Fragment as y, renderList as R, withDirectives as p, vModelText as m, createCommentVNode as w, normalizeClass as F, vModelSelect as Z, createTextVNode as se, createVNode as oe } from "/assets/dock/js/vendor/vue.esm.js";
const Se = (v) => v.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
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
const Te = ({ size: v, strokeWidth: c = 2, absoluteStrokeWidth: _, color: h, iconNode: b, name: x, class: ee, ...Y }, { slots: U }) => Q(
  "svg",
  {
    ...X,
    width: v || X.width,
    height: v || X.height,
    stroke: h || X.stroke,
    "stroke-width": _ ? Number(c) * 24 / Number(v) : c,
    class: ["lucide", `lucide-${Se(x ?? "icon")}`],
    ...Y
  },
  [...b.map((B) => Q(...B)), ...U.default ? [U.default()] : []]
);
const re = (v, c) => (_, { slots: h }) => Q(
  Te,
  {
    ..._,
    iconNode: c,
    name: v
  },
  h
);
const Ce = re("ChevronDownIcon", [
  ["path", { d: "m6 9 6 6 6-6", key: "qrunsl" }]
]);
const Ee = re("DownloadIcon", [
  ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", key: "ih7n3h" }],
  ["polyline", { points: "7 10 12 15 17 10", key: "2ggqvy" }],
  ["line", { x1: "12", x2: "12", y1: "15", y2: "3", key: "1vk2je" }]
]);
function s(v, c) {
  let h = (window.__messages || {})[v] || v;
  if (c)
    if (Array.isArray(c))
      for (let b = 0; b < c.length; b++)
        h = h.replace(new RegExp(`\\{${b}\\}`, "g"), String(c[b]));
    else
      for (const [b, x] of Object.entries(c))
        h = h.replace(new RegExp(`\\{${b}\\}`, "g"), String(x));
  return h;
}
const S = i({
  weekly_hour_target: 0,
  enable_keyboard_shortcuts: 1,
  focus_work_minutes: 25,
  focus_break_minutes: 5,
  focus_sessions: 4,
  extension_token_active: 0
}), ne = i(!1), D = i(!1);
async function Pe() {
  D.value = !0;
  try {
    const v = await fetch("/api/method/watch.api.user_settings.get_preferences", {
      headers: { "X-Frappe-CSRF-Token": window.csrf_token ?? "" }
    }), c = await v.json();
    if (!v.ok || c.exc) throw new Error(c.exc ?? "Load failed");
    return Object.assign(S.value, c.message), ne.value = !0, S.value;
  } finally {
    D.value = !1;
  }
}
async function je(v) {
  D.value = !0;
  try {
    const c = await fetch("/api/method/watch.api.user_settings.save_preferences", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": window.csrf_token ?? ""
      },
      body: JSON.stringify(v)
    }), _ = await c.json();
    if (!c.ok || _.exc) throw new Error(_.exc ?? "Save failed");
    return Object.assign(S.value, _.message), S.value;
  } finally {
    D.value = !1;
  }
}
async function Re() {
  const v = await fetch("/api/method/watch.api.user_settings.generate_extension_token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": window.csrf_token ?? ""
    }
  }), c = await v.json();
  if (!v.ok || c.exc) throw new Error(c.exc ?? "Token generation failed");
  return S.value.extension_token_active = 1, c.message.token;
}
async function Oe() {
  const v = await fetch("/api/method/watch.api.user_settings.revoke_extension_token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": window.csrf_token ?? ""
    }
  }), c = await v.json();
  if (!v.ok || c.exc) throw new Error(c.exc ?? "Token revocation failed");
  S.value.extension_token_active = 0;
}
function Ne() {
  return { prefs: S, loaded: ne, loading: D, load: Pe, save: je, generateExtensionToken: Re, revokeExtensionToken: Oe };
}
const Ve = { class: "min-h-screen bg-[var(--watch-bg-secondary)]" }, Fe = { class: "max-w-2xl mx-auto px-4 py-6 space-y-4" }, De = { class: "text-lg font-semibold text-[var(--watch-text)]" }, Ue = {
  key: 1,
  class: "text-sm text-red-500 px-1"
}, Le = { class: "bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] overflow-hidden divide-y divide-[var(--watch-border)]" }, $e = { class: "px-4 py-3" }, Ie = { class: "text-sm font-semibold text-[var(--watch-text)]" }, Me = { class: "text-xs text-[var(--watch-text-muted)] mt-0.5" }, We = { class: "px-4 py-3 flex items-center gap-4" }, Ae = { class: "flex-1" }, Ge = { class: "text-sm text-[var(--watch-text)]" }, Xe = { class: "text-xs text-[var(--watch-text-muted)]" }, Ye = { class: "flex items-center gap-1.5" }, Be = { class: "text-xs text-[var(--watch-text-muted)]" }, He = { class: "px-4 py-3 flex items-center gap-4" }, Ke = { class: "text-sm text-[var(--watch-text)] flex-1" }, qe = { class: "flex items-center gap-2 cursor-pointer shrink-0" }, Je = ["checked"], ze = { class: "text-sm text-[var(--watch-text)]" }, Ze = { class: "px-4 py-3 flex items-center gap-3 justify-end" }, Qe = {
  key: 0,
  class: "text-xs text-red-500 flex-1"
}, et = {
  key: 1,
  class: "text-xs text-green-600 dark:text-green-400 flex-1"
}, tt = ["disabled"], at = { class: "bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] overflow-hidden divide-y divide-[var(--watch-border)]" }, st = { class: "px-4 py-3" }, ot = { class: "text-sm font-semibold text-[var(--watch-text)]" }, rt = { class: "text-xs text-[var(--watch-text-muted)] mt-0.5" }, nt = { class: "px-4 py-3 space-y-3" }, lt = { class: "flex items-center gap-2" }, ct = { class: "text-sm text-[var(--watch-text-muted)]" }, it = {
  key: 0,
  class: "space-y-2"
}, dt = { class: "flex items-center gap-2" }, ut = ["value"], vt = { class: "text-xs text-amber-600 dark:text-amber-400" }, ht = {
  key: 1,
  class: "text-xs text-red-500"
}, xt = { class: "flex items-center gap-2" }, pt = ["disabled"], _t = ["disabled"], bt = ["disabled"], wt = { class: "bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] overflow-hidden divide-y divide-[var(--watch-border)]" }, mt = { class: "px-4 py-3" }, yt = { class: "text-sm font-semibold text-[var(--watch-text)]" }, gt = { class: "px-4 py-3 flex items-center gap-4" }, ft = { class: "text-sm text-[var(--watch-text)] flex-1" }, kt = ["value"], St = { class: "px-4 py-3 flex items-center gap-4" }, Tt = { class: "flex-1" }, Ct = { class: "text-sm text-[var(--watch-text)]" }, Et = { class: "text-xs text-[var(--watch-text-muted)]" }, Pt = { class: "px-4 py-3 flex items-center gap-4" }, jt = { class: "flex-1" }, Rt = { class: "text-sm text-[var(--watch-text)]" }, Ot = { class: "text-xs text-[var(--watch-text-muted)]" }, Nt = { class: "px-4 py-3 space-y-2" }, Vt = { class: "text-sm text-[var(--watch-text)]" }, Ft = { class: "flex gap-4" }, Dt = ["checked", "onChange"], Ut = { class: "text-xs text-[var(--watch-text-muted)] select-none" }, Lt = { class: "bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] overflow-hidden divide-y divide-[var(--watch-border)]" }, $t = { class: "px-4 py-3 flex items-center gap-4" }, It = { class: "flex-1" }, Mt = { class: "text-sm font-semibold text-[var(--watch-text)]" }, Wt = { class: "text-xs text-[var(--watch-text-muted)]" }, At = { class: "flex items-center gap-2 cursor-pointer shrink-0" }, Gt = ["checked"], Xt = { class: "text-sm text-[var(--watch-text)]" }, Yt = { class: "px-4 py-3 flex items-center gap-4" }, Bt = { class: "text-sm text-[var(--watch-text)] flex-1" }, Ht = { class: "px-4 py-3 flex items-center gap-4" }, Kt = { class: "text-sm text-[var(--watch-text)] flex-1" }, qt = ["value"], Jt = {
  key: 0,
  class: "px-4 py-3 flex items-center gap-4"
}, zt = { class: "text-sm text-[var(--watch-text)] flex-1" }, Zt = ["value"], Qt = { class: "px-4 py-3 flex items-center gap-4" }, ea = { class: "text-sm text-[var(--watch-text)] flex-1" }, ta = { class: "px-4 py-3 flex items-center gap-4" }, aa = { class: "text-sm text-[var(--watch-text)] flex-1" }, sa = ["checked"], oa = { class: "px-4 py-3 flex items-center gap-4" }, ra = { class: "text-sm text-[var(--watch-text)] flex-1" }, na = ["checked"], la = { class: "bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] overflow-hidden divide-y divide-[var(--watch-border)]" }, ca = { class: "px-4 py-3" }, ia = { class: "text-sm font-semibold text-[var(--watch-text)]" }, da = { class: "text-xs text-[var(--watch-text-muted)] mt-0.5" }, ua = { class: "px-4 py-3 space-y-3" }, va = { class: "text-xs font-semibold text-[var(--watch-text-muted)] uppercase tracking-wide" }, ha = { class: "flex items-center gap-3" }, xa = { class: "text-sm text-[var(--watch-text)] w-32 shrink-0" }, pa = ["disabled"], _a = { class: "flex items-center gap-4" }, ba = { class: "flex items-center gap-2 cursor-pointer" }, wa = ["checked"], ma = { class: "text-sm text-[var(--watch-text)]" }, ya = { class: "flex flex-col gap-1" }, ga = { class: "text-xs text-[var(--watch-text-muted)]" }, fa = { class: "px-4 py-3 space-y-3" }, ka = { class: "text-xs font-semibold text-[var(--watch-text-muted)] uppercase tracking-wide" }, Sa = { class: "flex items-center gap-3" }, Ta = { class: "text-sm text-[var(--watch-text)] w-32 shrink-0" }, Ca = ["disabled"], Ea = { class: "flex items-center gap-4" }, Pa = { class: "flex items-center gap-2 cursor-pointer" }, ja = ["checked"], Ra = { class: "text-sm text-[var(--watch-text)]" }, Oa = { class: "px-4 py-3 space-y-3" }, Na = { class: "text-xs font-semibold text-[var(--watch-text-muted)] uppercase tracking-wide" }, Va = { class: "flex items-center gap-3" }, Fa = { class: "text-sm text-[var(--watch-text)] w-32 shrink-0" }, Da = ["disabled"], Ua = { class: "flex items-center gap-3" }, La = { class: "text-sm text-[var(--watch-text)] w-32 shrink-0" }, $a = { class: "flex items-center gap-4" }, Ia = { class: "flex items-center gap-2 cursor-pointer" }, Ma = ["checked"], Wa = { class: "text-sm text-[var(--watch-text)]" }, Aa = { class: "bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] overflow-hidden divide-y divide-[var(--watch-border)]" }, Ga = { class: "px-4 py-3" }, Xa = { class: "text-sm font-semibold text-[var(--watch-text)]" }, Ya = { class: "text-xs text-[var(--watch-text-muted)] mt-0.5" }, Ba = { class: "px-4 py-3 flex flex-wrap items-center gap-2" }, Ha = { class: "relative" }, Ka = {
  key: 0,
  class: "absolute left-0 top-full mt-1 z-20 bg-[var(--watch-bg)] border border-[var(--watch-border)] rounded-xl shadow-lg py-1 min-w-[140px]"
}, qa = ["onClick"], Ja = ["max"], za = ["min"], Za = ["disabled"], Qa = {
  key: 0,
  class: "text-sm text-red-500 px-1"
}, es = {
  key: 1,
  class: "text-sm text-green-600 dark:text-green-400 px-1"
}, ts = { class: "flex justify-end" }, as = ["disabled"], os = /* @__PURE__ */ ge({
  __name: "Settings",
  setup(v) {
    const c = i(!0), _ = i(!1), h = i(null), b = i(!1), {
      prefs: x,
      load: ee,
      save: Y,
      generateExtensionToken: U,
      revokeExtensionToken: B
    } = Ne(), L = i(!1), $ = i(!1), O = i(null), T = i(!1), I = i(!1), f = i(null), C = i(null), H = i(!1);
    async function te() {
      if (!(x.value.extension_token_active && !window.confirm(s("This will revoke the existing token. Continue?")))) {
        T.value = !0, C.value = null, f.value = null;
        try {
          const l = await U();
          f.value = l;
        } catch (l) {
          C.value = l.message;
        } finally {
          T.value = !1;
        }
      }
    }
    async function le() {
      I.value = !0, C.value = null, f.value = null;
      try {
        await B();
      } catch (l) {
        C.value = l.message;
      } finally {
        I.value = !1;
      }
    }
    async function ce() {
      if (f.value)
        try {
          await navigator.clipboard.writeText(f.value), H.value = !0, setTimeout(() => {
            H.value = !1;
          }, 2e3);
        } catch {
        }
    }
    async function ie() {
      L.value = !0, O.value = null, $.value = !1;
      try {
        await Y({
          weekly_hour_target: x.value.weekly_hour_target,
          enable_keyboard_shortcuts: x.value.enable_keyboard_shortcuts,
          focus_work_minutes: x.value.focus_work_minutes,
          focus_break_minutes: x.value.focus_break_minutes,
          focus_sessions: x.value.focus_sessions
        }), $.value = !0, setTimeout(() => {
          $.value = !1;
        }, 2500);
      } catch (l) {
        O.value = l.message;
      } finally {
        L.value = !1;
      }
    }
    const n = i({
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
    fe(async () => {
      const [, l] = await Promise.allSettled([
        (async () => {
          try {
            const r = await fetch("/api/method/watch.api.settings.get_settings", {
              headers: { "X-Frappe-CSRF-Token": window.csrf_token ?? "" }
            }), t = await r.json();
            if (!r.ok || t.exc) throw new Error(t.exc ?? "Load failed");
            Object.assign(n.value, t.message);
          } catch (r) {
            h.value = r.message;
          } finally {
            c.value = !1;
          }
        })(),
        ee()
      ]);
      l.status === "rejected" && (O.value = l.reason?.message ?? "Failed to load preferences");
    });
    async function de() {
      _.value = !0, h.value = null, b.value = !1;
      try {
        const l = await fetch("/api/method/watch.api.settings.save_settings", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Frappe-CSRF-Token": window.csrf_token ?? ""
          },
          body: JSON.stringify(n.value)
        }), r = await l.json();
        if (!l.ok || r.exc) throw new Error(r.exc ?? "Save failed");
        Object.assign(n.value, r.message), b.value = !0, setTimeout(() => {
          b.value = !1;
        }, 2500);
      } catch (l) {
        h.value = l.message;
      } finally {
        _.value = !1;
      }
    }
    const K = i(!1), M = i(null), q = i(!1), W = i(null), J = i(!1), A = i(null);
    async function z(l, r, t, g) {
      r.value = !0, t.value = null;
      try {
        const j = await fetch(`/api/method/${l}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Frappe-CSRF-Token": window.csrf_token ?? ""
          }
        }), k = await j.json();
        if (!j.ok || k.exc) throw new Error(k._server_messages || k.exc || "Test failed");
        t.value = g(k.message);
      } catch (j) {
        t.value = `Error: ${j.message}`;
      } finally {
        r.value = !1;
      }
    }
    function ue() {
      z("watch.api.integrations.test_slack", K, M, () => s("Connected"));
    }
    function ve() {
      z(
        "watch.api.integrations.test_linear",
        q,
        W,
        (l) => s("Connected") + (l?.workspace ? ` (${l.workspace})` : "")
      );
    }
    function he() {
      z(
        "watch.api.integrations.test_github",
        J,
        A,
        (l) => s("Connected") + (l?.username ? ` (${l.username})` : "")
      );
    }
    const xe = [
      { value: "billable", label: "Billable" },
      { value: "non-billable", label: "Non-billable" },
      { value: "internal", label: "Internal" }
    ], pe = [
      { value: "on_save", label: "On save" },
      { value: "manual", label: "Manual" },
      { value: "scheduled", label: "Scheduled" }
    ], _e = [
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
    function we(l, r) {
      n.value[l] = r ? 1 : 0;
    }
    function E(l, r) {
      n.value[l] = r ? 1 : 0;
    }
    const ae = [
      { value: "all_time", label: "All time" },
      { value: "this_year", label: "This year" },
      { value: "last_year", label: "Last year" },
      { value: "custom", label: "Custom…" }
    ], P = i("all_time"), N = i(""), V = i(""), G = i(!1), me = ke(
      () => ae.find((l) => l.value === P.value)?.label ?? s("All time")
    );
    function ye() {
      const l = /* @__PURE__ */ new Date(), r = l.toISOString().slice(0, 10);
      let t, g = r;
      switch (P.value) {
        case "this_year":
          t = `${l.getFullYear()}-01-01`;
          break;
        case "last_year": {
          const k = l.getFullYear() - 1;
          t = `${k}-01-01`, g = `${k}-12-31`;
          break;
        }
        case "custom":
          t = N.value, g = V.value;
          break;
        default:
          t = "2000-01-01";
      }
      const j = new URLSearchParams({ from_date: t, to_date: g });
      window.location.href = `/api/method/watch.api.time_entry.export_csv?${j}`;
    }
    return (l, r) => (d(), u("div", Ve, [
      e("div", Fe, [
        e("h1", De, o(a(s)("Settings")), 1),
        c.value ? (d(), u(y, { key: 0 }, R(4, (t) => e("div", {
          key: t,
          class: "bg-[var(--watch-bg)] rounded-xl border border-[var(--watch-border)] p-4 animate-pulse h-14"
        })), 64)) : h.value && !n.value ? (d(), u("p", Ue, o(h.value), 1)) : (d(), u(y, { key: 2 }, [
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
                p(e("input", {
                  "onUpdate:modelValue": r[0] || (r[0] = (t) => a(x).weekly_hour_target = t),
                  type: "number",
                  min: "0",
                  step: "1",
                  class: "w-20 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 512), [
                  [
                    m,
                    a(x).weekly_hour_target,
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
                  checked: !!a(x).enable_keyboard_shortcuts,
                  class: "w-4 h-4 rounded accent-[var(--watch-primary)]",
                  onChange: r[1] || (r[1] = (t) => a(x).enable_keyboard_shortcuts = t.target.checked ? 1 : 0)
                }, null, 40, Je),
                e("span", ze, o(a(s)("Enabled")), 1)
              ])
            ]),
            e("div", Ze, [
              O.value ? (d(), u("p", Qe, o(O.value), 1)) : w("", !0),
              $.value ? (d(), u("p", et, o(a(s)("Saved.")), 1)) : w("", !0),
              e("button", {
                type: "button",
                disabled: L.value,
                class: "px-4 py-1.5 rounded-lg bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)] text-white text-sm font-medium transition-colors disabled:opacity-50",
                onClick: ie
              }, o(L.value ? a(s)("Saving…") : a(s)("Save")), 9, tt)
            ])
          ]),
          e("div", at, [
            e("div", st, [
              e("h2", ot, o(a(s)("Browser Extension")), 1),
              e("p", rt, o(a(s)("Connect the Watch browser extension to this site.")), 1)
            ]),
            e("div", nt, [
              e("div", lt, [
                e("span", ct, o(a(s)("Status")) + ":", 1),
                e("span", {
                  class: F(["text-sm font-medium", a(x).extension_token_active ? "text-green-600 dark:text-green-400" : "text-[var(--watch-text-muted)]"])
                }, o(a(x).extension_token_active ? a(s)("Token active") : a(s)("Not connected")), 3)
              ]),
              f.value ? (d(), u("div", it, [
                e("div", dt, [
                  e("input", {
                    type: "text",
                    value: f.value,
                    readonly: "",
                    class: "flex-1 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg-secondary)] text-xs font-mono text-[var(--watch-text)] outline-none select-all",
                    onFocus: r[2] || (r[2] = (t) => t.target.select())
                  }, null, 40, ut),
                  e("button", {
                    type: "button",
                    class: "px-3 py-1.5 rounded-lg border border-[var(--watch-border)] text-xs font-medium text-[var(--watch-text)] hover:bg-[var(--watch-bg-secondary)] transition-colors",
                    onClick: ce
                  }, o(H.value ? a(s)("Copied") : a(s)("Copy")), 1)
                ]),
                e("p", vt, o(a(s)("This token will not be shown again. Paste it into the extension setup screen.")), 1)
              ])) : w("", !0),
              C.value ? (d(), u("p", ht, o(C.value), 1)) : w("", !0),
              e("div", xt, [
                a(x).extension_token_active ? (d(), u(y, { key: 1 }, [
                  e("button", {
                    type: "button",
                    disabled: T.value,
                    class: "px-4 py-1.5 rounded-lg border border-[var(--watch-border)] text-sm font-medium text-[var(--watch-text)] hover:bg-[var(--watch-bg-secondary)] transition-colors disabled:opacity-50",
                    onClick: te
                  }, o(T.value ? a(s)("Generating…") : a(s)("Regenerate token")), 9, _t),
                  e("button", {
                    type: "button",
                    disabled: I.value,
                    class: "px-4 py-1.5 rounded-lg border border-red-300 dark:border-red-700 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50",
                    onClick: le
                  }, o(I.value ? a(s)("Revoking…") : a(s)("Revoke access")), 9, bt)
                ], 64)) : (d(), u("button", {
                  key: 0,
                  type: "button",
                  disabled: T.value,
                  class: "px-4 py-1.5 rounded-lg bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)] text-white text-sm font-medium transition-colors disabled:opacity-50",
                  onClick: te
                }, o(T.value ? a(s)("Generating…") : a(s)("Generate extension token")), 9, pt))
              ])
            ])
          ]),
          e("div", wt, [
            e("div", mt, [
              e("h2", yt, o(a(s)("General")), 1)
            ]),
            e("div", gt, [
              e("label", ft, o(a(s)("Default entry type")), 1),
              p(e("select", {
                "onUpdate:modelValue": r[3] || (r[3] = (t) => n.value.default_entry_type = t),
                class: "px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
              }, [
                (d(), u(y, null, R(xe, (t) => e("option", {
                  key: t.value,
                  value: t.value
                }, o(a(s)(t.label)), 9, kt)), 64))
              ], 512), [
                [Z, n.value.default_entry_type]
              ])
            ]),
            e("div", St, [
              e("div", Tt, [
                e("div", Ct, o(a(s)("Lock entries older than (days)")), 1),
                e("div", Et, o(a(s)("0 = disabled.")), 1)
              ]),
              p(e("input", {
                "onUpdate:modelValue": r[4] || (r[4] = (t) => n.value.lock_entries_older_than = t),
                type: "number",
                min: "0",
                class: "w-20 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
              }, null, 512), [
                [
                  m,
                  n.value.lock_entries_older_than,
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
              p(e("input", {
                "onUpdate:modelValue": r[5] || (r[5] = (t) => n.value.auto_stop_timer_after = t),
                type: "number",
                min: "0",
                class: "w-20 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
              }, null, 512), [
                [
                  m,
                  n.value.auto_stop_timer_after,
                  void 0,
                  { number: !0 }
                ]
              ])
            ]),
            e("div", Nt, [
              e("div", Vt, o(a(s)("Work days")), 1),
              e("div", Ft, [
                (d(), u(y, null, R(be, (t) => e("label", {
                  key: t.key,
                  class: "flex flex-col items-center gap-1 cursor-pointer"
                }, [
                  e("input", {
                    type: "checkbox",
                    checked: !!n.value[t.key],
                    class: "w-4 h-4 rounded accent-[var(--watch-primary)]",
                    onChange: (g) => we(t.key, g.target.checked)
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
                  checked: !!n.value.enable_erpnext_bridge,
                  class: "w-4 h-4 rounded accent-[var(--watch-primary)]",
                  onChange: r[6] || (r[6] = (t) => E("enable_erpnext_bridge", t.target.checked))
                }, null, 40, Gt),
                e("span", Xt, o(a(s)("Enable")), 1)
              ])
            ]),
            n.value.enable_erpnext_bridge ? (d(), u(y, { key: 0 }, [
              e("div", Yt, [
                e("label", Bt, o(a(s)("ERPNext site URL")), 1),
                p(e("input", {
                  "onUpdate:modelValue": r[7] || (r[7] = (t) => n.value.erpnext_site_url = t),
                  type: "url",
                  placeholder: "https://erp.example.com",
                  class: "w-56 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 512), [
                  [m, n.value.erpnext_site_url]
                ])
              ]),
              e("div", Ht, [
                e("label", Kt, o(a(s)("Sync mode")), 1),
                p(e("select", {
                  "onUpdate:modelValue": r[8] || (r[8] = (t) => n.value.sync_mode = t),
                  class: "px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, [
                  (d(), u(y, null, R(pe, (t) => e("option", {
                    key: t.value,
                    value: t.value
                  }, o(a(s)(t.label)), 9, qt)), 64))
                ], 512), [
                  [Z, n.value.sync_mode]
                ])
              ]),
              n.value.sync_mode === "scheduled" ? (d(), u("div", Jt, [
                e("label", zt, o(a(s)("Sync interval")), 1),
                p(e("select", {
                  "onUpdate:modelValue": r[9] || (r[9] = (t) => n.value.sync_interval = t),
                  class: "px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, [
                  (d(), u(y, null, R(_e, (t) => e("option", {
                    key: t.value,
                    value: t.value
                  }, o(a(s)(t.label)), 9, Zt)), 64))
                ], 512), [
                  [Z, n.value.sync_interval]
                ])
              ])) : w("", !0),
              e("div", Qt, [
                e("label", ea, o(a(s)("Default activity type")), 1),
                p(e("input", {
                  "onUpdate:modelValue": r[10] || (r[10] = (t) => n.value.default_activity_type = t),
                  type: "text",
                  class: "w-40 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 512), [
                  [m, n.value.default_activity_type]
                ])
              ]),
              e("div", ta, [
                e("label", aa, o(a(s)("Sync billable entries only")), 1),
                e("input", {
                  type: "checkbox",
                  checked: !!n.value.sync_billable_only,
                  class: "w-4 h-4 rounded accent-[var(--watch-primary)]",
                  onChange: r[11] || (r[11] = (t) => E("sync_billable_only", t.target.checked))
                }, null, 40, sa)
              ]),
              e("div", oa, [
                e("label", ra, o(a(s)("Map project tags to ERPNext projects")), 1),
                e("input", {
                  type: "checkbox",
                  checked: !!n.value.map_project_tags,
                  class: "w-4 h-4 rounded accent-[var(--watch-primary)]",
                  onChange: r[12] || (r[12] = (t) => E("map_project_tags", t.target.checked))
                }, null, 40, na)
              ])
            ], 64)) : w("", !0)
          ]),
          e("div", la, [
            e("div", ca, [
              e("h2", ia, o(a(s)("Integrations")), 1),
              e("p", da, o(a(s)("Connect Watch to Slack, Linear, and GitHub.")), 1)
            ]),
            e("div", ua, [
              e("div", va, o(a(s)("Slack")), 1),
              e("div", ha, [
                e("label", xa, o(a(s)("Webhook URL")), 1),
                p(e("input", {
                  "onUpdate:modelValue": r[13] || (r[13] = (t) => n.value.slack_webhook_url = t),
                  type: "password",
                  placeholder: "https://hooks.slack.com/...",
                  class: "flex-1 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 512), [
                  [m, n.value.slack_webhook_url]
                ]),
                e("button", {
                  type: "button",
                  disabled: K.value || !n.value.slack_webhook_url,
                  class: "px-3 py-1.5 rounded-lg border border-[var(--watch-border)] text-xs font-medium text-[var(--watch-text)] hover:bg-[var(--watch-bg-secondary)] transition-colors disabled:opacity-40",
                  onClick: ue
                }, o(K.value ? a(s)("Testing…") : a(s)("Test")), 9, pa)
              ]),
              e("div", _a, [
                e("label", ba, [
                  e("input", {
                    type: "checkbox",
                    checked: !!n.value.slack_notify_on_stop,
                    class: "w-4 h-4 rounded accent-[var(--watch-primary)]",
                    onChange: r[14] || (r[14] = (t) => E("slack_notify_on_stop", t.target.checked))
                  }, null, 40, wa),
                  e("span", ma, o(a(s)("Notify on timer stop")), 1)
                ])
              ]),
              e("div", ya, [
                e("label", ga, o(a(s)("Message template (optional)")), 1),
                p(e("input", {
                  "onUpdate:modelValue": r[15] || (r[15] = (t) => n.value.slack_message_template = t),
                  type: "text",
                  placeholder: "⏱ {description} — {duration} logged{tag_part}",
                  class: "px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 512), [
                  [m, n.value.slack_message_template]
                ])
              ]),
              M.value ? (d(), u("p", {
                key: 0,
                class: F(["text-xs", M.value.startsWith("Error") ? "text-red-500" : "text-green-600 dark:text-green-400"])
              }, o(M.value), 3)) : w("", !0)
            ]),
            e("div", fa, [
              e("div", ka, o(a(s)("Linear")), 1),
              e("div", Sa, [
                e("label", Ta, o(a(s)("API Key")), 1),
                p(e("input", {
                  "onUpdate:modelValue": r[16] || (r[16] = (t) => n.value.linear_api_key = t),
                  type: "password",
                  placeholder: "lin_api_…",
                  class: "flex-1 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 512), [
                  [m, n.value.linear_api_key]
                ]),
                e("button", {
                  type: "button",
                  disabled: q.value || !n.value.linear_api_key,
                  class: "px-3 py-1.5 rounded-lg border border-[var(--watch-border)] text-xs font-medium text-[var(--watch-text)] hover:bg-[var(--watch-bg-secondary)] transition-colors disabled:opacity-40",
                  onClick: ve
                }, o(q.value ? a(s)("Testing…") : a(s)("Test")), 9, Ca)
              ]),
              e("div", Ea, [
                e("label", Pa, [
                  e("input", {
                    type: "checkbox",
                    checked: !!n.value.linear_post_comment,
                    class: "w-4 h-4 rounded accent-[var(--watch-primary)]",
                    onChange: r[17] || (r[17] = (t) => E("linear_post_comment", t.target.checked))
                  }, null, 40, ja),
                  e("span", Ra, o(a(s)("Post comment on save")), 1)
                ])
              ]),
              W.value ? (d(), u("p", {
                key: 0,
                class: F(["text-xs", W.value.startsWith("Error") ? "text-red-500" : "text-green-600 dark:text-green-400"])
              }, o(W.value), 3)) : w("", !0)
            ]),
            e("div", Oa, [
              e("div", Na, o(a(s)("GitHub")), 1),
              e("div", Va, [
                e("label", Fa, o(a(s)("Token")), 1),
                p(e("input", {
                  "onUpdate:modelValue": r[18] || (r[18] = (t) => n.value.github_token = t),
                  type: "password",
                  placeholder: "ghp_…",
                  class: "flex-1 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 512), [
                  [m, n.value.github_token]
                ]),
                e("button", {
                  type: "button",
                  disabled: J.value || !n.value.github_token,
                  class: "px-3 py-1.5 rounded-lg border border-[var(--watch-border)] text-xs font-medium text-[var(--watch-text)] hover:bg-[var(--watch-bg-secondary)] transition-colors disabled:opacity-40",
                  onClick: he
                }, o(J.value ? a(s)("Testing…") : a(s)("Test")), 9, Da)
              ]),
              e("div", Ua, [
                e("label", La, o(a(s)("Default repo")), 1),
                p(e("input", {
                  "onUpdate:modelValue": r[19] || (r[19] = (t) => n.value.github_default_repo = t),
                  type: "text",
                  placeholder: "owner/repo",
                  class: "flex-1 px-2 py-1.5 rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-sm text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 512), [
                  [m, n.value.github_default_repo]
                ])
              ]),
              e("div", $a, [
                e("label", Ia, [
                  e("input", {
                    type: "checkbox",
                    checked: !!n.value.github_post_comment,
                    class: "w-4 h-4 rounded accent-[var(--watch-primary)]",
                    onChange: r[20] || (r[20] = (t) => E("github_post_comment", t.target.checked))
                  }, null, 40, Ma),
                  e("span", Wa, o(a(s)("Post comment on save")), 1)
                ])
              ]),
              A.value ? (d(), u("p", {
                key: 0,
                class: F(["text-xs", A.value.startsWith("Error") ? "text-red-500" : "text-green-600 dark:text-green-400"])
              }, o(A.value), 3)) : w("", !0)
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
                  class: "flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[var(--watch-border)] text-sm text-[var(--watch-text)] hover:border-[var(--watch-primary)]/50 transition-colors",
                  onClick: r[21] || (r[21] = (t) => G.value = !G.value)
                }, [
                  se(o(a(s)(me.value)) + " ", 1),
                  oe(a(Ce), {
                    class: "w-3.5 h-3.5",
                    "aria-hidden": "true"
                  })
                ]),
                G.value ? (d(), u("div", Ka, [
                  (d(), u(y, null, R(ae, (t) => e("button", {
                    key: t.value,
                    type: "button",
                    class: F([
                      "w-full text-left px-3 py-1.5 text-sm transition-colors",
                      P.value === t.value ? "text-[var(--watch-primary)] font-medium" : "text-[var(--watch-text)] hover:bg-[var(--watch-bg-secondary)]"
                    ]),
                    onClick: (g) => {
                      P.value = t.value, G.value = !1;
                    }
                  }, o(a(s)(t.label)), 11, qa)), 64))
                ])) : w("", !0)
              ]),
              P.value === "custom" ? (d(), u(y, { key: 0 }, [
                p(e("input", {
                  "onUpdate:modelValue": r[22] || (r[22] = (t) => N.value = t),
                  type: "date",
                  max: V.value || void 0,
                  class: "px-2 py-1.5 text-sm rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 8, Ja), [
                  [m, N.value]
                ]),
                r[24] || (r[24] = e("span", { class: "text-[var(--watch-text-muted)] text-sm" }, "→", -1)),
                p(e("input", {
                  "onUpdate:modelValue": r[23] || (r[23] = (t) => V.value = t),
                  type: "date",
                  min: N.value || void 0,
                  class: "px-2 py-1.5 text-sm rounded-lg border border-[var(--watch-border)] bg-[var(--watch-bg)] text-[var(--watch-text)] outline-none focus:ring-2 focus:ring-[var(--watch-primary)]/30 focus:border-[var(--watch-primary)]"
                }, null, 8, za), [
                  [m, V.value]
                ])
              ], 64)) : w("", !0),
              e("button", {
                type: "button",
                disabled: P.value === "custom" && (!N.value || !V.value),
                class: "flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--watch-border)] text-sm text-[var(--watch-text)] hover:bg-[var(--watch-bg-secondary)] transition-colors disabled:opacity-40",
                onClick: ye
              }, [
                oe(a(Ee), {
                  class: "w-3.5 h-3.5",
                  "aria-hidden": "true"
                }),
                se(" " + o(a(s)("Download CSV")), 1)
              ], 8, Za)
            ])
          ]),
          h.value ? (d(), u("p", Qa, o(h.value), 1)) : w("", !0),
          b.value ? (d(), u("p", es, o(a(s)("Settings saved.")), 1)) : w("", !0),
          e("div", ts, [
            e("button", {
              type: "button",
              disabled: _.value,
              class: "px-5 py-2 rounded-lg bg-[var(--watch-primary)] hover:bg-[var(--watch-primary-dark)] text-white text-sm font-medium transition-colors disabled:opacity-50",
              onClick: de
            }, o(_.value ? a(s)("Saving…") : a(s)("Save settings")), 9, as)
          ])
        ], 64))
      ])
    ]));
  }
});
export {
  os as WatchSettings
};
