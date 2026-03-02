from __future__ import annotations

import html
from pathlib import Path
import re


def render_homepage() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Quantum Error Correction</title>
    <style>
      @import url("https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@200..900&family=JetBrains+Mono:wght@100..800&display=swap");

      :root {
        --bg: #f8f7f4;
        --panel: #ffffff;
        --text: #1f1f1f;
        --muted: #6a6a6a;
        --border: #dedad4;
        --accent: #8f4b17;
        --accent-dark: #763a0d;
        --green: #1f9b4f;
      }

      * {
        box-sizing: border-box;
      }

      html {
        scroll-behavior: smooth;
      }

      body {
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font-family: "Crimson Pro", Georgia, serif;
        font-size: 18px;
        line-height: 1.6;
      }

      a {
        color: var(--accent);
        text-decoration: none;
      }

      .container {
        width: 100%;
        max-width: 1080px;
        margin: 0 auto;
        padding: 0 1rem;
      }

      @media (min-width: 640px) {
        .container {
          padding: 0 2rem;
        }
      }

      .site-header {
        height: 72px;
        border-bottom: 1px solid var(--border);
        background: #fff;
      }

      .header-row {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
      }

      .header-left {
        display: flex;
        align-items: center;
        gap: 26px;
        min-width: 0;
      }

      .brand {
        color: var(--text);
        font-size: 1.125rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        white-space: nowrap;
      }

      .nav {
        display: none;
      }

      @media (min-width: 760px) {
        .nav {
          display: flex;
          gap: 4px;
          align-items: center;
        }
      }

      .nav-item {
        position: relative;
        color: #444;
        font-size: 0.875rem;
        font-weight: 500;
        padding: 8px 20px 8px 10px;
      }

      .nav-item::after {
        content: "";
        position: absolute;
        right: 7px;
        top: 50%;
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid currentColor;
        transform: translateY(-20%);
        opacity: 0.75;
      }

      .auth-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: var(--accent);
        color: #fff;
        border: 1px solid var(--accent);
        border-radius: 6px;
        font-size: 0.95rem;
        font-weight: 600;
        padding: 10px 16px;
      }

      .auth-btn:hover {
        background: var(--accent-dark);
        border-color: var(--accent-dark);
        color: #fff;
      }

      main {
        padding: 56px 0 72px;
      }

      .hero {
        display: grid;
        grid-template-columns: 1fr;
        gap: 28px;
        align-items: start;
      }

      @media (min-width: 980px) {
        .hero {
          grid-template-columns: minmax(0, 1fr) 460px;
          gap: 48px;
        }
      }

      .hero-copy h1 {
        margin: 0 0 16px;
        font-size: 2.25rem;
        line-height: calc(2.5 / 2.25);
        font-weight: 700;
      }

      .hero-copy p {
        margin: 0 0 12px;
        color: var(--muted);
        font-size: 1.125rem;
        line-height: calc(1.75 / 1.125);
      }

      .hero-actions {
        margin-top: 24px;
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
      }

      .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        cursor: pointer;
        border: 1px solid transparent;
        font-family: inherit;
        font-size: 1rem;
        font-weight: 500;
        padding: 0.625rem 1.25rem;
      }

      .btn-primary {
        background: var(--accent);
        border-color: var(--accent);
        color: #fff;
      }

      .btn-primary:hover {
        background: var(--accent-dark);
        border-color: var(--accent-dark);
      }

      .btn-secondary {
        background: #fff;
        border-color: var(--border);
        color: var(--text);
      }

      .btn-secondary:hover {
        border-color: #cfc8be;
      }

      .hero-graphic {
        width: min(100%, 460px);
        aspect-ratio: 520 / 430;
        margin-inline: auto;
      }

      .lattice-grid-line {
        stroke: #d8c5af;
        stroke-width: 1;
        opacity: 0.58;
      }

      .lattice-node {
        fill: #ebd8c4;
        stroke: #c89f76;
        stroke-width: 1.15;
        transition: fill 260ms ease, stroke 260ms ease, r 260ms ease;
      }

      .lattice-node.failed {
        fill: #d25f4a;
        stroke: #8f2f22;
      }

      .lattice-label {
        font-family: "JetBrains Mono", monospace;
        fill: #8f6d51;
        font-size: 11px;
      }

      .lattice-arrow {
        stroke: #9d6f44;
        stroke-width: 1.8;
        fill: none;
        transition: stroke 260ms ease;
      }

      .lattice-bracket {
        stroke: #9d6f44;
        stroke-width: 1.6;
        fill: none;
      }

      .logical-qubit-ring {
        fill: none;
        stroke: #cfab86;
        stroke-width: 1.4;
        transition: stroke 260ms ease;
      }

      .logical-qubit-core {
        fill: #fffaf4;
        stroke: #9d6f44;
        stroke-width: 2;
        transition: fill 260ms ease, stroke 260ms ease;
      }

      .section {
        margin-top: 70px;
      }

      .section h2 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 2.6rem);
        line-height: 1.15;
      }

      .section-subrow {
        margin-top: 8px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
      }

      .muted {
        margin: 0;
        color: var(--muted);
      }

      .show-buttons {
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }

      .show-buttons span {
        color: var(--muted);
        font-size: 1.05rem;
      }

      .show-btn {
        border: 1px solid var(--border);
        border-radius: 5px;
        background: #fff;
        color: #5d5d5d;
        cursor: pointer;
        font-family: "JetBrains Mono", monospace;
        font-size: 0.9rem;
        padding: 3px 10px;
      }

      .show-btn.active {
        color: #fff;
        background: var(--accent);
        border-color: var(--accent);
      }

      .table-card {
        margin-top: 16px;
        border: 1px solid var(--border);
        border-radius: 10px;
        background: #faf9f7;
        overflow: auto;
      }

      table {
        width: 100%;
        border-collapse: collapse;
        min-width: 760px;
      }

      th,
      td {
        text-align: left;
        padding: 16px 18px;
        border-bottom: 1px solid #e6e0d8;
        font-size: 1.15rem;
      }

      th {
        color: #66615c;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.95rem;
      }

      tr:last-child td {
        border-bottom: none;
      }

      .mono {
        font-family: "JetBrains Mono", monospace;
      }

      .rank-cell {
        font-weight: 700;
      }

      .rank-gold {
        color: #c67a00;
      }

      .rank-silver {
        color: #6b7380;
      }

      .rank-bronze {
        color: #b14f00;
      }

      .text-right {
        text-align: right;
      }

      .text-success {
        color: var(--green);
      }

      .track-pill {
        display: inline-flex;
        padding: 2px 8px;
        border: 1px solid #d8d0c7;
        border-radius: 999px;
        color: #5f5f5f;
        font-family: "JetBrains Mono", monospace;
        font-size: 0.78rem;
      }

      .msg {
        margin-top: 10px;
        color: var(--muted);
      }

      .submit-card {
        margin-top: 14px;
        border: 1px solid var(--border);
        border-radius: 10px;
        background: #fff;
        padding: 20px;
      }

      .form-grid {
        display: grid;
        gap: 12px;
      }

      @media (min-width: 860px) {
        .form-grid {
          grid-template-columns: 1fr auto auto;
          align-items: center;
        }
      }

      input[type="text"],
      input[type="file"],
      select {
        width: 100%;
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 11px 14px;
        font-family: inherit;
        font-size: 1rem;
        background: #fff;
      }

      input[type="text"]:focus,
      input[type="file"]:focus,
      select:focus {
        outline: none;
        border-color: var(--accent);
      }

      .inline-row {
        margin: 18px 0 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }

      .inline-row h3 {
        margin: 0;
        font-size: 1.4rem;
      }

      .footer {
        border-top: 1px solid var(--border);
        background: #fcfbf8;
      }

      .footer-inner {
        padding: 20px 0 28px;
      }

      .footer-links {
        display: flex;
        gap: 22px;
        flex-wrap: wrap;
      }

      .modal-open {
        overflow: hidden;
      }

      .submit-modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(22, 16, 10, 0.42);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 60;
        padding: 18px;
      }

      .submit-modal-overlay.open {
        display: flex;
      }

      .submit-modal {
        width: min(980px, 100%);
        max-height: calc(100vh - 40px);
        overflow: auto;
        border-radius: 12px;
        border: 1px solid var(--border);
        background: var(--bg);
        padding: 18px;
      }

      .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 10px;
      }

      .modal-header h3 {
        margin: 0;
        font-size: 1.8rem;
      }

      .modal-close {
        border: 1px solid var(--border);
        background: #fff;
        color: #584d43;
        border-radius: 6px;
        padding: 6px 10px;
        cursor: pointer;
        font-size: 1rem;
      }
    </style>
  </head>
  <body>
    <header class="site-header">
      <div class="container header-row">
        <div class="header-left">
          <a class="brand" href="/">Optimization Arena</a>
          <nav class="nav">
            <a class="nav-item" href="#">Trading</a>
            <a class="nav-item" href="#">Gaming</a>
            <a class="nav-item" href="#">Language</a>
          </nav>
        </div>
        <a class="auth-btn" href="#"><span style="font-family: 'JetBrains Mono', monospace;">X</span>Sign in with X</a>
      </div>
    </header>

    <main>
      <div class="container">
        <section class="hero">
          <div class="hero-copy">
            <h1>Quantum Error Correction</h1>
            <p>
              Quantum error correction keeps quantum computers reliable by using many noisy physical qubits to represent a single logical one. A classical decoding algorithm runs alongside the hardware, detecting and fixing failures in real time. The best known decoder for this problem is Minimum Weight Perfect Matching (MWPM), but it assumes qubit failures are independent. In practice, real hardware produces correlated errors due to cosmic rays, gate crosstalk, and leakage. In those cases, MWPM breaks down. In this challenge, you will try to replace it with something better.
            </p>
            <div class="hero-actions">
              <a class="btn btn-secondary" href="/about">Read More</a>
              <button class="btn btn-primary" type="button" data-open-submit>Submit Your Strategy</button>
            </div>
          </div>
          <div class="hero-graphic" aria-hidden="true">
            <svg id="lattice-svg" viewBox="0 0 520 430" width="100%" height="100%">
              <defs>
                <marker id="lattice-arrowhead" markerWidth="8" markerHeight="8" refX="6.2" refY="4" orient="auto">
                  <path id="lattice-arrowhead-path" d="M 0 0 L 8 4 L 0 8 z" fill="#9d6f44"></path>
                </marker>
              </defs>
              <g id="lattice-grid"></g>
              <g id="lattice-nodes"></g>
              <line id="logical-arrow" x1="292" y1="182" x2="406" y2="182" class="lattice-arrow" marker-end="url(#lattice-arrowhead)"></line>
              <text x="349" y="166" class="lattice-label" text-anchor="middle">Error Correction</text>
              <circle id="logical-qubit-ring" cx="438" cy="182" r="14" class="logical-qubit-ring"></circle>
              <circle id="logical-qubit-core" cx="438" cy="182" r="9" class="logical-qubit-core"></circle>
              <path d="M 42 320 v 12 h 228 v -12" class="lattice-bracket"></path>
              <text x="156" y="350" class="lattice-label" text-anchor="middle">Physical Qubits</text>
              <path d="M 420 218 v 10 h 36 v -10" class="lattice-bracket"></path>
              <text x="438" y="247" class="lattice-label" text-anchor="middle">Logical Qubit</text>
            </svg>
          </div>
        </section>

        <section id="leaderboard" class="section">
          <h2>Leaderboard</h2>
          <div class="section-subrow">
            <p class="muted">Strategies ranked by logical failure rate on fixed L=10, p=0.03, xi=10</p>
            <div class="show-buttons">
              <span>Show</span>
              <button class="show-btn active" data-limit="10">10</button>
              <button class="show-btn" data-limit="50">50</button>
              <button class="show-btn" data-limit="100">100</button>
            </div>
          </div>

          <div class="table-card">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Author</th>
                  <th>Strategy</th>
                  <th class="text-right">Avg Failure</th>
                  <th class="text-right">Throughput (info)</th>
                </tr>
              </thead>
              <tbody id="leaderboard-body"></tbody>
            </table>
          </div>
          <p id="leaderboard-msg" class="msg"></p>
        </section>
      </div>
    </main>

    <div id="submit-modal-overlay" class="submit-modal-overlay" aria-hidden="true">
      <div class="submit-modal" role="dialog" aria-modal="true" aria-labelledby="submit-modal-title">
        <div class="modal-header">
          <h3 id="submit-modal-title">Submit Strategy</h3>
          <button id="close-submit-modal" class="modal-close" type="button">Close</button>
        </div>
        <p class="muted">Upload a Python file implementing your decoder factory.</p>
        <div class="submit-card">
          <form id="submit-form" class="form-grid">
            <input id="name" type="text" value="my-decoder" placeholder="submission name" />
            <input id="file" type="file" accept=".py" />
            <button id="submit-btn" class="btn btn-primary" type="submit">Upload</button>
          </form>
          <p class="muted" style="margin-top: 10px;">Endpoint: <code>POST /submissions/python</code></p>
          <p id="submit-msg" class="msg"></p>
        </div>

        <div class="inline-row">
          <h3>Recent Submissions</h3>
          <select id="status-filter" style="max-width: 220px;">
            <option value="">all statuses</option>
            <option value="queued">queued</option>
            <option value="running">running</option>
            <option value="succeeded">succeeded</option>
            <option value="failed">failed</option>
          </select>
          <button id="refresh-submissions" class="btn btn-secondary" type="button">Refresh</button>
        </div>

        <div class="table-card">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Status</th>
                <th class="text-right">Failure</th>
                <th class="text-right">Throughput</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody id="submissions-body"></tbody>
          </table>
        </div>
        <p id="submissions-msg" class="msg"></p>
      </div>
    </div>

    <footer class="footer">
      <div class="container footer-inner">
        <nav class="footer-links">
          <a href="#leaderboard">Leaderboard</a>
          <a href="#" data-open-submit>Submit</a>
          <a href="https://github.com/MaxResnick/quantum_error_correction_challenge" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="/about">About</a>
          <a href="/health">API Health</a>
        </nav>
      </div>
    </footer>

    <script>
      const state = {
        leaderboardLimit: 10,
      };
      const submitModalOverlay = document.getElementById("submit-modal-overlay");
      const closeSubmitModalBtn = document.getElementById("close-submit-modal");

      function openSubmitModal() {
        submitModalOverlay.classList.add("open");
        submitModalOverlay.setAttribute("aria-hidden", "false");
        document.body.classList.add("modal-open");
        refreshSubmissions();
      }

      function closeSubmitModal() {
        submitModalOverlay.classList.remove("open");
        submitModalOverlay.setAttribute("aria-hidden", "true");
        document.body.classList.remove("modal-open");
      }

      function fmt(value, digits = 6) {
        if (value === null || value === undefined) return "-";
        if (typeof value !== "number") return String(value);
        return value.toFixed(digits);
      }

      function fmtFailure(value, digits = 3) {
        if (value === null || value === undefined) return "-";
        if (typeof value !== "number") return String(value);
        return value.toExponential(digits);
      }

      function rankClass(rank) {
        if (rank === 1) return "rank-gold";
        if (rank === 2) return "rank-silver";
        if (rank === 3) return "rank-bronze";
        return "";
      }

      function toLocalTime(value) {
        if (!value) return "-";
        const dt = new Date(value);
        if (Number.isNaN(dt.getTime())) return value;
        return dt.toLocaleString();
      }

      function initLatticeAnimation() {
        const gridLayer = document.getElementById("lattice-grid");
        const nodeLayer = document.getElementById("lattice-nodes");
        const logicalRing = document.getElementById("logical-qubit-ring");
        const logicalCore = document.getElementById("logical-qubit-core");
        const logicalArrow = document.getElementById("logical-arrow");
        const arrowHeadPath = document.getElementById("lattice-arrowhead-path");
        if (!gridLayer || !nodeLayer) return;

        const NS = "http://www.w3.org/2000/svg";
        const L = 13;
        const x0 = 42;
        const y0 = 44;
        const step = 19;
        const nodes = [];
        let logicalPhase = Math.random() * Math.PI * 2;

        function wrapHue(value) {
          const hue = value % 360;
          return hue < 0 ? hue + 360 : hue;
        }

        function phaseToHue(phase) {
          return wrapHue((phase * 180) / Math.PI);
        }

        function nodeColor(hue, failed) {
          if (failed) {
            return {
              fill: `hsl(${wrapHue(hue + 20)} 72% 58%)`,
              stroke: `hsl(${wrapHue(hue + 20)} 78% 34%)`,
            };
          }
          return {
            fill: `hsl(${hue} 56% 79%)`,
            stroke: `hsl(${hue} 62% 45%)`,
          };
        }

        for (let i = 0; i < L; i += 1) {
          const y = y0 + i * step;
          const hLine = document.createElementNS(NS, "line");
          hLine.setAttribute("x1", String(x0));
          hLine.setAttribute("y1", String(y));
          hLine.setAttribute("x2", String(x0 + (L - 1) * step));
          hLine.setAttribute("y2", String(y));
          hLine.setAttribute("class", "lattice-grid-line");
          gridLayer.appendChild(hLine);

          const x = x0 + i * step;
          const vLine = document.createElementNS(NS, "line");
          vLine.setAttribute("x1", String(x));
          vLine.setAttribute("y1", String(y0));
          vLine.setAttribute("x2", String(x));
          vLine.setAttribute("y2", String(y0 + (L - 1) * step));
          vLine.setAttribute("class", "lattice-grid-line");
          gridLayer.appendChild(vLine);
        }

        for (let row = 0; row < L; row += 1) {
          for (let col = 0; col < L; col += 1) {
            const node = document.createElementNS(NS, "circle");
            node.setAttribute("cx", String(x0 + col * step));
            node.setAttribute("cy", String(y0 + row * step));
            node.setAttribute("r", "4.4");
            node.setAttribute("class", "lattice-node");
            nodeLayer.appendChild(node);
            nodes.push({ row, col, node, phase: Math.random() * Math.PI * 2 });
          }
        }

        function sampleFrame() {
          const xi = 1.0 + Math.random() * 2.5;
          const seeds = 1 + Math.floor(Math.random() * 3);
          const centers = [];
          let sumX = 0;
          let sumY = 0;
          let failedCount = 0;

          for (let i = 0; i < seeds; i += 1) {
            centers.push({
              row: Math.floor(Math.random() * L),
              col: Math.floor(Math.random() * L),
              amp: 0.54 + Math.random() * 0.32,
            });
          }

          for (const point of nodes) {
            let pFail = 0.01;
            for (const center of centers) {
              const d = Math.abs(point.row - center.row) + Math.abs(point.col - center.col);
              pFail = 1 - (1 - pFail) * (1 - center.amp * Math.exp(-d / xi));
            }

            point.phase += 0.06 + Math.random() * 0.018;
            const hue = phaseToHue(point.phase);
            const failed = Math.random() < pFail;
            const colors = nodeColor(hue, failed);
            point.node.classList.toggle("failed", failed);
            point.node.style.fill = colors.fill;
            point.node.style.stroke = colors.stroke;
            point.node.setAttribute("r", failed ? "6.1" : "4.4");

            const weight = failed ? 1.35 : 1.0;
            sumX += Math.cos(point.phase) * weight;
            sumY += Math.sin(point.phase) * weight;
            if (failed) failedCount += 1;
          }

          const targetPhase = Math.atan2(sumY, sumX);
          let phaseDelta = targetPhase - logicalPhase;
          while (phaseDelta > Math.PI) phaseDelta -= 2 * Math.PI;
          while (phaseDelta < -Math.PI) phaseDelta += 2 * Math.PI;
          logicalPhase += phaseDelta * 0.35;

          const failRatio = failedCount / nodes.length;
          const logicalHue = phaseToHue(logicalPhase);
          if (logicalRing) {
            logicalRing.style.stroke = `hsl(${logicalHue} ${62 + failRatio * 16}% ${42 + failRatio * 10}%)`;
          }
          if (logicalCore) {
            logicalCore.style.fill = `hsl(${wrapHue(logicalHue + 28)} ${70 + failRatio * 18}% ${62 + failRatio * 8}%)`;
            logicalCore.style.stroke = `hsl(${logicalHue} ${80 + failRatio * 12}% ${28 + failRatio * 9}%)`;
            logicalCore.setAttribute("r", String(8.4 + failRatio * 2.2));
          }
          if (logicalArrow) {
            logicalArrow.style.stroke = `hsl(${logicalHue} 62% 40%)`;
          }
          if (arrowHeadPath) {
            arrowHeadPath.setAttribute("fill", `hsl(${logicalHue} 62% 40%)`);
          }
        }

        sampleFrame();
        setInterval(sampleFrame, 360);
      }

      async function refreshLeaderboard() {
        const msg = document.getElementById("leaderboard-msg");
        try {
          const res = await fetch("/leaderboard");
          if (!res.ok) throw new Error("leaderboard request failed");
          const data = await res.json();
          const entries = (data.entries || []).slice(0, state.leaderboardLimit);
          const tbody = document.getElementById("leaderboard-body");
          tbody.innerHTML = "";
          entries.forEach((entry, index) => {
            const rank = index + 1;
            const tr = document.createElement("tr");
            tr.innerHTML = `
              <td class="rank-cell ${rankClass(rank)}">#${rank}</td>
              <td>${entry.name}</td>
              <td><span class="track-pill">${entry.track}</span></td>
              <td class="text-right mono text-success">${fmtFailure(entry.mean_failure_rate, 3)}</td>
              <td class="text-right mono">${fmt(entry.mean_throughput_sps, 1)}</td>
            `;
            tbody.appendChild(tr);
          });
          msg.textContent = `${data.entries?.length || 0} total entries`;
        } catch (err) {
          msg.textContent = "Failed to load leaderboard";
        }
      }

      async function refreshSubmissions() {
        const status = document.getElementById("status-filter").value;
        const params = new URLSearchParams({ limit: "100", offset: "0" });
        if (status) params.set("status", status);

        const msg = document.getElementById("submissions-msg");
        try {
          const res = await fetch(`/submissions?${params.toString()}`);
          if (!res.ok) throw new Error("submissions request failed");
          const data = await res.json();
          const tbody = document.getElementById("submissions-body");
          tbody.innerHTML = "";
          (data.entries || []).forEach((entry) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
              <td class="mono">${entry.id}</td>
              <td>${entry.name}</td>
              <td>${entry.status}</td>
              <td class="text-right mono">${fmtFailure(entry.mean_failure_rate, 3)}</td>
              <td class="text-right mono">${fmt(entry.mean_throughput_sps, 1)}</td>
              <td>${toLocalTime(entry.created_at)}</td>
            `;
            tbody.appendChild(tr);
          });
          msg.textContent = `${data.total} total submissions`;
        } catch (err) {
          msg.textContent = "Failed to load submissions";
        }
      }

      document.getElementById("refresh-submissions").addEventListener("click", refreshSubmissions);
      document.getElementById("status-filter").addEventListener("change", refreshSubmissions);
      closeSubmitModalBtn.addEventListener("click", closeSubmitModal);

      submitModalOverlay.addEventListener("click", (event) => {
        if (event.target === submitModalOverlay) closeSubmitModal();
      });

      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && submitModalOverlay.classList.contains("open")) {
          closeSubmitModal();
        }
      });

      document.querySelectorAll("[data-open-submit]").forEach((element) => {
        element.addEventListener("click", (event) => {
          event.preventDefault();
          openSubmitModal();
        });
      });

      document.querySelectorAll(".show-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          state.leaderboardLimit = Number(btn.dataset.limit || "10");
          document.querySelectorAll(".show-btn").forEach((candidate) => {
            candidate.classList.toggle("active", candidate === btn);
          });
          refreshLeaderboard();
        });
      });

      document.getElementById("submit-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const submitBtn = document.getElementById("submit-btn");
        const submitMsg = document.getElementById("submit-msg");
        const fileInput = document.getElementById("file");
        const name = document.getElementById("name").value.trim() || "submission";

        if (!fileInput.files || fileInput.files.length === 0) {
          submitMsg.textContent = "Pick a .py file first.";
          return;
        }

        submitBtn.disabled = true;
        submitMsg.textContent = "Uploading...";
        try {
          const formData = new FormData();
          formData.append("file", fileInput.files[0]);
          const res = await fetch(`/submissions/python?name=${encodeURIComponent(name)}`, {
            method: "POST",
            body: formData,
          });
          if (!res.ok) {
            submitMsg.textContent = `Upload failed (${res.status})`;
            return;
          }
          const payload = await res.json();
          submitMsg.textContent = `Queued submission #${payload.id}`;
          await refreshSubmissions();
          await refreshLeaderboard();
        } catch (err) {
          submitMsg.textContent = "Upload failed";
        } finally {
          submitBtn.disabled = false;
        }
      });

      refreshLeaderboard();
      refreshSubmissions();
      initLatticeAnimation();
      setInterval(refreshLeaderboard, 10000);
      setInterval(refreshSubmissions, 5000);
    </script>
  </body>
</html>
"""


def render_read_more_page() -> str:
    docs_dir = Path(__file__).resolve().parents[2] / "docs"
    doc_html_path = docs_dir / "qec_quickstart.html"
    doc_txt_path = docs_dir / "qec_quickstart.txt"

    embedded_body = ""
    if doc_html_path.exists():
        raw = doc_html_path.read_text(encoding="utf-8")
        body_match = re.search(r"<body[^>]*>(.*?)</body>", raw, flags=re.IGNORECASE | re.DOTALL)
        embedded_body = body_match.group(1).strip() if body_match else raw
        embedded_body = re.sub(r'^\s*<p class="p1"><br></p>\s*', "", embedded_body, flags=re.IGNORECASE)
        embedded_body = re.sub(r'<span class="Apple-converted-space">.*?</span>', " ", embedded_body)
    elif doc_txt_path.exists():
        text = doc_txt_path.read_text(encoding="utf-8")
        embedded_body = f"<pre>{html.escape(text)}</pre>"
    else:
        embedded_body = "<p>Missing docs/qec_quickstart.html</p>"

    math_replacements = [
        (
            "|ψ⟩ = α|0⟩ + β|1⟩  where |α|² + |β|² = 1",
            "$$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle,\\quad |\\alpha|^2 + |\\beta|^2 = 1$$",
        ),
        (
            "ε(ρ) = (1-p)ρ + (p/3)(XρX + YρY + ZρZ)",
            "$$\\varepsilon(\\rho) = (1-p)\\rho + \\frac{{p}}{{3}}(X\\rho X + Y\\rho Y + Z\\rho Z)$$",
        ),
        (
            "C_ij = p · exp(-|i-j| / ξ)",
            "$$C_{{ij}} = p \\cdot e^{{-|i-j|/\\xi}}$$",
        ),
        (
            "p_L ~ (p / p_threshold)^((d+1)/2)",
            "$$p_L \\sim \\left(\\frac{{p}}{{p_{{\\text{{threshold}}}}}}\\right)^{{(d+1)/2}}$$",
        ),
        (
            "decode(syndrome_tensor) → int",
            "$$\\text{{decode}}(\\text{{syndrome_tensor}}) \\to \\mathbb{{Z}}$$",
        ),
        (
            "S = 0.7 × (improvement over MWPM) + 0.3 × min(1, throughput / 1M syndromes/sec)",
            "$$S = 0.7\\,(\\text{{improvement over MWPM}}) + 0.3\\,\\min\\!\\left(1, \\frac{{\\tau}}{{10^6}}\\right)$$",
        ),
    ]
    for src, dest in math_replacements:
        embedded_body = embedded_body.replace(src, dest)

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Quantum Error Correction - Read More</title>
    <style>
      @import url("https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@200..900&family=JetBrains+Mono:wght@100..800&display=swap");

      :root {{
        --bg: #f8f7f4;
        --text: #1f1f1f;
        --muted: #666;
        --border: #ddd7cf;
        --header-bg: #fff;
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font-family: "Crimson Pro", Georgia, serif;
        font-size: 18px;
      }}

      .site-header {{
        height: 64px;
        border-bottom: 1px solid var(--border);
        background: var(--header-bg);
      }}

      .header-row {{
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }}

      .header-left {{
        display: flex;
        align-items: center;
        gap: 24px;
      }}

      .brand {{
        color: var(--text);
        text-decoration: none;
        font-size: 1.125rem;
        font-weight: 600;
      }}

      .nav {{
        display: none;
      }}

      @media (min-width: 640px) {{
        .nav {{
          display: flex;
          align-items: center;
          gap: 4px;
        }}
      }}

      .nav-item {{
        color: var(--muted);
        position: relative;
        padding: 6px 20px 6px 10px;
        font-size: 0.88rem;
        text-decoration: none;
      }}

      .nav-item::after {{
        content: "";
        position: absolute;
        right: 7px;
        top: 50%;
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid currentColor;
        transform: translateY(-20%);
        opacity: 0.75;
      }}

      .avatar {{
        width: 32px;
        height: 32px;
        border-radius: 999px;
        background: #e5e7eb;
      }}

      .container {{
        width: 100%;
        max-width: 1080px;
        margin: 0 auto;
        padding: 0 20px;
      }}

      .page {{
        padding: 30px 0 54px;
      }}

      .top-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 18px;
      }}

      .title {{
        margin: 0;
        font-size: 1.95rem;
        font-weight: 700;
      }}

      .back-link {{
        display: inline-block;
        border: 1px solid var(--border);
        border-radius: 6px;
        background: #fff;
        color: var(--text);
        text-decoration: none;
        padding: 8px 12px;
        font-size: 0.95rem;
      }}

      .about-doc {{
        max-width: 760px;
        font-size: 1.03rem;
      }}

      .about-doc p {{
        margin: 0 0 0.8rem;
        line-height: 1.62;
        font-size: 1.03rem;
      }}

      .about-doc p.p2 {{
        font-size: 2.35rem;
        line-height: 1.1;
        margin: 0 0 0.35rem;
        color: var(--text);
        text-align: left;
      }}

      .about-doc p.p3 {{
        font-size: 1.22rem;
        line-height: 1.3;
        margin: 0 0 1rem;
        color: var(--muted);
        text-align: left;
      }}

      .about-doc p.p4,
      .about-doc p.p5 {{
        color: var(--muted);
        text-align: left;
        margin: 0 0 0.15rem;
      }}

      .about-doc p.p8 {{
        font-size: 1.64rem;
        line-height: 1.22;
        margin: 2.2rem 0 0.7rem;
        color: var(--text);
      }}

      .about-doc p.p14 {{
        font-size: 1.26rem;
        line-height: 1.35;
        margin: 1.35rem 0 0.35rem;
        color: var(--text);
      }}

      .about-doc p.p11 {{
        font-size: 1.12rem;
        line-height: 1.35;
        margin: 0.2rem 0 0.35rem;
      }}

      .about-doc p.p9,
      .about-doc p.p12,
      .about-doc p.p17,
      .about-doc p.p20,
      .about-doc p.p21,
      .about-doc p.p25,
      .about-doc p.p27,
      .about-doc p.p28 {{
        font-size: 1.03rem;
      }}

      .about-doc p.p23,
      .about-doc p.p24 {{
        font-family: "JetBrains Mono", monospace;
        font-size: 0.9rem;
        line-height: 1.5;
      }}

      .about-doc p.p1,
      .about-doc p.p6,
      .about-doc p.p7,
      .about-doc p.p10,
      .about-doc p.p13,
      .about-doc p.p15,
      .about-doc p.p18,
      .about-doc p.p19,
      .about-doc p.p24 {{
        margin: 0;
      }}

      .about-doc ul {{
        margin: 0.35rem 0 0.9rem 1.25rem;
        padding: 0;
      }}

      .about-doc li {{
        margin: 0.2rem 0;
        line-height: 1.55;
      }}

      .about-doc table {{
        width: 100%;
        border-collapse: collapse;
        margin: 0.65rem 0 1rem;
        font-size: 1rem;
      }}

      .about-doc td {{
        border: 1px solid var(--border);
        padding: 7px 8px;
        vertical-align: top;
      }}

      .about-doc td p {{
        margin: 0.2rem 0;
      }}

      /* Equation lines in the DOCX export are wrapped in single-cell tables. */
      .about-doc tr > td:only-child {{
        border: none;
        padding: 0;
      }}

      .about-doc pre {{
        margin: 0.5rem 0 1rem;
        background: #efede7;
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 10px 12px;
        font-family: "JetBrains Mono", monospace;
        font-size: 0.82rem;
        line-height: 1.45;
        white-space: pre-wrap;
        overflow-x: auto;
      }}
    </style>
    <script>
      window.MathJax = {{
        tex: {{
          inlineMath: [["$", "$"], ["\\\\(", "\\\\)"]],
          displayMath: [["$$", "$$"], ["\\\\[", "\\\\]"]]
        }},
        svg: {{ fontCache: "global" }}
      }};
    </script>
    <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  </head>
  <body>
    <header class="site-header">
      <div class="container header-row">
        <div class="header-left">
          <a class="brand" href="/">Optimization Arena</a>
          <nav class="nav">
            <a class="nav-item" href="#">Trading</a>
            <a class="nav-item" href="#">Gaming</a>
            <a class="nav-item" href="#">Language</a>
          </nav>
        </div>
        <div class="avatar"></div>
      </div>
    </header>
    <main class="container page">
      <div class="top-row">
        <h1 class="title">Quantum Error Correction</h1>
        <a class="back-link" href="/">Back</a>
      </div>
      <article class="about-doc">{embedded_body}</article>
    </main>
  </body>
</html>
"""
