const $ = (id) => document.getElementById(id);
const consoleEl = $("console");

function log(text, cls = "") {
  const line = document.createElement("div");
  line.className = `line ${cls}`;
  line.textContent = text;
  consoleEl.prepend(line);
}

const API_KEY = "dev-operator-key";

async function api(path, opts = {}) {
  const headers = {
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY,
    ...(opts.headers || {}),
  };
  const res = await fetch(path, { ...opts, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "request failed");
  return data;
}

function stroops(n) {
  return `${n.toLocaleString()} stroops`;
}

function render(state) {
  $("ledger").textContent = `ledger ${state.ledger.toLocaleString()}`;
  $("remain").textContent = stroops(state.remaining_stroops);
  $("rules").textContent = state.rule_count;

  $("policy").innerHTML = (state.rules || [])
    .map(
      (r) => `<article class="card">
        <strong>${r.name}</strong>
        <small>${r.method} · cap ${stroops(r.max_spend_per_period)} · max ${r.max_calls_per_period} calls</small>
      </article>`
    )
    .join("");

  $("market").innerHTML = (state.resources || [])
    .map(
      (r) => `<article class="card">
        <strong>${r.name}</strong>
        <small>${r.id} · ${r.price} stroops / call</small>
      </article>`
    )
    .join("");

  $("bars").innerHTML = (state.rules || [])
    .map(
      (r) => `<div>
        <small>${r.name} · ${r.spent}/${r.max_spend_per_period} used</small>
        <div class="bar"><i style="width:${Math.min(100, r.used_pct)}%"></i></div>
      </div>`
    )
    .join("");

  $("audit").innerHTML = (state.audit || [])
    .map((e) => {
      const cls = e.decision === "denied" ? "denied" : "approved";
      const extra = e.tx_hash ? ` tx ${e.tx_hash}` : "";
      return `<div class="${cls}">${e.decision} · ${e.reason} · ${e.resource_id || "policy"} · ${e.amount}${extra}</div>`;
    })
    .join("");
}

async function refresh() {
  render(await api("/api/state"));
}

async function discover() {
  const query = $("query").value;
  log(`> discover_resources("${query}")`, "dim");
  const data = await api("/api/discover", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
  log(JSON.stringify(data.results, null, 2), "ok");
}

async function budget() {
  log("> check_budget()", "dim");
  const data = await api("/api/budget");
  log(JSON.stringify(data, null, 2), "ok");
  await refresh();
}

async function pay(id) {
  log(`> pay_and_call("${id}", "{}")`, "dim");
  const data = await api("/api/pay", {
    method: "POST",
    body: JSON.stringify({ resource_id: id, params: "{}" }),
  });
  log(JSON.stringify(data, null, 2), data.ok ? "ok" : "err");
  await refresh();
  return data;
}

$("discover").onclick = discover;
$("budget-btn").onclick = budget;
$("reset").onclick = async () => {
  await api("/api/reset", { method: "POST" });
  consoleEl.innerHTML = "";
  $("script").innerHTML = "Demo reset. Policy regenerated from 75 synthetic transactions.";
  await refresh();
};
document.querySelectorAll("[data-pay]").forEach((btn) => {
  btn.onclick = () => pay(btn.dataset.pay);
});

const PITCH = [
  {
    say: "1/6 Simulate observed agent traffic, then generate a least-privilege policy.",
    run: refresh,
  },
  {
    say: "2/6 The agent discovers a paid weather oracle over MCP.",
    run: async () => {
      $("query").value = "weather";
      await discover();
    },
  },
  {
    say: "3/6 It checks remaining budget on the smart account before spending.",
    run: budget,
  },
  {
    say: "4/6 pay_and_call succeeds under the weather cap. Spend is recorded on-chain.",
    run: () => pay("weather-oracle"),
  },
  {
    say: "5/6 A second weather call exceeds the p95-derived cap and is denied.",
    run: () => pay("weather-oracle"),
  },
  {
    say: "6/6 Price feed is still allowed — policies are scoped per vendor, not a global wallet.",
    run: () => pay("price-feed"),
  },
];

$("pitch").onclick = async () => {
  $("pitch").disabled = true;
  try {
    await api("/api/reset", { method: "POST" });
    consoleEl.innerHTML = "";
    for (const step of PITCH) {
      $("script").innerHTML = step.say;
      await step.run();
      await new Promise((r) => setTimeout(r, 1600));
    }
    $("script").innerHTML =
      "Done. Every approve/deny is an <strong>auth_decision</strong> event. Reset and run again.";
  } finally {
    $("pitch").disabled = false;
  }
};

refresh();
