import { h as ee, defineComponent as ye, ref as i, reactive as se, onMounted as be, openBlock as l, createElementBlock as d, createElementVNode as e, toDisplayString as r, Fragment as w, renderList as D, normalizeClass as M, createTextVNode as re, createCommentVNode as g, unref as s, withDirectives as u, vModelText as _, vModelSelect as H, createVNode as xe } from "/assets/dock/js/vendor/vue.esm.js";
const _e = (k) => k.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
var K = {
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
const ke = ({ size: k, strokeWidth: x = 2, absoluteStrokeWidth: C, color: p, iconNode: m, name: U, class: te, ...v }, { slots: O }) => ee(
  "svg",
  {
    ...K,
    width: k || K.width,
    height: k || K.height,
    stroke: p || K.stroke,
    "stroke-width": C ? Number(x) * 24 / Number(k) : x,
    class: ["lucide", `lucide-${_e(U ?? "icon")}`],
    ...v
  },
  [...m.map((f) => ee(...f)), ...O.default ? [O.default()] : []]
);
const pe = (k, x) => (C, { slots: p }) => ee(
  ke,
  {
    ...C,
    iconNode: x,
    name: k
  },
  p
);
const he = pe("DownloadIcon", [
  ["path", { d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4", key: "ih7n3h" }],
  ["polyline", { points: "7 10 12 15 17 10", key: "2ggqvy" }],
  ["line", { x1: "12", x2: "12", y1: "15", y2: "3", key: "1vk2je" }]
]);
function t(k, x) {
  let p = (window.__messages || {})[k] || k;
  if (x)
    if (Array.isArray(x))
      for (let m = 0; m < x.length; m++)
        p = p.replace(new RegExp(`\\{${m}\\}`, "g"), String(x[m]));
    else
      for (const [m, U] of Object.entries(x))
        p = p.replace(new RegExp(`\\{${m}\\}`, "g"), String(U));
  return p;
}
const me = {
  key: 0,
  class: "flex items-center justify-center py-20"
}, ve = {
  key: 1,
  class: "text-sm text-red-500"
}, fe = { class: "flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6" }, we = ["onClick"], Se = {
  key: 0,
  class: "absolute bottom-0 left-0 right-0 h-0.5 bg-accent-600 dark:bg-accent-400 rounded-full"
}, Te = {
  key: 0,
  class: "max-w-2xl space-y-6"
}, Ce = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, Ee = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, Re = { class: "mb-4 text-xs text-gray-400 dark:text-gray-500" }, Ve = { class: "space-y-5" }, Pe = { class: "flex items-center gap-4" }, Ne = { class: "flex-1" }, De = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, Ue = { class: "text-xs text-gray-400 dark:text-gray-500" }, Oe = { class: "flex items-center gap-1.5" }, Fe = { class: "text-xs text-gray-400 dark:text-gray-500" }, Ie = { class: "flex items-center gap-4" }, Me = { class: "text-sm font-medium text-gray-700 dark:text-gray-300 flex-1" }, $e = { class: "flex items-center gap-2 cursor-pointer" }, Ae = ["checked"], We = { class: "text-sm text-gray-700 dark:text-gray-300" }, je = { class: "flex items-center gap-3 mt-5 pt-4 border-t border-gray-100 dark:border-gray-700" }, Le = ["disabled"], Ge = {
  key: 0,
  class: "text-xs text-green-600 dark:text-green-400"
}, Ye = {
  key: 1,
  class: "text-xs text-red-500"
}, Be = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, He = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, Ke = { class: "mb-4 text-xs text-gray-400 dark:text-gray-500" }, qe = { class: "space-y-4" }, Xe = { class: "flex items-center gap-2" }, Ze = { class: "text-sm text-gray-500 dark:text-gray-400" }, ze = {
  key: 0,
  class: "space-y-2"
}, Je = { class: "flex items-center gap-2" }, Qe = ["value"], et = { class: "text-xs text-amber-600 dark:text-amber-400" }, tt = {
  key: 1,
  class: "text-xs text-red-500"
}, at = { class: "flex items-center gap-2" }, st = ["disabled"], rt = ["disabled"], ot = ["disabled"], nt = {
  key: 1,
  class: "max-w-2xl space-y-6"
}, lt = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, dt = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, ct = { class: "space-y-5" }, it = { class: "flex items-center gap-4" }, gt = { class: "text-sm font-medium text-gray-700 dark:text-gray-300 flex-1" }, ut = ["value"], yt = { class: "flex items-center gap-4" }, bt = { class: "flex-1" }, xt = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, _t = { class: "text-xs text-gray-400 dark:text-gray-500" }, kt = { class: "flex items-center gap-4" }, pt = { class: "flex-1" }, ht = { class: "text-sm font-medium text-gray-700 dark:text-gray-300" }, mt = { class: "text-xs text-gray-400 dark:text-gray-500" }, vt = { class: "text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block" }, ft = { class: "flex gap-4" }, wt = ["checked", "onChange"], St = { class: "text-xs text-gray-400 dark:text-gray-500 select-none" }, Tt = { class: "flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 py-4" }, Ct = ["disabled"], Et = {
  key: 0,
  class: "text-xs text-green-600 dark:text-green-400"
}, Rt = {
  key: 1,
  class: "text-xs text-red-500"
}, Vt = {
  key: 2,
  class: "max-w-2xl space-y-6"
}, Pt = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, Nt = { class: "flex items-center justify-between mb-4" }, Dt = { class: "text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, Ut = { class: "text-xs text-gray-400 dark:text-gray-500 mt-1" }, Ot = { class: "flex items-center gap-2 cursor-pointer" }, Ft = ["checked"], It = { class: "text-sm text-gray-700 dark:text-gray-300" }, Mt = {
  key: 0,
  class: "space-y-5"
}, $t = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, At = { class: "grid gap-4 sm:grid-cols-2" }, Wt = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, jt = ["value"], Lt = { key: 0 }, Gt = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, Yt = ["value"], Bt = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, Ht = { class: "flex items-center gap-2 cursor-pointer" }, Kt = ["checked"], qt = { class: "text-sm text-gray-700 dark:text-gray-300" }, Xt = { class: "flex items-center gap-2 cursor-pointer" }, Zt = ["checked"], zt = { class: "text-sm text-gray-700 dark:text-gray-300" }, Jt = { class: "flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 py-4" }, Qt = ["disabled"], ea = {
  key: 0,
  class: "text-xs text-green-600 dark:text-green-400"
}, ta = {
  key: 1,
  class: "text-xs text-red-500"
}, aa = {
  key: 3,
  class: "max-w-2xl space-y-6"
}, sa = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, ra = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, oa = { class: "space-y-5" }, na = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, la = { class: "flex items-center gap-2 cursor-pointer" }, da = ["checked"], ca = { class: "text-sm text-gray-700 dark:text-gray-300" }, ia = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, ga = { class: "flex items-center gap-3" }, ua = ["disabled"], ya = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, ba = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, xa = { class: "space-y-5" }, _a = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, ka = { class: "flex items-center gap-2 cursor-pointer" }, pa = ["checked"], ha = { class: "text-sm text-gray-700 dark:text-gray-300" }, ma = { class: "flex items-center gap-3" }, va = ["disabled"], fa = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, wa = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, Sa = { class: "space-y-5" }, Ta = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, Ca = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, Ea = { class: "flex items-center gap-2 cursor-pointer" }, Ra = ["checked"], Va = { class: "text-sm text-gray-700 dark:text-gray-300" }, Pa = { class: "flex items-center gap-3" }, Na = ["disabled"], Da = { class: "flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 py-4" }, Ua = ["disabled"], Oa = {
  key: 0,
  class: "text-xs text-green-600 dark:text-green-400"
}, Fa = {
  key: 1,
  class: "text-xs text-red-500"
}, Ia = {
  key: 4,
  class: "max-w-2xl space-y-6"
}, Ma = { class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5" }, $a = { class: "mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400" }, Aa = { class: "mb-4 text-xs text-gray-400 dark:text-gray-500" }, Wa = { class: "space-y-5" }, ja = { class: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5" }, La = ["value"], Ga = {
  key: 0,
  class: "flex items-center gap-3"
}, Ya = ["max"], Ba = ["min"], Ha = ["disabled"], qa = /* @__PURE__ */ ye({
  __name: "Settings",
  setup(k) {
    const x = [
      { value: "billable", label: "Billable" },
      { value: "non-billable", label: "Non-billable" },
      { value: "internal", label: "Internal" }
    ], C = [
      { value: "on_save", label: "On save" },
      { value: "manual", label: "Manual" },
      { value: "scheduled", label: "Scheduled" }
    ], p = [
      { value: "hourly", label: "Hourly" },
      { value: "every_6_hours", label: "Every 6 hours" },
      { value: "daily", label: "Daily" }
    ], m = [
      { key: "work_mon", label: "Mon" },
      { key: "work_tue", label: "Tue" },
      { key: "work_wed", label: "Wed" },
      { key: "work_thu", label: "Thu" },
      { key: "work_fri", label: "Fri" },
      { key: "work_sat", label: "Sat" },
      { key: "work_sun", label: "Sun" }
    ], U = [
      { value: "all", label: "All time" },
      { value: "this_year", label: "This year" },
      { value: "last_year", label: "Last year" },
      { value: "custom", label: "Custom range" }
    ], te = [
      { label: t("My Preferences") },
      { label: t("General") },
      { label: t("ERPNext Bridge") },
      { label: t("Integrations") },
      { label: t("Export") }
    ], v = i(0), O = i(!0), f = i(!1), E = i(!1), h = i(""), $ = i(!1), A = i(!1), W = i(""), n = se({
      default_entry_type: "billable",
      lock_entries_older_than: 0,
      auto_stop_timer_after: 0,
      work_mon: 1,
      work_tue: 1,
      work_wed: 1,
      work_thu: 1,
      work_fri: 1,
      work_sat: 0,
      work_sun: 0,
      enable_erpnext_bridge: 0,
      erpnext_site_url: "",
      sync_mode: "on_save",
      sync_interval: "daily",
      default_activity_type: "",
      sync_billable_only: 0,
      map_project_tags: 0,
      slack_webhook_url: "",
      slack_notify_on_stop: 0,
      slack_message_template: "",
      linear_api_key: "",
      linear_post_comment: 0,
      github_token: "",
      github_default_repo: "",
      github_post_comment: 0
    }), b = se({
      weekly_hour_target: 0,
      enable_keyboard_shortcuts: 1,
      extension_token_active: !1
    }), R = i(""), q = i(!1), V = i(!1), j = i(!1), P = i(""), X = i(!1), L = i(null), Z = i(!1), G = i(null), z = i(!1), Y = i(null), S = i("all"), F = i(""), I = i("");
    i(!1);
    async function T(c, o = {}) {
      return window.frappe.call({ method: c, args: o, type: "POST" });
    }
    be(async () => {
      try {
        const [c, o] = await Promise.all([
          T("frappe.client.get", { doctype: "Watch Settings", name: "Watch Settings" }),
          T("watch.api.settings.get_user_preferences")
        ]), a = c.message;
        a && Object.keys(n).forEach((B) => {
          a[B] !== void 0 && (n[B] = a[B]);
        });
        const y = o.message;
        y && (b.weekly_hour_target = y.weekly_hour_target ?? 0, b.enable_keyboard_shortcuts = y.enable_keyboard_shortcuts ?? 1, b.extension_token_active = !!y.extension_token_active);
      } catch (c) {
        h.value = c?.message || t("Failed to load settings");
      } finally {
        O.value = !1;
      }
    });
    async function oe() {
      $.value = !0, W.value = "", A.value = !1;
      try {
        await T("watch.api.settings.save_user_preferences", {
          weekly_hour_target: b.weekly_hour_target,
          enable_keyboard_shortcuts: b.enable_keyboard_shortcuts
        }), A.value = !0, setTimeout(() => A.value = !1, 2500);
      } catch (c) {
        W.value = c?.message || t("Failed to save");
      } finally {
        $.value = !1;
      }
    }
    async function J() {
      f.value = !0, h.value = "", E.value = !1;
      try {
        await T("frappe.client.set_value", {
          doctype: "Watch Settings",
          name: "Watch Settings",
          fieldname: { ...n }
        }), E.value = !0, setTimeout(() => E.value = !1, 2500);
      } catch (c) {
        h.value = c?.message || t("Failed to save");
      } finally {
        f.value = !1;
      }
    }
    async function ae() {
      V.value = !0, P.value = "", R.value = "";
      try {
        const c = await T("watch.api.settings.generate_extension_token");
        R.value = c.message?.token ?? "", b.extension_token_active = !0;
      } catch (c) {
        P.value = c?.message || t("Failed to generate token");
      } finally {
        V.value = !1;
      }
    }
    async function ne() {
      if (confirm(t("Revoke the browser extension token? The extension will be disconnected."))) {
        j.value = !0, P.value = "";
        try {
          await T("watch.api.settings.revoke_extension_token"), b.extension_token_active = !1, R.value = "";
        } catch (c) {
          P.value = c?.message || t("Failed to revoke token");
        } finally {
          j.value = !1;
        }
      }
    }
    function le() {
      navigator.clipboard.writeText(R.value), q.value = !0, setTimeout(() => q.value = !1, 2e3);
    }
    async function Q(c, o, a) {
      o.value = !0, a.value = null;
      try {
        const y = await T(`watch.api.integrations.test_${c}`);
        a.value = { ok: y.message?.success ?? !1, msg: y.message?.message ?? "" };
      } catch (y) {
        a.value = { ok: !1, msg: y?.message || t("Test failed") };
      } finally {
        o.value = !1;
      }
    }
    function de() {
      Q("slack", X, L);
    }
    function ce() {
      Q("linear", Z, G);
    }
    function ie() {
      Q("github", z, Y);
    }
    function ge(c, o) {
      n[c] = o ? 1 : 0;
    }
    function N(c, o) {
      n[c] = o ? 1 : 0;
    }
    async function ue() {
      let c = "", o = "";
      const a = /* @__PURE__ */ new Date();
      S.value === "this_year" ? (c = `${a.getFullYear()}-01-01`, o = a.toISOString().slice(0, 10)) : S.value === "last_year" ? (c = `${a.getFullYear() - 1}-01-01`, o = `${a.getFullYear() - 1}-12-31`) : S.value === "custom" && (c = F.value, o = I.value), window.open(
        `/api/method/watch.api.export.download_csv?from_date=${c}&to_date=${o}`,
        "_blank"
      );
    }
    return (c, o) => O.value ? (l(), d("div", me, [...o[24] || (o[24] = [
      e("div", { class: "h-6 w-6 animate-spin rounded-full border-2 border-accent-600 border-t-transparent" }, null, -1)
    ])])) : h.value && !n ? (l(), d("p", ve, r(h.value), 1)) : (l(), d(w, { key: 2 }, [
      e("nav", fe, [
        (l(), d(w, null, D(te, (a, y) => e("button", {
          key: a.label,
          class: M(["relative px-3 py-2 text-sm font-medium transition-colors", v.value === y ? "text-gray-900 dark:text-white" : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"]),
          onClick: (B) => v.value = y
        }, [
          re(r(a.label) + " ", 1),
          v.value === y ? (l(), d("span", Se)) : g("", !0)
        ], 10, we)), 64))
      ]),
      v.value === 0 ? (l(), d("div", Te, [
        e("div", Ce, [
          e("h2", Ee, r(s(t)("Personal Settings")), 1),
          e("p", Re, r(s(t)("Only you can see these.")), 1),
          e("div", Ve, [
            e("div", Pe, [
              e("div", Ne, [
                e("label", De, r(s(t)("Weekly hour target")), 1),
                e("p", Ue, r(s(t)("0 = no target (progress bar hidden).")), 1)
              ]),
              e("div", Oe, [
                u(e("input", {
                  "onUpdate:modelValue": o[0] || (o[0] = (a) => b.weekly_hour_target = a),
                  type: "number",
                  min: "0",
                  step: "1",
                  class: "w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
                }, null, 512), [
                  [
                    _,
                    b.weekly_hour_target,
                    void 0,
                    { number: !0 }
                  ]
                ]),
                e("span", Fe, r(s(t)("hours")), 1)
              ])
            ]),
            e("div", Ie, [
              e("label", Me, r(s(t)("Keyboard shortcuts")), 1),
              e("label", $e, [
                e("input", {
                  type: "checkbox",
                  checked: !!b.enable_keyboard_shortcuts,
                  class: "h-4 w-4 rounded accent-accent-600 dark:accent-accent-400",
                  onChange: o[1] || (o[1] = (a) => b.enable_keyboard_shortcuts = a.target.checked ? 1 : 0)
                }, null, 40, Ae),
                e("span", We, r(s(t)("Enabled")), 1)
              ])
            ])
          ]),
          e("div", je, [
            e("button", {
              disabled: $.value,
              class: "rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900 hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50",
              onClick: oe
            }, r($.value ? s(t)("Saving…") : s(t)("Save")), 9, Le),
            A.value ? (l(), d("span", Ge, r(s(t)("Saved")), 1)) : g("", !0),
            W.value ? (l(), d("span", Ye, r(W.value), 1)) : g("", !0)
          ])
        ]),
        e("div", Be, [
          e("h2", He, r(s(t)("Browser Extension")), 1),
          e("p", Ke, r(s(t)("Connect the Watch browser extension to this site.")), 1),
          e("div", qe, [
            e("div", Xe, [
              e("span", Ze, r(s(t)("Status")) + ":", 1),
              e("span", {
                class: M(["text-sm font-medium", b.extension_token_active ? "text-green-600 dark:text-green-400" : "text-gray-400 dark:text-gray-500"])
              }, r(b.extension_token_active ? s(t)("Token active") : s(t)("Not connected")), 3)
            ]),
            R.value ? (l(), d("div", ze, [
              e("div", Je, [
                e("input", {
                  type: "text",
                  value: R.value,
                  readonly: "",
                  class: "flex-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-3 py-2 text-xs font-mono text-gray-900 dark:text-white select-all",
                  onFocus: o[2] || (o[2] = (a) => a.target.select())
                }, null, 40, Qe),
                e("button", {
                  class: "rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors",
                  onClick: le
                }, r(q.value ? s(t)("Copied") : s(t)("Copy")), 1)
              ]),
              e("p", et, r(s(t)("This token will not be shown again. Paste it into the extension setup screen.")), 1)
            ])) : g("", !0),
            P.value ? (l(), d("p", tt, r(P.value), 1)) : g("", !0),
            e("div", at, [
              b.extension_token_active ? (l(), d(w, { key: 1 }, [
                e("button", {
                  disabled: V.value,
                  class: "rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50",
                  onClick: ae
                }, r(V.value ? s(t)("Generating…") : s(t)("Regenerate token")), 9, rt),
                e("button", {
                  disabled: j.value,
                  class: "rounded-lg border border-red-300 dark:border-red-700 px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50",
                  onClick: ne
                }, r(j.value ? s(t)("Revoking…") : s(t)("Revoke access")), 9, ot)
              ], 64)) : (l(), d("button", {
                key: 0,
                disabled: V.value,
                class: "rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900 hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50",
                onClick: ae
              }, r(V.value ? s(t)("Generating…") : s(t)("Generate extension token")), 9, st))
            ])
          ])
        ])
      ])) : v.value === 1 ? (l(), d("div", nt, [
        e("div", lt, [
          e("h2", dt, r(s(t)("Time Tracking")), 1),
          e("div", ct, [
            e("div", it, [
              e("label", gt, r(s(t)("Default entry type")), 1),
              u(e("select", {
                "onUpdate:modelValue": o[3] || (o[3] = (a) => n.default_entry_type = a),
                class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, [
                (l(), d(w, null, D(x, (a) => e("option", {
                  key: a.value,
                  value: a.value
                }, r(s(t)(a.label)), 9, ut)), 64))
              ], 512), [
                [H, n.default_entry_type]
              ])
            ]),
            e("div", yt, [
              e("div", bt, [
                e("label", xt, r(s(t)("Lock entries older than (days)")), 1),
                e("p", _t, r(s(t)("0 = disabled.")), 1)
              ]),
              u(e("input", {
                "onUpdate:modelValue": o[4] || (o[4] = (a) => n.lock_entries_older_than = a),
                type: "number",
                min: "0",
                class: "w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [
                  _,
                  n.lock_entries_older_than,
                  void 0,
                  { number: !0 }
                ]
              ])
            ]),
            e("div", kt, [
              e("div", pt, [
                e("label", ht, r(s(t)("Auto-stop timer after (hours)")), 1),
                e("p", mt, r(s(t)("0 = disabled.")), 1)
              ]),
              u(e("input", {
                "onUpdate:modelValue": o[5] || (o[5] = (a) => n.auto_stop_timer_after = a),
                type: "number",
                min: "0",
                class: "w-20 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [
                  _,
                  n.auto_stop_timer_after,
                  void 0,
                  { number: !0 }
                ]
              ])
            ]),
            e("div", null, [
              e("label", vt, r(s(t)("Work days")), 1),
              e("div", ft, [
                (l(), d(w, null, D(m, (a) => e("label", {
                  key: a.key,
                  class: "flex flex-col items-center gap-1 cursor-pointer"
                }, [
                  e("input", {
                    type: "checkbox",
                    checked: !!n[a.key],
                    class: "h-4 w-4 rounded accent-accent-600 dark:accent-accent-400",
                    onChange: (y) => ge(a.key, y.target.checked)
                  }, null, 40, wt),
                  e("span", St, r(s(t)(a.label)), 1)
                ])), 64))
              ])
            ])
          ])
        ]),
        e("div", Tt, [
          e("button", {
            disabled: f.value,
            class: "rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900 hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50",
            onClick: J
          }, r(f.value ? s(t)("Saving…") : s(t)("Save")), 9, Ct),
          E.value ? (l(), d("span", Et, r(s(t)("Saved")), 1)) : g("", !0),
          h.value ? (l(), d("span", Rt, r(h.value), 1)) : g("", !0)
        ])
      ])) : v.value === 2 ? (l(), d("div", Vt, [
        e("div", Pt, [
          e("div", Nt, [
            e("div", null, [
              e("h2", Dt, r(s(t)("ERPNext Bridge")), 1),
              e("p", Ut, r(s(t)("One-way sync of billable entries to ERPNext Timesheets.")), 1)
            ]),
            e("label", Ot, [
              e("input", {
                type: "checkbox",
                checked: !!n.enable_erpnext_bridge,
                class: "h-4 w-4 rounded accent-accent-600 dark:accent-accent-400",
                onChange: o[6] || (o[6] = (a) => N("enable_erpnext_bridge", a.target.checked))
              }, null, 40, Ft),
              e("span", It, r(s(t)("Enable")), 1)
            ])
          ]),
          n.enable_erpnext_bridge ? (l(), d("div", Mt, [
            e("div", null, [
              e("label", $t, r(s(t)("ERPNext site URL")), 1),
              u(e("input", {
                "onUpdate:modelValue": o[7] || (o[7] = (a) => n.erpnext_site_url = a),
                type: "url",
                placeholder: "https://erp.example.com",
                class: "w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [_, n.erpnext_site_url]
              ])
            ]),
            e("div", At, [
              e("div", null, [
                e("label", Wt, r(s(t)("Sync mode")), 1),
                u(e("select", {
                  "onUpdate:modelValue": o[8] || (o[8] = (a) => n.sync_mode = a),
                  class: "w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
                }, [
                  (l(), d(w, null, D(C, (a) => e("option", {
                    key: a.value,
                    value: a.value
                  }, r(s(t)(a.label)), 9, jt)), 64))
                ], 512), [
                  [H, n.sync_mode]
                ])
              ]),
              n.sync_mode === "scheduled" ? (l(), d("div", Lt, [
                e("label", Gt, r(s(t)("Sync interval")), 1),
                u(e("select", {
                  "onUpdate:modelValue": o[9] || (o[9] = (a) => n.sync_interval = a),
                  class: "w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
                }, [
                  (l(), d(w, null, D(p, (a) => e("option", {
                    key: a.value,
                    value: a.value
                  }, r(s(t)(a.label)), 9, Yt)), 64))
                ], 512), [
                  [H, n.sync_interval]
                ])
              ])) : g("", !0)
            ]),
            e("div", null, [
              e("label", Bt, r(s(t)("Default activity type")), 1),
              u(e("input", {
                "onUpdate:modelValue": o[10] || (o[10] = (a) => n.default_activity_type = a),
                type: "text",
                placeholder: "Development",
                class: "w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [_, n.default_activity_type]
              ])
            ]),
            e("label", Ht, [
              e("input", {
                type: "checkbox",
                checked: !!n.sync_billable_only,
                class: "h-4 w-4 rounded accent-accent-600 dark:accent-accent-400",
                onChange: o[11] || (o[11] = (a) => N("sync_billable_only", a.target.checked))
              }, null, 40, Kt),
              e("span", qt, r(s(t)("Sync billable entries only")), 1)
            ]),
            e("label", Xt, [
              e("input", {
                type: "checkbox",
                checked: !!n.map_project_tags,
                class: "h-4 w-4 rounded accent-accent-600 dark:accent-accent-400",
                onChange: o[12] || (o[12] = (a) => N("map_project_tags", a.target.checked))
              }, null, 40, Zt),
              e("span", zt, r(s(t)("Map project tags to ERPNext")), 1)
            ])
          ])) : g("", !0)
        ]),
        e("div", Jt, [
          e("button", {
            disabled: f.value,
            class: "rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900 hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50",
            onClick: J
          }, r(f.value ? s(t)("Saving…") : s(t)("Save")), 9, Qt),
          E.value ? (l(), d("span", ea, r(s(t)("Saved")), 1)) : g("", !0),
          h.value ? (l(), d("span", ta, r(h.value), 1)) : g("", !0)
        ])
      ])) : v.value === 3 ? (l(), d("div", aa, [
        e("div", sa, [
          e("h2", ra, r(s(t)("Slack")), 1),
          e("div", oa, [
            e("div", null, [
              e("label", na, r(s(t)("Webhook URL")), 1),
              u(e("input", {
                "onUpdate:modelValue": o[13] || (o[13] = (a) => n.slack_webhook_url = a),
                type: "url",
                placeholder: "https://hooks.slack.com/services/...",
                class: "w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [_, n.slack_webhook_url]
              ])
            ]),
            e("label", la, [
              e("input", {
                type: "checkbox",
                checked: !!n.slack_notify_on_stop,
                class: "h-4 w-4 rounded accent-accent-600 dark:accent-accent-400",
                onChange: o[14] || (o[14] = (a) => N("slack_notify_on_stop", a.target.checked))
              }, null, 40, da),
              e("span", ca, r(s(t)("Notify when timer stops")), 1)
            ]),
            e("div", null, [
              e("label", ia, r(s(t)("Message template")), 1),
              u(e("textarea", {
                "onUpdate:modelValue": o[15] || (o[15] = (a) => n.slack_message_template = a),
                rows: "3",
                class: "w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [_, n.slack_message_template]
              ])
            ]),
            e("div", ga, [
              e("button", {
                disabled: X.value || !n.slack_webhook_url,
                class: "rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50",
                onClick: de
              }, r(X.value ? s(t)("Testing…") : s(t)("Test Connection")), 9, ua),
              L.value ? (l(), d("span", {
                key: 0,
                class: M(["text-xs", L.value.ok ? "text-green-600" : "text-red-500"])
              }, r(L.value.msg), 3)) : g("", !0)
            ])
          ])
        ]),
        e("div", ya, [
          e("h2", ba, r(s(t)("Linear")), 1),
          e("div", xa, [
            e("div", null, [
              e("label", _a, r(s(t)("API Key")), 1),
              u(e("input", {
                "onUpdate:modelValue": o[16] || (o[16] = (a) => n.linear_api_key = a),
                type: "password",
                class: "w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [_, n.linear_api_key]
              ])
            ]),
            e("label", ka, [
              e("input", {
                type: "checkbox",
                checked: !!n.linear_post_comment,
                class: "h-4 w-4 rounded accent-accent-600 dark:accent-accent-400",
                onChange: o[17] || (o[17] = (a) => N("linear_post_comment", a.target.checked))
              }, null, 40, pa),
              e("span", ha, r(s(t)("Post time entry as comment on issue")), 1)
            ]),
            e("div", ma, [
              e("button", {
                disabled: Z.value || !n.linear_api_key,
                class: "rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50",
                onClick: ce
              }, r(Z.value ? s(t)("Testing…") : s(t)("Test Connection")), 9, va),
              G.value ? (l(), d("span", {
                key: 0,
                class: M(["text-xs", G.value.ok ? "text-green-600" : "text-red-500"])
              }, r(G.value.msg), 3)) : g("", !0)
            ])
          ])
        ]),
        e("div", fa, [
          e("h2", wa, r(s(t)("GitHub")), 1),
          e("div", Sa, [
            e("div", null, [
              e("label", Ta, r(s(t)("Personal Access Token")), 1),
              u(e("input", {
                "onUpdate:modelValue": o[18] || (o[18] = (a) => n.github_token = a),
                type: "password",
                class: "w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [_, n.github_token]
              ])
            ]),
            e("div", null, [
              e("label", Ca, r(s(t)("Default repository")), 1),
              u(e("input", {
                "onUpdate:modelValue": o[19] || (o[19] = (a) => n.github_default_repo = a),
                type: "text",
                placeholder: "owner/repo",
                class: "w-full max-w-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 512), [
                [_, n.github_default_repo]
              ])
            ]),
            e("label", Ea, [
              e("input", {
                type: "checkbox",
                checked: !!n.github_post_comment,
                class: "h-4 w-4 rounded accent-accent-600 dark:accent-accent-400",
                onChange: o[20] || (o[20] = (a) => N("github_post_comment", a.target.checked))
              }, null, 40, Ra),
              e("span", Va, r(s(t)("Post time entry as comment on issue")), 1)
            ]),
            e("div", Pa, [
              e("button", {
                disabled: z.value || !n.github_token,
                class: "rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50",
                onClick: ie
              }, r(z.value ? s(t)("Testing…") : s(t)("Test Connection")), 9, Na),
              Y.value ? (l(), d("span", {
                key: 0,
                class: M(["text-xs", Y.value.ok ? "text-green-600" : "text-red-500"])
              }, r(Y.value.msg), 3)) : g("", !0)
            ])
          ])
        ]),
        e("div", Da, [
          e("button", {
            disabled: f.value,
            class: "rounded-lg bg-accent-600 dark:bg-accent-400 px-4 py-2 text-sm font-medium text-white dark:text-gray-900 hover:bg-accent-700 dark:hover:bg-accent-300 transition-colors disabled:opacity-50",
            onClick: J
          }, r(f.value ? s(t)("Saving…") : s(t)("Save")), 9, Ua),
          E.value ? (l(), d("span", Oa, r(s(t)("Saved")), 1)) : g("", !0),
          h.value ? (l(), d("span", Fa, r(h.value), 1)) : g("", !0)
        ])
      ])) : v.value === 4 ? (l(), d("div", Ia, [
        e("div", Ma, [
          e("h2", $a, r(s(t)("Export My Data")), 1),
          e("p", Aa, r(s(t)("Download your time entries as a CSV file.")), 1),
          e("div", Wa, [
            e("div", null, [
              e("label", ja, r(s(t)("Date range")), 1),
              u(e("select", {
                "onUpdate:modelValue": o[21] || (o[21] = (a) => S.value = a),
                class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, [
                (l(), d(w, null, D(U, (a) => e("option", {
                  key: a.value,
                  value: a.value
                }, r(s(t)(a.label)), 9, La)), 64))
              ], 512), [
                [H, S.value]
              ])
            ]),
            S.value === "custom" ? (l(), d("div", Ga, [
              u(e("input", {
                "onUpdate:modelValue": o[22] || (o[22] = (a) => F.value = a),
                type: "date",
                max: I.value || void 0,
                class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 8, Ya), [
                [_, F.value]
              ]),
              o[25] || (o[25] = e("span", { class: "text-gray-400 text-sm" }, "→", -1)),
              u(e("input", {
                "onUpdate:modelValue": o[23] || (o[23] = (a) => I.value = a),
                type: "date",
                min: F.value || void 0,
                class: "rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-accent-500 dark:focus:ring-accent-400"
              }, null, 8, Ba), [
                [_, I.value]
              ])
            ])) : g("", !0),
            e("button", {
              disabled: S.value === "custom" && (!F.value || !I.value),
              class: "flex items-center gap-1.5 rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50",
              onClick: ue
            }, [
              xe(s(he), {
                class: "w-4 h-4",
                "aria-hidden": "true"
              }),
              re(" " + r(s(t)("Download CSV")), 1)
            ], 8, Ha)
          ])
        ])
      ])) : g("", !0)
    ], 64));
  }
});
export {
  qa as WatchSettings
};
