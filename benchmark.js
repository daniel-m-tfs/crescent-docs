// Benchmark page: renders window.CRESCENT_BENCH (benchmark-data.js, generated
// by benchmark/bench/export_site.py) as tiles, small-multiple bar charts,
// a memory chart and a full table. No libraries.
(function () {
    'use strict';

    var DATA = window.CRESCENT_BENCH;

    // Fixed entity order = fixed colour slot (validated palette, see benchmark.css).
    var APPS = [
        { id: 'crescent-2', name: 'Crescent 2', stack: 'OpenResty', slot: 1 },
        { id: 'node-fastify', name: 'Node + Fastify', stack: 'Node.js', slot: 2 },
        { id: 'python-fastapi', name: 'Python + FastAPI', stack: 'uvicorn', slot: 3 },
        { id: 'crescent-1x', name: 'Crescent 1.x', stack: 'Luvit', slot: 4 }
    ];
    var APP = {};
    APPS.forEach(function (a) { APP[a.id] = a; });

    var SCENARIOS = [
        { id: 'plain', title: 'Texto', req: 'GET /plain', what: 'O mínimo: HTTP + roteamento + resposta de texto.' },
        { id: 'json', title: 'JSON', req: 'GET /json', what: 'Serializa um objeto pequeno.' },
        { id: 'params', title: 'Rota com parâmetro', req: 'GET /params/42?q=lua', what: 'Parâmetro de rota e query string.' },
        { id: 'echo', title: 'Corpo JSON', req: 'POST /echo', what: 'Lê, faz parse e devolve um JSON.' },
        { id: 'db-one', title: 'Banco: 1 linha', req: 'GET /db/{id}', what: 'SELECT por chave primária, id aleatório.' },
        { id: 'db-list', title: 'Banco: 20 linhas', req: 'GET /db', what: 'SELECT de 20 linhas e um JSON maior.' },
        { id: 'db-insert', title: 'Banco: INSERT', req: 'POST /db', what: 'Um INSERT com commit por requisição.' },
        { id: 'orm-one', title: 'ORM: 1 linha', req: 'GET /orm/{id}', what: 'O mesmo SELECT via Model:find — só Crescent.' }
    ];
    var SCEN = {};
    SCENARIOS.forEach(function (s) { SCEN[s.id] = s; });

    var state = { workers: 1, metric: 'rps' };
    var nf0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
    var nf1 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
    var nf2 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 });

    function $(id) { return document.getElementById(id); }
    function el(tag, cls, text) {
        var e = document.createElement(tag);
        if (cls) e.className = cls;
        if (text != null) e.textContent = text;
        return e;
    }
    function ms(v) { return v == null ? '—' : (v < 10 ? nf2 : nf1).format(v) + ' ms'; }

    if (!DATA || !DATA.results) {
        $('bench-meta').textContent = 'Os dados do benchmark não foram carregados.';
        return;
    }

    var byKey = {};
    DATA.results.forEach(function (r) { byKey[r.app + '|' + r.workers + '|' + r.scenario] = r; });
    function get(app, workers, scenario) { return byKey[app + '|' + workers + '|' + scenario]; }
    var workerSets = {};
    DATA.results.forEach(function (r) { workerSets[r.workers] = true; });

    // ---- meta line -----------------------------------------------------------
    (function meta() {
        var env = DATA.environment || {};
        var date = env.date ? new Date(env.date) : null;
        var when = date ? date.toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', year: 'numeric' }) : '';
        var parts = [];
        if (when) parts.push('Rodada de ' + when);
        if (env.machine) parts.push(env.machine + ' · ' + env.cpus + ' núcleos · ' + env.mem_gb + ' GB');
        if (env.mysql) parts.push('MySQL ' + env.mysql);
        if (env.wrk) parts.push('wrk ' + env.wrk + (env.warmup ? ' (+' + env.warmup + ' de aquecimento)' : ''));
        if (+env.rounds > 1) parts.push('mediana de ' + env.rounds + ' rodadas, ordem dos apps alternada');
        else parts.push('rodada única: entre execuções, o mesmo app variou até ~25% nesta máquina');
        $('bench-meta').textContent = parts.join(' — ');
        if (env.wrk) $('m-wrk').textContent = 'wrk ' + env.wrk;
    })();

    // ---- headline tiles ------------------------------------------------------
    function ratio(a, b, workers, scenarios) {
        // Geometric mean of per-scenario req/s ratios (a / b).
        var logs = 0, n = 0;
        scenarios.forEach(function (s) {
            var ra = get(a, workers, s), rb = get(b, workers, s);
            if (ra && rb && ra.rps && rb.rps) { logs += Math.log(ra.rps / rb.rps); n++; }
        });
        return n ? Math.exp(logs / n) : null;
    }
    function xfmt(r) { return '×' + nf1.format(r); }

    (function tiles() {
        var box = $('bench-tiles');
        var common = ['plain', 'json', 'params', 'echo', 'db-one', 'db-list', 'db-insert'];
        var tiles = [];
        var v1 = ratio('crescent-2', 'crescent-1x', 1, common);
        if (v1) tiles.push({ value: xfmt(v1), label: 'vs. Crescent 1.x', sub: 'requisições/s, média geométrica dos 7 cenários, 1 worker' });
        var vdb = ratio('crescent-2', 'node-fastify', 1, ['db-one', 'db-list', 'db-insert']);
        if (vdb) tiles.push({
            value: xfmt(vdb),
            label: 'vs. Node + Fastify com banco' + (vdb < 1 ? ' (Node à frente)' : ''),
            sub: 'requisições/s, média dos 3 cenários de banco, 1 worker'
        });
        var vpy = ratio('crescent-2', 'python-fastapi', 1, common);
        if (vpy) tiles.push({ value: xfmt(vpy), label: 'vs. Python + FastAPI', sub: 'requisições/s, média geométrica dos 7 cenários, 1 worker' });
        var total = 0, bad = 0;
        DATA.results.forEach(function (r) {
            if (r.scenario === 'idle') return;
            total += r.requests || 0;
            bad += (r.errors || 0) + (r.non2xx || 0);
        });
        tiles.push({
            value: bad ? nf0.format(bad) : '0',
            label: bad ? 'respostas com erro em toda a rodada' : 'erros em toda a rodada',
            sub: nf0.format(total) + ' requisições medidas, todas as aplicações'
        });
        tiles.forEach(function (t) {
            var d = el('div', 'bench-tile');
            d.appendChild(el('p', 'bench-tile-value', t.value));
            d.appendChild(el('p', 'bench-tile-label', t.label));
            d.appendChild(el('p', 'bench-tile-sub', t.sub));
            box.appendChild(d);
        });
    })();

    // ---- legend --------------------------------------------------------------
    (function legend() {
        var ul = $('bench-legend');
        APPS.forEach(function (a) {
            var li = el('li', 'legend-item');
            li.appendChild(el('span', 'swatch s' + a.slot));
            li.appendChild(el('span', null, a.name));
            li.appendChild(el('span', 'legend-stack', a.stack));
            ul.appendChild(li);
        });
    })();

    // ---- tooltip ---------------------------------------------------------------
    var tip = $('bench-tip');
    var tipTarget = null;
    function showTip(target, r, appId, scenario) {
        var a = APP[appId];
        tip.innerHTML = '';
        var h = el('p', 'tip-title');
        h.appendChild(el('span', 'swatch s' + a.slot));
        h.appendChild(document.createTextNode(a.name));
        tip.appendChild(h);
        tip.appendChild(el('p', 'tip-sub', SCEN[scenario].title + ' · ' + r.workers + (r.workers > 1 ? ' workers' : ' worker')));
        var dl = el('dl', 'tip-list');
        var rows = [['Requisições/s (mediana)', nf0.format(r.rps)]];
        if (r.rounds > 1 && r.rps_min != null) rows.push(['Faixa (' + r.rounds + ' rodadas)', nf0.format(r.rps_min) + '–' + nf0.format(r.rps_max)]);
        rows.concat([ ['Latência média', ms(r.avg)], ['p50', ms(r.p50)], ['p90', ms(r.p90)],
            ['p99', ms(r.p99)], ['Requisições', nf0.format(r.requests)],
            ['Erros', nf0.format((r.errors || 0) + (r.non2xx || 0))], ['Memória (pico)', r.rss != null ? r.rss + ' MB' : '—']])
            .forEach(function (p) {
                dl.appendChild(el('dt', null, p[0]));
                dl.appendChild(el('dd', null, p[1]));
            });
        tip.appendChild(dl);
        tip.hidden = false;
        tipTarget = target;
        placeTip();
    }
    function placeTip() {
        if (!tipTarget || tip.hidden) return;
        var b = tipTarget.getBoundingClientRect();
        var tw = tip.offsetWidth, th = tip.offsetHeight;
        var x = Math.min(Math.max(8, b.left + b.width / 2 - tw / 2), window.innerWidth - tw - 8);
        var y = b.top - th - 10;
        if (y < 8) y = b.bottom + 10;
        tip.style.left = x + 'px';
        tip.style.top = y + 'px';
    }
    function hideTip() { tip.hidden = true; tipTarget = null; }
    // Keyboard focus scrolls the row into view: follow it instead of closing.
    window.addEventListener('scroll', placeTip, { passive: true });
    window.addEventListener('resize', placeTip);
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hideTip(); });

    // ---- charts ----------------------------------------------------------------
    function render() {
        var grid = $('bench-grid');
        grid.innerHTML = '';
        hideTip();
        var metric = state.metric, w = state.workers;
        $('bench-hint').textContent = metric === 'rps'
            ? 'Requisições por segundo — maior é melhor.'
            : 'Latência p99 (99% das requisições responderam em até este tempo) — menor é melhor.';

        SCENARIOS.forEach(function (s) {
            var apps = s.id === 'orm-one' ? APPS.filter(function (a) { return a.id.indexOf('crescent') === 0; }) : APPS;
            var values = apps.map(function (a) { return get(a.id, w, s.id); });
            if (!values.some(function (r) { return r && r[metric] != null; })) return;
            var max = 0;
            values.forEach(function (r) { if (r && r[metric] > max) max = r[metric]; });

            var card = el('figure', 'bench-card');
            var cap = el('figcaption', 'bench-card-head');
            cap.appendChild(el('h3', 'bench-card-title', s.title));
            cap.appendChild(el('code', 'bench-card-req', s.req));
            cap.appendChild(el('p', 'bench-card-what', s.what));
            card.appendChild(cap);

            var list = el('ul', 'bars');
            apps.forEach(function (a, i) {
                var r = values[i];
                var li = el('li', 'bar-row');
                li.appendChild(el('span', 'bar-name' + (a.id === 'crescent-2' ? ' is-focus' : ''), a.name));
                var track = el('span', 'bar-track');
                var val;
                if (r && r[metric] != null) {
                    var fill = el('span', 'bar-fill s' + a.slot);
                    fill.style.width = Math.max(0.6, (r[metric] / max) * 100) + '%';
                    track.appendChild(fill);
                    val = metric === 'rps' ? nf0.format(r.rps) : ms(r.p99);
                    var bad = (r.errors || 0) + (r.non2xx || 0);
                    li.tabIndex = 0;
                    li.setAttribute('aria-label', a.name + ': ' + val + (metric === 'rps' ? ' requisições por segundo' : ' de latência p99') + (bad ? ', com erros' : ''));
                    (function (row) {
                        li.addEventListener('mouseenter', function () { showTip(li, row, a.id, s.id); });
                        li.addEventListener('focus', function () { showTip(li, row, a.id, s.id); });
                        li.addEventListener('mouseleave', hideTip);
                        li.addEventListener('blur', hideTip);
                    })(r);
                    if (bad) val += ' ⚠';
                } else {
                    li.classList.add('is-missing');
                    val = a.id === 'crescent-1x' && w > 1 ? 'processo único' : 'sem dado';
                }
                li.appendChild(track);
                li.appendChild(el('span', 'bar-value', val));
                list.appendChild(li);
            });
            card.appendChild(list);
            grid.appendChild(card);
        });

        renderMemory();
    }

    function renderMemory() {
        var box = $('bench-memory');
        box.innerHTML = '';
        var w = state.workers, rows = [], max = 0;
        APPS.forEach(function (a) {
            var idle = get(a.id, w, 'idle');
            var peak = 0;
            DATA.results.forEach(function (r) {
                if (r.app === a.id && r.workers === w && r.rss != null && r.rss > peak) peak = r.rss;
            });
            rows.push({ app: a, idle: idle ? idle.rss : null, peak: peak || null });
            if (peak > max) max = peak;
        });
        var list = el('ul', 'bars bars-memory');
        rows.forEach(function (m) {
            var li = el('li', 'bar-row');
            li.appendChild(el('span', 'bar-name' + (m.app.id === 'crescent-2' ? ' is-focus' : ''), m.app.name));
            var track = el('span', 'bar-track');
            var val;
            if (m.peak) {
                var fill = el('span', 'bar-fill s' + m.app.slot);
                fill.style.width = Math.max(0.6, (m.peak / max) * 100) + '%';
                track.appendChild(fill);
                if (m.idle != null) {
                    var tick = el('span', 'bar-tick');
                    tick.style.left = (m.idle / max) * 100 + '%';
                    tick.title = 'ociosa: ' + m.idle + ' MB';
                    track.appendChild(tick);
                }
                val = (m.idle != null ? m.idle + ' → ' : '') + m.peak + ' MB';
            } else {
                li.classList.add('is-missing');
                val = m.app.id === 'crescent-1x' && w > 1 ? 'processo único' : 'sem dado';
            }
            li.appendChild(track);
            li.appendChild(el('span', 'bar-value', val));
            list.appendChild(li);
        });
        box.appendChild(list);
        var key = el('p', 'bench-note', 'A marca fina indica a memória ociosa; a barra vai até o pico.');
        box.appendChild(key);
    }

    function renderTable() {
        var t = el('table', 'bench-table');
        var head = el('thead');
        var tr = el('tr');
        ['Aplicação', 'Workers', 'Cenário', 'Req/s (mediana)', 'Mín–máx', 'Média', 'p50', 'p90', 'p99', 'Erros', 'RSS (MB)'].forEach(function (h, i) {
            var th = el('th', i > 2 ? 'num' : null, h);
            th.scope = 'col';
            tr.appendChild(th);
        });
        head.appendChild(tr);
        t.appendChild(head);
        var body = el('tbody');
        var ws = Object.keys(workerSets).map(Number).sort();
        ws.forEach(function (w) {
            APPS.forEach(function (a) {
                SCENARIOS.forEach(function (s) {
                    var r = get(a.id, w, s.id);
                    if (!r) return;
                    var row = el('tr');
                    [a.name, String(w), s.title, nf0.format(r.rps),
                        r.rps_min != null ? nf0.format(r.rps_min) + '–' + nf0.format(r.rps_max) : '—', ms(r.avg), ms(r.p50), ms(r.p90), ms(r.p99),
                        nf0.format((r.errors || 0) + (r.non2xx || 0)), r.rss != null ? String(r.rss) : '—']
                        .forEach(function (v, i) { row.appendChild(el(i === 0 ? 'th' : 'td', i > 2 ? 'num' : null, v)); });
                    body.appendChild(row);
                });
            });
        });
        t.appendChild(body);
        $('bench-table').appendChild(t);
    }

    // ---- controls --------------------------------------------------------------
    function bindSeg(id, key, parse) {
        var group = $(id);
        var buttons = group.querySelectorAll('button');
        Array.prototype.forEach.call(buttons, function (b) {
            if (key === 'workers' && !workerSets[parse(b.dataset.value)]) {
                b.disabled = true;
                b.title = 'Ainda não medido';
            }
            b.addEventListener('click', function () {
                state[key] = parse(b.dataset.value);
                Array.prototype.forEach.call(buttons, function (o) { o.setAttribute('aria-checked', String(o === b)); });
                render();
            });
        });
    }
    bindSeg('ctl-workers', 'workers', Number);
    bindSeg('ctl-metric', 'metric', String);

    render();
    renderTable();
})();
