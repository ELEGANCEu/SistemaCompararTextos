
const $ = id => document.getElementById(id);

const pct = v => (v * 100).toFixed(1) + "%";

const esc = s => String(s).replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
}[c]));

const colorFor = v =>
    v >= 0.6 ? "#16a34a" :
        v >= 0.35 ? "#d97706" :
            v >= 0.15 ? "#f59e0b" : "#9ca3af";

function options() {
    return {
        StopWords: $("optStop").checked,
        Radicaliar: $("optStem").checked,
        Acentos: $("optAcc").checked
    };
}

function showError(msg) {
    const e = $("error");
    e.textContent = msg;
    e.classList.toggle("hidden", !msg);
}

async function api(path, body) {
    showError("");

    try {
        const r = await fetch(path, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        const data = await r.json();

        if (!r.ok) {
            throw new Error(data.error || "Erro no servidor");
        }

        return data;
    } catch (e) {
        showError(e.message || "Não foi possível conectar ao servidor.");
        return null;
    }
}

/* ---------- Abas ---------- */

document.querySelectorAll(".tab").forEach(t => {
    t.onclick = () => {
        document.querySelectorAll(".tab").forEach(x =>
            x.classList.toggle("active", x === t)
        );

        $("tab-pair").classList.toggle("hidden", t.dataset.tab !== "pair");
        $("tab-many").classList.toggle("hidden", t.dataset.tab !== "many");

        showError("");
    };
});

/* ---------- Comparação de 2 textos ---------- */

$("btnPair").onclick = async () => {
    const btn = $("btnPair");
    btn.disabled = true;

    try {
        const r = await api("/api/compare", {
            text_a: $("textA").value,
            text_b: $("textB").value,
            options: options()
        });

        if (!r) return;

        const c = r.SimilaridadeCombinada;
        const col = colorFor(c);

        $("resultPair").classList.remove("hidden");

        $("gauge").style.background =
            `conic-gradient(${col} ${c * 360}deg, #eceef5 0)`;

        $("scoreNum").textContent = pct(c);
        $("verdict").textContent = r.Classificacao;
        $("verdict").style.color = col;

        const metric = (name, v, hint) => `
            <div class="metric">
                <div class="top">
                    <span>${name}
                        <small style="color:var(--muted)">${hint}</small>
                    </span>
                    <b>${pct(v)}</b>
                </div>
                <div class="bar">
                    <span style="width:${v * 100}%"></span>
                </div>
            </div>
        `;

        $("metrics").innerHTML =
            metric("Cosseno (TF-IDF)", r.Cosseno, "— peso das palavras") +
            metric("Jaccard", r.Jaccard, "— vocabulário compartilhado") +
            metric("Bigramas", r.SobreposicaoNgram, "— ordem das palavras");

        const termos = r.TermosComuns || [];

        $("terms").innerHTML = termos.length
            ? termos.map(t =>
                `<span class="chip">${esc(t)}</span>`
            ).join("")
            : `<span style="color:var(--muted)">Nenhum termo em comum.</span>`;

        const trechos = r.TrechosComuns || [];

        $("passages").innerHTML = trechos.length
            ? trechos.map(p =>
                `<div class="passage">${esc(p.text)}
                    <small>(${p.words} palavras)</small>
                </div>`
            ).join("")
            : `<span style="color:var(--muted)">Nenhum trecho literal com 4+ palavras em comum.</span>`;

        const s = r.Estatisticas;

        $("stats").innerHTML = `
            Texto A: <b>${s.TokensA}</b> termos (${s.UniqueA} únicos)
            · Texto B: <b>${s.TokensB}</b> termos (${s.UniqueB} únicos)
            · Em comum: <b>${s.TermosUnicos}</b> termos únicos
        `;
    } catch (e) {
        showError(e.message || "Erro ao exibir a comparação.");
    } finally {
        btn.disabled = false;
    }
};

/* ---------- Limpar e preencher exemplos ---------- */

$("btnClear").onclick = () => {
    $("textA").value = "";
    $("textB").value = "";
    $("resultPair").classList.add("hidden");
    showError("");
};

$("btnExample").onclick = () => {
    $("textA").value =
        "A inteligência artificial está transformando a medicina. Algoritmos de aprendizado de máquina ajudam médicos a diagnosticar doenças com mais rapidez e precisão, analisando exames de imagem e históricos de pacientes.";

    $("textB").value =
        "Na área da saúde, a inteligência artificial vem mudando o diagnóstico. Modelos de aprendizado de máquina auxiliam médicos a identificar doenças mais rápido, analisando exames de imagem e dados dos pacientes.";
};

/* ---------- Comparação de vários textos ---------- */

function addDoc(value = "") {
    const wrap = document.createElement("div");
    wrap.className = "doc";

    wrap.innerHTML = `
        <textarea placeholder="Cole um texto…"></textarea>
        <button class="ghost" title="Remover">✕</button>
    `;

    wrap.querySelector("textarea").value = value;

    wrap.querySelector("button").onclick = () => {
        if ($("docs").children.length > 2) {
            wrap.remove();
            renumber();
        }
    };

    $("docs").appendChild(wrap);
    renumber();
}

function renumber() {
    [...$("docs").children].forEach((d, i) => {
        d.querySelector("textarea").placeholder = `Texto ${i + 1}…`;
    });
}

$("btnAddDoc").onclick = () => addDoc();

addDoc();
addDoc();
addDoc();

$("btnMany").onclick = async () => {
    const todosTextos = [...$("docs").querySelectorAll("textarea")]
        .map(t => t.value);

    const idx = todosTextos
        .map((t, i) => t.trim() ? i : -1)
        .filter(i => i >= 0);

    if (idx.length < 2) {
        showError("Informe pelo menos dois textos para comparar.");
        return;
    }

    const btn = $("btnMany");
    btn.disabled = true;

    try {
        const r = await api("/api/compare-many", {
            texts: todosTextos,
            options: options()
        });

        if (!r) return;

        const name = k => `Texto ${idx[k] + 1}`;

        let html =
            "<table class='matrix'><tr><th></th>" +
            idx.map((_, k) => `<th>${name(k)}</th>`).join("") +
            "</tr>";

        r.Matriz.forEach((row, i) => {
            html += `<tr><th>${name(i)}</th>`;

            html += row.map((v, j) => {
                const bg = i === j
                    ? "#f3f4f6"
                    : `color-mix(in srgb, ${colorFor(v)} ${Math.round(v * 70 + 10)}%, white)`;

                return `<td style="background:${bg}">${i === j ? "—" : pct(v)}</td>`;
            }).join("");

            html += "</tr>";
        });

        $("matrix").innerHTML = html + "</table>";

        // A chave Classificacao contém a lista de pares no retorno do Python.
        const pares = r.Classificacao || [];

        $("ranking").innerHTML = pares.map(p =>
            `<div class="rank-item">
                <span>
                    ${name(p.a)} ↔ ${name(p.b)}
                    <small style="color:var(--muted)">· ${esc(p.Classificacao)}</small>
                </span>
                <b style="color:${colorFor(p.Score)}">${pct(p.Score)}</b>
            </div>`
        ).join("");

        $("resultMany").classList.remove("hidden");
    } catch (e) {
        showError(e.message || "Erro ao exibir a comparação.");
    } finally {
        btn.disabled = false;
    }
};
