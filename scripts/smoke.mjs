#!/usr/bin/env node
// KRChar proof test — run against a local `wrangler dev` or the deployed worker.
//
//   node scripts/smoke.mjs http://127.0.0.1:8799
//   ADMIN_TOKEN=... node scripts/smoke.mjs https://krchar-d1.fred0928.workers.dev
//
// Owner is always `smoke-test`, so the author's weights are untouched.
// Cleanup afterwards (the API has no delete route):
//   wrangler d1 execute krchar --remote --command="DELETE FROM card_stats WHERE owner='smoke-test'; DELETE FROM reviews WHERE owner='smoke-test';"

const BASE = process.argv[2] || 'http://127.0.0.1:8799';
const TOKEN = process.env.ADMIN_TOKEN || 'dev-token';
const OWNER = 'smoke-test';
const CP_SYL = 'AC00';   // 가  · L3 · keys rk · rr ga
const CP_JAMO = '3131';  // ㄱ  · L1c · keys r · rr g

let pass = 0;
const fails = [];
const ok = (name, cond, extra = '') => {
  if (cond) { pass += 1; console.log(`  ✓ ${name}`); }
  else { fails.push(name); console.log(`  ✗ ${name} ${extra}`); }
};

async function get(path) {
  const r = await fetch(BASE + path);
  return { status: r.status, body: await r.json().catch(() => ({})) };
}
async function post(path, body, headers = {}) {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });
  return { status: r.status, body: await r.json().catch(() => ({})) };
}
const cardOf = (cards, cp) => cards.find((c) => c.cp === cp);

(async () => {
  console.log(`target ${BASE}  owner ${OWNER}`);

  // 1 ─ health
  const health = await get('/api/health');
  ok('1 health 200 and 833 cards', health.status === 200 && health.body.cards === 833, JSON.stringify(health.body));

  // 2 ─ cumulative level sizes
  const sets = {};
  for (const [level, want] of [['L1', 26], ['L2', 37], ['L3', 211], ['L4', 366]]) {
    const r = await get(`/api/cards?level=${level}&owner=${OWNER}`);
    sets[level] = r.body.cards || [];
    ok(`2 ${level} returns ${want}`, r.status === 200 && r.body.count === want, `got ${r.body.count}`);
  }

  // 3 ─ nothing closed, and higher level ⊇ lower level
  const forbidden = [];
  for (const [level, cards] of Object.entries(sets)) {
    for (const c of cards) if (c.category.startsWith('L0') || ['L5', 'L6'].includes(c.category)) forbidden.push(`${level}:${c.hangul}`);
  }
  ok('3 no L0/L5/L6 in any pool', forbidden.length === 0, forbidden.slice(0, 5).join(','));
  const cpSet = (level) => new Set(sets[level].map((c) => c.cp));
  const [s1, s2, s3, s4] = [cpSet('L1'), cpSet('L2'), cpSet('L3'), cpSet('L4')];
  const subset = (a, b) => [...a].every((x) => b.has(x));
  ok('3 L1 ⊆ L2 ⊆ L3 ⊆ L4', subset(s1, s2) && subset(s2, s3) && subset(s3, s4));

  // 4 ─ invalid level rejected
  const badLevel = await get('/api/cards?level=L0');
  ok('4 level=L0 rejected', badLevel.status === 400, `status ${badLevel.status}`);

  // baseline weight for the smoke owner
  const before = cardOf(sets.L4, CP_SYL);
  if (before.weight !== 12) {
    console.log(`\n! ${OWNER} already has weight ${before.weight} on ${CP_SYL} — clean up first:`);
    console.log(`  npx wrangler d1 execute krchar --local --command="DELETE FROM card_stats WHERE owner='${OWNER}'; DELETE FROM reviews WHERE owner='${OWNER}';"`);
    process.exit(1);
  }

  const statsBefore = await get(`/api/stats?owner=${OWNER}&level=L4`);
  const todayBefore = statsBefore.body.today ? statsBefore.body.today.count : 0;

  // 5 ─ wrong: 12 -> 15
  const w1 = await post('/api/review', { owner: OWNER, cp: CP_SYL, result: 'wrong', mode: 'rr' });
  ok('5 wrong 12 -> 15', w1.status === 200 && w1.body.weight === 15, JSON.stringify(w1.body));

  // 6 ─ clamped at 15
  const w2 = await post('/api/review', { owner: OWNER, cp: CP_SYL, result: 'wrong', mode: 'rr' });
  ok('6 weight clamped at 15', w2.status === 200 && w2.body.weight === 15, JSON.stringify(w2.body));

  // 7 ─ correct: 15 -> 14
  const w3 = await post('/api/review', { owner: OWNER, cp: CP_SYL, result: 'correct', mode: 'dubeolsik' });
  ok('7 correct 15 -> 14', w3.status === 200 && w3.body.weight === 14, JSON.stringify(w3.body));

  // 8 ─ keys that do not type the character are rejected and change nothing
  const badKeys = await post('/api/card', { owner: OWNER, cp: CP_SYL, keys: 'xx' }, { 'X-Admin-Token': TOKEN });
  const afterBad = await get(`/api/cards?level=L4&owner=${OWNER}`);
  const unchanged = cardOf(afterBad.body.cards, CP_SYL).keys;
  ok('8 bad keys rejected (400) and DB unchanged', badKeys.status === 400 && unchanged === 'rk',
    `status ${badKeys.status} keys ${unchanged}`);

  // 9 ─ edit requires the admin token, and restores the memo afterwards
  const origMemo = cardOf(afterBad.body.cards, CP_SYL).memo;
  const noToken = await post('/api/card', { owner: OWNER, cp: CP_SYL, memo: 'smoke' });
  ok('9 edit without token -> 401', noToken.status === 401, `status ${noToken.status}`);
  const withToken = await post('/api/card', { owner: OWNER, cp: CP_SYL, memo: `${origMemo} [smoke]` },
    { 'X-Admin-Token': TOKEN });
  const seen = cardOf((await get(`/api/cards?level=L4&owner=${OWNER}`)).body.cards, CP_SYL).memo;
  await post('/api/card', { owner: OWNER, cp: CP_SYL, memo: origMemo }, { 'X-Admin-Token': TOKEN });
  const restored = cardOf((await get(`/api/cards?level=L4&owner=${OWNER}`)).body.cards, CP_SYL).memo;
  ok('9 token edit works and memo restored',
    withToken.status === 200 && seen.endsWith('[smoke]') && restored === origMemo,
    `status ${withToken.status} seen=${JSON.stringify(seen)}`);

  // 10 ─ today's counters moved by exactly the three reviews we just posted
  const statsAfter = await get(`/api/stats?owner=${OWNER}&level=L4`);
  const t = statsAfter.body.today || {};
  ok('10 today.count +3', t.count === todayBefore + 3, `${todayBefore} -> ${t.count}`);
  ok('10 mode mix has both modes',
    (statsAfter.body.review_mode_mix.rr || 0) >= 2 && (statsAfter.body.review_mode_mix.dubeolsik || 0) >= 1,
    JSON.stringify(statsAfter.body.review_mode_mix));

  // jamo sanity: ㄱ exists in the L1 pool
  ok('extra: ㄱ in L1 pool', !!cardOf(sets.L1, CP_JAMO));

  console.log(`\n${pass} passed, ${fails.length} failed`);
  if (fails.length) { console.log('FAILED:', fails.join(' | ')); process.exit(1); }
  console.log('cleanup:');
  console.log(`  npx wrangler d1 execute krchar --local --command="DELETE FROM card_stats WHERE owner='${OWNER}'; DELETE FROM reviews WHERE owner='${OWNER}';"`);
  console.log('ALL PASS');
})();
