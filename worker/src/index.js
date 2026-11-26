// KRChar — Korean Dubeolsik drill API (Cloudflare Worker + D1)
//
// Endpoints
//   GET  /api/health                       → { ok, cards }
//   GET  /api/cards?level=L2&owner=fred0928 → cumulative level set + per-owner weight
//   GET  /api/cards?scope=all              → every card (used by /table)
//   GET  /api/stats?owner=fred0928         → totals, today, category counts, mode mix
//   POST /api/review                       → one answer, updates weight + reviews
//   POST /api/card                         → edit content (needs X-Admin-Token)

const LEVELS = {
  L1: ['L1c', 'L1v', 'L1'],
  L2: ['L1c', 'L1v', 'L1', 'L2'],
  L3: ['L1c', 'L1v', 'L1', 'L2', 'L3'],
  L4: ['L1c', 'L1v', 'L1', 'L2', 'L3', 'L4'],
};
const OPEN_CATEGORIES = ['L1c', 'L1v', 'L1', 'L2', 'L3', 'L4'];
const DEFAULT_OWNER = 'fred0928';

// ── Dubeolsik: keys -> character (same table as code/validate_krchar.py) ────────
const KEY = {
  q: 'ㅂ', w: 'ㅈ', e: 'ㄷ', r: 'ㄱ', t: 'ㅅ', y: 'ㅛ', u: 'ㅕ', i: 'ㅑ', o: 'ㅐ', p: 'ㅔ',
  a: 'ㅁ', s: 'ㄴ', d: 'ㅇ', f: 'ㄹ', g: 'ㅎ', h: 'ㅗ', j: 'ㅓ', k: 'ㅏ', l: 'ㅣ',
  z: 'ㅋ', x: 'ㅌ', c: 'ㅊ', v: 'ㅍ', b: 'ㅠ', n: 'ㅜ', m: 'ㅡ',
  Q: 'ㅃ', W: 'ㅉ', E: 'ㄸ', R: 'ㄲ', T: 'ㅆ', O: 'ㅒ', P: 'ㅖ',
};
const INI = [...'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'];
const MED = [...'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'];
const FIN = ['', ...'ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ'];
const VV = { 'ㅗㅏ': 'ㅘ', 'ㅗㅐ': 'ㅙ', 'ㅗㅣ': 'ㅚ', 'ㅜㅓ': 'ㅝ', 'ㅜㅔ': 'ㅞ', 'ㅜㅣ': 'ㅟ', 'ㅡㅣ': 'ㅢ', 'ㅑㅣ': 'ㅒ', 'ㅕㅣ': 'ㅖ', 'ㅏㅣ': 'ㅐ', 'ㅓㅣ': 'ㅔ' };
const CC = { 'ㄱㅅ': 'ㄳ', 'ㄴㅈ': 'ㄵ', 'ㄴㅎ': 'ㄶ', 'ㄹㄱ': 'ㄺ', 'ㄹㅁ': 'ㄻ', 'ㄹㅂ': 'ㄼ', 'ㄹㅅ': 'ㄽ', 'ㄹㅌ': 'ㄾ', 'ㄹㅍ': 'ㄿ', 'ㄹㅎ': 'ㅀ', 'ㅂㅅ': 'ㅄ' };

const syllable = (i, m, f = '') => String.fromCharCode(0xac00 + (INI.indexOf(i) * 21 + MED.indexOf(m)) * 28 + FIN.indexOf(f));

/** Rebuild the character a key sequence would type, or null if it types something else. */
function compose(keys) {
  if (!keys || [...keys].some((c) => !(c in KEY))) return null;
  const j = [...keys].map((c) => KEY[c]);
  if (j.length === 1) return j[0];
  if (MED.includes(j[0])) {                     // bare vowel, possibly compound
    let m = j[0];
    for (const n of j.slice(1)) {
      if (MED.includes(n) && VV[m + n]) m = VV[m + n]; else return null;
    }
    return m;
  }
  if (j.length < 2 || !INI.includes(j[0]) || !MED.includes(j[1])) return null;
  let m = j[1];
  let rest = j.slice(2);
  if (rest.length && MED.includes(rest[0]) && VV[m + rest[0]]) { m = VV[m + rest[0]]; rest = rest.slice(1); }
  if (!rest.length) return syllable(j[0], m);
  if (rest.length === 1 && FIN.includes(rest[0]) && rest[0]) return syllable(j[0], m, rest[0]);
  if (rest.length === 2 && CC[rest[0] + rest[1]]) return syllable(j[0], m, CC[rest[0] + rest[1]]);
  return null;
}

// ── helpers ───────────────────────────────────────────────────────────────────
const nowTaipei = () =>
  new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Taipei', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  }).format(new Date());

const clampWeight = (w) => Math.min(15, Math.max(1, w));

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });
}
const bad = (message, status = 400) => json({ error: message }, status);

const CARD_COLS = 'c.cp, c.hangul, c.category, c.rr, c.keys, c.memo, c.ord';

async function getWeight(env, owner, cp) {
  const row = await env.DB.prepare('SELECT weight FROM card_stats WHERE owner = ? AND cp = ?')
    .bind(owner, cp).first();
  return row ? row.weight : 12;
}

async function setWeight(env, owner, cp, weight, delta = { correct: 0, wrong: 0 }, ts = nowTaipei()) {
  const w = clampWeight(weight);
  await env.DB.prepare(
    `INSERT INTO card_stats (owner, cp, weight, correct, wrong, last) VALUES (?, ?, ?, ?, ?, ?)
     ON CONFLICT(owner, cp) DO UPDATE SET
       weight = excluded.weight,
       correct = card_stats.correct + excluded.correct,
       wrong = card_stats.wrong + excluded.wrong,
       last = excluded.last`,
  ).bind(owner, cp, w, delta.correct || 0, delta.wrong || 0, ts).run();
  return w;
}

// ── routes ────────────────────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    const owner = url.searchParams.get('owner') || DEFAULT_OWNER;

    try {
      if (path === '/api/health') {
        const { n } = await env.DB.prepare('SELECT COUNT(*) AS n FROM cards').first();
        return json({ ok: true, cards: n });
      }

      if (path === '/api/cards' && request.method === 'GET') {
        const scope = url.searchParams.get('scope');
        if (scope === 'all') {
          const { results } = await env.DB.prepare(
            `SELECT ${CARD_COLS}, COALESCE(cs.weight, 12) AS weight
             FROM cards c LEFT JOIN card_stats cs ON cs.cp = c.cp AND cs.owner = ?
             ORDER BY c.ord`,
          ).bind(owner).all();
          return json({ scope: 'all', count: results.length, cards: results });
        }
        const level = (url.searchParams.get('level') || 'L1').toUpperCase();
        const cats = LEVELS[level];
        if (!cats) return bad(`level must be one of ${Object.keys(LEVELS).join('/')}`);
        const placeholders = cats.map(() => '?').join(',');
        const { results } = await env.DB.prepare(
          `SELECT ${CARD_COLS}, COALESCE(cs.weight, 12) AS weight
           FROM cards c LEFT JOIN card_stats cs ON cs.cp = c.cp AND cs.owner = ?
           WHERE c.category IN (${placeholders})
           ORDER BY c.ord`,
        ).bind(owner, ...cats).all();
        return json({ level, categories: cats, count: results.length, cards: results });
      }

      if (path === '/api/stats' && request.method === 'GET') {
        const level = (url.searchParams.get('level') || 'L1').toUpperCase();
        const cats = LEVELS[level];
        if (!cats) return bad(`level must be one of ${Object.keys(LEVELS).join('/')}`);
        const today = nowTaipei().slice(0, 10);
        const { n: cards_total } = await env.DB.prepare('SELECT COUNT(*) AS n FROM cards').first();
        const { results: byCat } = await env.DB.prepare(
          'SELECT category, COUNT(*) AS n FROM cards GROUP BY category ORDER BY category',
        ).all();
        const { n: poolCount } = await env.DB.prepare(
          `SELECT COUNT(*) AS n FROM cards WHERE category IN (${cats.map(() => '?').join(',')})`,
        ).bind(...cats).first();
        const t = await env.DB.prepare(
          `SELECT COUNT(*) AS count,
                  SUM(CASE WHEN result = 'correct' THEN 1 ELSE 0 END) AS correct
           FROM reviews WHERE owner = ? AND action = 'review' AND substr(ts, 1, 10) = ?`,
        ).bind(owner, today).first();
        const { results: mix } = await env.DB.prepare(
          `SELECT mode, COUNT(*) AS n FROM reviews
           WHERE owner = ? AND action = 'review' AND substr(ts, 1, 10) = ? GROUP BY mode`,
        ).bind(owner, today).all();
        return json({
          owner,
          cards_total,
          pool: { level, count: poolCount },
          byCategory: Object.fromEntries(byCat.map((r) => [r.category, r.n])),
          today: {
            date: today,
            count: t.count || 0,
            correct: t.correct || 0,
            accuracy: t.count ? Math.round((t.correct / t.count) * 1000) / 10 : null,
          },
          review_mode_mix: Object.fromEntries(mix.map((r) => [r.mode || 'unknown', r.n])),
        });
      }

      if (path === '/api/review' && request.method === 'POST') {
        const body = await request.json().catch(() => null);
        if (!body) return bad('invalid JSON');
        const { cp, result, mode } = body;
        const who = body.owner || DEFAULT_OWNER;
        if (!cp) return bad('cp is required');
        if (!['correct', 'wrong'].includes(result)) return bad("result must be 'correct' or 'wrong'");
        if (!['rr', 'dubeolsik'].includes(mode)) return bad("mode must be 'rr' or 'dubeolsik'");

        const card = await env.DB.prepare('SELECT cp, hangul FROM cards WHERE cp = ?').bind(cp).first();
        if (!card) return bad('unknown cp', 404);

        const prev = await getWeight(env, who, cp);
        const ts = nowTaipei();
        const delta = result === 'wrong' ? 3 : -1;
        const weight = await setWeight(env, who, cp, prev + delta,
          result === 'wrong' ? { wrong: 1 } : { correct: 1 }, ts);
        await env.DB.prepare(
          `INSERT INTO reviews (ts, owner, cp, action, result, note, mode) VALUES (?, ?, ?, 'review', ?, '', ?)`,
        ).bind(ts, who, cp, result, mode).run();
        return json({ cp, result, mode, weight_before: prev, weight, ts });
      }

      if (path === '/api/card' && request.method === 'POST') {
        const token = request.headers.get('X-Admin-Token') || '';
        if (!env.ADMIN_TOKEN || token !== env.ADMIN_TOKEN) return bad('unauthorized', 401);

        const body = await request.json().catch(() => null);
        if (!body || !body.cp) return bad('cp is required');
        const card = await env.DB.prepare('SELECT * FROM cards WHERE cp = ?').bind(body.cp).first();
        if (!card) return bad('unknown cp', 404);

        const sets = [];
        const args = [];
        const changed = {};

        if (body.memo !== undefined) {
          sets.push('memo = ?'); args.push(String(body.memo)); changed.memo = body.memo;
        }
        if (body.rr !== undefined) {
          const rr = String(body.rr).trim().toLowerCase();
          if (!/^[a-z]+$/.test(rr)) return bad('rr must be a single lowercase token, e.g. "kkwa"');
          sets.push('rr = ?'); args.push(rr); changed.rr = rr;
        }
        if (body.category !== undefined) {
          const cat = String(body.category).trim();
          if (!OPEN_CATEGORIES.includes(cat)) {
            return bad(`category must be one of ${OPEN_CATEGORIES.join('/')}`);
          }
          sets.push('category = ?'); args.push(cat); changed.category = cat;
        }
        if (body.keys !== undefined) {
          const keys = String(body.keys).trim();
          const composed = compose(keys);
          if (composed !== card.hangul) {
            return bad(`keys "${keys}" would type ${composed || 'nothing'}, not ${card.hangul}`);
          }
          sets.push('keys = ?'); args.push(keys); changed.keys = keys;
        }
        let weight;
        if (body.weight !== undefined) {
          const w = Number(body.weight);
          if (!Number.isInteger(w) || w < 1 || w > 15) return bad('weight must be an integer 1–15');
          weight = await setWeight(env, body.owner || DEFAULT_OWNER, card.cp, w);
          changed.weight = weight;
        }
        if (sets.length) {
          args.push(card.cp);
          await env.DB.prepare(`UPDATE cards SET ${sets.join(', ')} WHERE cp = ?`).bind(...args).run();
          await env.DB.prepare(
            `INSERT INTO reviews (ts, owner, cp, action, result, note, mode)
             VALUES (?, ?, ?, 'edit', '', ?, '')`,
          ).bind(nowTaipei(), body.owner || DEFAULT_OWNER, card.cp, JSON.stringify(changed)).run();
        }
        const updated = await env.DB.prepare(`SELECT ${CARD_COLS} FROM cards c WHERE c.cp = ?`)
          .bind(card.cp).first();
        return json({ ok: true, changed, card: updated, weight });
      }

      return bad('not found', 404);
    } catch (err) {
      return json({ error: String(err && err.message ? err.message : err) }, 500);
    }
  },
};
