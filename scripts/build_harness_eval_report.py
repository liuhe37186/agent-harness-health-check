#!/usr/bin/env python3
"""Build a standalone HTML report for agent harness skill evaluations."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

DEFAULT_CONFIGS = [
    {"key": "with_skill", "label": "技能启用版", "description": "启用目标技能后的结果"},
    {"key": "without_skill", "label": "基线版", "description": "不启用技能的基线结果"},
]

DEFAULT_STAGE_ORDER = ["概念验证", "可内测", "可受控上线", "可规模化运行"]

HTML_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>__TITLE__</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f7fb;
      --card: #ffffff;
      --text: #17212f;
      --muted: #667085;
      --line: #d9e2ec;
      --primary: #2563eb;
      --primary-soft: #eaf2ff;
      --success: #16a34a;
      --warning: #f59e0b;
      --danger: #dc2626;
      --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
      --radius: 20px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: linear-gradient(180deg, #eef4fb 0%, #f8fbff 260px, #f4f7fb 100%);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .page { max-width: 1400px; margin: 0 auto; padding: 28px; }
    .hero {
      background: linear-gradient(135deg, #0f172a 0%, #1e40af 45%, #2563eb 100%);
      color: #fff;
      border-radius: 28px;
      padding: 28px 30px;
      box-shadow: 0 28px 60px rgba(37, 99, 235, 0.26);
    }
    .hero-top { display: flex; justify-content: space-between; gap: 24px; flex-wrap: wrap; }
    .hero h1 { margin: 0 0 8px; font-size: 30px; line-height: 1.2; }
    .hero p { margin: 6px 0; color: rgba(255,255,255,0.9); max-width: 900px; }
    .grade-box {
      min-width: 190px;
      background: rgba(255,255,255,0.12);
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 22px;
      padding: 18px 20px;
      backdrop-filter: blur(8px);
    }
    .grade-box .label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: rgba(255,255,255,0.74); }
    .grade-box .value { font-size: 42px; font-weight: 800; margin-top: 6px; }
    .chips { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
    .chip {
      padding: 7px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,0.12);
      border: 1px solid rgba(255,255,255,0.2);
      font-size: 13px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 14px;
      margin: 22px 0 10px;
    }
    .stat-card, .panel, .list-card, .run-card, .config-card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .stat-card { padding: 18px 18px 16px; }
    .stat-card .title { color: var(--muted); font-size: 13px; }
    .stat-card .value { margin-top: 8px; font-size: 30px; font-weight: 750; }
    .tab-bar { display: flex; gap: 10px; flex-wrap: wrap; margin: 24px 0 18px; }
    .tab-btn {
      border: 0; background: #e8eef7; color: #48607c;
      padding: 11px 16px; border-radius: 999px; font-size: 14px; font-weight: 600; cursor: pointer;
    }
    .tab-btn.active { background: var(--primary); color: #fff; box-shadow: 0 10px 24px rgba(37,99,235,0.22); }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    .outputs-layout { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 18px; align-items: start; }
    .list-card { padding: 14px; position: sticky; top: 18px; }
    .list-head {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 10px; padding: 4px 4px 10px; border-bottom: 1px solid var(--line);
    }
    .eval-list { display: grid; gap: 8px; max-height: calc(100vh - 180px); overflow: auto; padding-right: 2px; }
    .eval-item {
      border: 1px solid var(--line); background: #f8fbff; border-radius: 14px; padding: 12px; cursor: pointer;
    }
    .eval-item.active { border-color: var(--primary); background: var(--primary-soft); box-shadow: inset 0 0 0 1px rgba(37,99,235,0.08); }
    .eval-item .name { font-weight: 650; font-size: 14px; }
    .eval-item .meta { color: var(--muted); font-size: 12px; margin-top: 4px; }
    .content-col { display: grid; gap: 16px; }
    .panel { padding: 18px 20px; }
    .panel h2, .panel h3, .panel h4 { margin: 0 0 12px; }
    .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }
    .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }
    .info-block, .finding-block, .grade-block, .output-block, .feedback-block {
      border: 1px solid var(--line); border-radius: 16px; padding: 14px; background: #fbfdff;
    }
    .info-block .k, .section-title {
      font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted);
    }
    .info-block .k { margin-bottom: 6px; }
    .run-grid { display: grid; gap: 14px; }
    .run-card { padding: 18px; }
    .run-top { display: flex; justify-content: space-between; gap: 14px; flex-wrap: wrap; align-items: flex-start; margin-bottom: 14px; }
    .run-title { font-size: 18px; font-weight: 700; margin: 0 0 4px; }
    .muted, .run-desc { color: var(--muted); font-size: 13px; }
    .pill-row { display: flex; gap: 8px; flex-wrap: wrap; }
    .pill {
      border-radius: 999px; padding: 6px 10px; font-size: 12px; font-weight: 650; border: 1px solid transparent;
    }
    .pill.primary { background: var(--primary-soft); color: var(--primary); }
    .pill.good { background: rgba(22,163,74,0.12); color: var(--success); }
    .pill.warn { background: rgba(245,158,11,0.12); color: var(--warning); }
    .pill.bad { background: rgba(220,38,38,0.12); color: var(--danger); }
    .section-title { margin: 16px 0 8px; font-weight: 700; }
    pre {
      margin: 0; white-space: pre-wrap; word-break: break-word;
      background: #0f172a; color: #e2e8f0; border-radius: 14px; padding: 14px;
      font-size: 13px; line-height: 1.6; overflow: auto;
    }
    .grade-table, .benchmark-table, .review-table {
      width: 100%; border-collapse: collapse; font-size: 13px;
    }
    .grade-table th, .grade-table td, .benchmark-table th, .benchmark-table td, .review-table th, .review-table td {
      text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--line); vertical-align: top;
    }
    .grade-table th, .benchmark-table th, .review-table th { color: var(--muted); font-weight: 650; }
    textarea {
      width: 100%; min-height: 110px; border: 1px solid var(--line); border-radius: 14px;
      padding: 12px; font: inherit; resize: vertical; background: #fff; color: var(--text);
    }
    .action-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
    .btn {
      border: 0; border-radius: 12px; padding: 10px 14px; font-weight: 650; cursor: pointer;
      background: var(--primary); color: #fff;
    }
    .btn.secondary { background: #e7eef8; color: #35506f; }
    .benchmark-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
    .config-card { padding: 18px; }
    .config-card h3 { margin: 0 0 10px; font-size: 18px; }
    .metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
    .metric-box { background: #f8fbff; border: 1px solid var(--line); border-radius: 14px; padding: 12px; }
    .metric-box .k { color: var(--muted); font-size: 12px; }
    .metric-box .v { margin-top: 6px; font-size: 20px; font-weight: 750; }
    .bar-row { margin-top: 10px; }
    .bar-label { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--muted); margin-bottom: 6px; }
    .bar { height: 10px; border-radius: 999px; background: #edf2f7; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #3b82f6, #2563eb); }
    .bar-fill.good { background: linear-gradient(90deg, #22c55e, #16a34a); }
    .bar-fill.warn { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
    .bar-fill.bad { background: linear-gradient(90deg, #ef4444, #dc2626); }
    .list { margin: 0; padding-left: 20px; }
    .empty {
      padding: 12px; border-radius: 14px; background: #f8fafc; border: 1px dashed var(--line);
      color: var(--muted); font-size: 14px;
    }
    .finding-title { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
    .footer { text-align: center; color: var(--muted); font-size: 12px; margin: 20px 0 6px; }
    @media (max-width: 1024px) {
      .outputs-layout { grid-template-columns: 1fr; }
      .list-card { position: static; }
      .eval-list { max-height: none; }
    }
    @media (max-width: 720px) {
      .page { padding: 16px; }
      .hero { padding: 22px; }
      .hero h1 { font-size: 24px; }
      .metric-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <div class="hero-top">
        <div>
          <h1 id="heroTitle">Agent Harness 评测报告</h1>
          <p id="heroScope"></p>
          <p id="heroSummary"></p>
        </div>
        <div class="grade-box">
          <div class="label">Overall Grade</div>
          <div class="value" id="heroGrade">-</div>
          <div class="muted" id="heroScore"></div>
        </div>
      </div>
      <div class="chips" id="heroChips"></div>
    </section>

    <section class="stats" id="stats"></section>
    <section class="tab-bar" id="tabBar"></section>
    <section id="tab-outputs" class="tab-panel"></section>
    <section id="tab-benchmark" class="tab-panel"></section>
    <section id="tab-review" class="tab-panel"></section>

    <div class="footer">由 agent-harness-health-check 评测报告生成器生成</div>
  </div>

  <script>
    const REPORT_DATA = __REPORT_DATA__;
    const state = { tab: 'outputs', evalIndex: 0, feedback: loadFeedback() };

    function feedbackStorageKey() {
      return `agent-harness-eval-feedback::${REPORT_DATA.meta.skill_name}::${REPORT_DATA.meta.evaluation_date}`;
    }
    function loadFeedback() {
      try {
        const raw = localStorage.getItem(feedbackStorageKey());
        return raw ? JSON.parse(raw) : {};
      } catch (error) {
        return {};
      }
    }
    function saveFeedback() {
      localStorage.setItem(feedbackStorageKey(), JSON.stringify(state.feedback));
    }
    function escapeHtml(value) {
      return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }
    function formatNumber(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
      return Number(value).toFixed(2);
    }
    function formatInt(value) {
      if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
      return Math.round(Number(value)).toLocaleString('zh-CN');
    }
    function badgeClass(score) {
      if (score >= 85) return 'good';
      if (score >= 65) return 'warn';
      return 'bad';
    }
    function runFeedbackKey(evalId, configKey) {
      return `${evalId}::${configKey}`;
    }
    function setTab(tab) { state.tab = tab; renderTabs(); renderPanels(); }
    function setEval(index) { state.evalIndex = index; renderOutputs(); }

    function renderHero() {
      const meta = REPORT_DATA.meta;
      document.getElementById('heroTitle').textContent = `${meta.skill_name} Agent Harness 评测报告`;
      document.getElementById('heroScope').textContent = meta.scope || '';
      document.getElementById('heroSummary').textContent = meta.summary || '';
      document.getElementById('heroGrade').textContent = REPORT_DATA.overall_grade;
      document.getElementById('heroScore').textContent = `总分 ${formatNumber(REPORT_DATA.overall_score)} / 100`;
      const chips = [
        `版本 ${meta.version}`,
        `评测人 ${meta.evaluator}`,
        `评测日期 ${meta.evaluation_date}`,
        `评测对象 ${meta.audit_target || '-'}`,
        `用例数 ${REPORT_DATA.evals.length}`,
        `配置数 ${REPORT_DATA.configs.length}`,
        `生成时间 ${REPORT_DATA.generated_at}`
      ];
      document.getElementById('heroChips').innerHTML = chips.map(item => `<span class="chip">${escapeHtml(item)}</span>`).join('');
    }

    function renderStats() {
      const stats = [
        { title: '总分', value: formatNumber(REPORT_DATA.overall_score) },
        { title: '通过率', value: `${formatNumber(REPORT_DATA.pass_rate)}%` },
        { title: '已通过断言', value: `${REPORT_DATA.passed_assertions}/${REPORT_DATA.total_assertions}` },
        { title: 'P0 Findings', value: REPORT_DATA.benchmark.overview.total_p0_findings || 0 },
        { title: '平均耗时', value: REPORT_DATA.benchmark.overview.avg_duration_ms ? `${formatInt(REPORT_DATA.benchmark.overview.avg_duration_ms)} ms` : '-' },
        { title: '平均 Token', value: REPORT_DATA.benchmark.overview.avg_tokens ? formatInt(REPORT_DATA.benchmark.overview.avg_tokens) : '-' }
      ];
      document.getElementById('stats').innerHTML = stats.map(item => `
        <div class="stat-card">
          <div class="title">${escapeHtml(item.title)}</div>
          <div class="value">${escapeHtml(String(item.value))}</div>
        </div>
      `).join('');
    }

    function renderTabs() {
      const tabs = [
        { key: 'outputs', label: '结果详情' },
        { key: 'benchmark', label: '审计对比' },
        { key: 'review', label: '评测集概览' }
      ];
      document.getElementById('tabBar').innerHTML = tabs.map(tab => `
        <button class="tab-btn ${state.tab === tab.key ? 'active' : ''}" onclick="setTab('${tab.key}')">${tab.label}</button>
      `).join('');
    }

    function renderPanels() {
      ['outputs', 'benchmark', 'review'].forEach(key => {
        const node = document.getElementById(`tab-${key}`);
        node.className = `tab-panel ${state.tab === key ? 'active' : ''}`;
      });
      renderOutputs();
      renderBenchmark();
      renderReview();
    }

    function renderOutputs() {
      const root = document.getElementById('tab-outputs');
      const evals = REPORT_DATA.evals;
      const current = evals[state.evalIndex] || evals[0];
      if (!current) {
        root.innerHTML = `<div class="empty">没有可展示的评测用例。</div>`;
        return;
      }
      const listHtml = evals.map((item, index) => `
        <div class="eval-item ${index === state.evalIndex ? 'active' : ''}" onclick="setEval(${index})">
          <div class="name">${escapeHtml(item.title || item.id)}</div>
          <div class="meta">${escapeHtml(item.id)} · ${item.runs.length} 个结果</div>
        </div>
      `).join('');
      const assertions = current.assertions && current.assertions.length
        ? `<div class="panel"><h3>Assertions</h3><ul class="list">${current.assertions.map(item => `<li>${escapeHtml(item.text)}</li>`).join('')}</ul></div>`
        : '';
      root.innerHTML = `
        <div class="outputs-layout">
          <aside class="list-card">
            <div class="list-head">
              <strong>结果详情</strong>
              <span class="muted">${state.evalIndex + 1}/${evals.length}</span>
            </div>
            <div class="eval-list">${listHtml}</div>
            <div class="action-row">
              <button class="btn secondary" ${state.evalIndex === 0 ? 'disabled' : ''} onclick="setEval(Math.max(0, state.evalIndex - 1))">上一条</button>
              <button class="btn secondary" ${state.evalIndex === evals.length - 1 ? 'disabled' : ''} onclick="setEval(Math.min(REPORT_DATA.evals.length - 1, state.evalIndex + 1))">下一条</button>
            </div>
          </aside>
          <div class="content-col">
            <div class="panel">
              <h2>${escapeHtml(current.title || current.id)}</h2>
              <div class="muted">${escapeHtml(current.id)} · ${escapeHtml(current.summary || '未填写总结')}</div>
              <div class="grid-2" style="margin-top:14px;">
                <div class="info-block">
                  <div class="k">Prompt</div>
                  <pre>${escapeHtml(current.prompt || '未填写')}</pre>
                </div>
                <div class="info-block">
                  <div class="k">期望输出</div>
                  <pre>${escapeHtml(current.expected_output || '未填写')}</pre>
                </div>
              </div>
            </div>
            ${assertions}
            <div class="run-grid">${current.runs.map(run => renderRunCard(current, run)).join('')}</div>
            <div class="panel">
              <h3>反馈操作</h3>
              <div class="action-row">
                <button class="btn" onclick="downloadFeedback()">提交全部评审反馈</button>
                <button class="btn secondary" onclick="resetFeedback()">清空本地反馈</button>
              </div>
              <div class="muted" style="margin-top:10px;">点击提交会下载 feedback.json，便于回收人工评审意见。</div>
            </div>
          </div>
        </div>
      `;
    }

    function renderRunCard(evalItem, run) {
      const feedbackKey = runFeedbackKey(evalItem.id, run.config_key);
      const feedback = state.feedback[feedbackKey] || '';
      const outputsHtml = run.outputs && run.outputs.length
        ? run.outputs.map(output => `
            <div class="output-block">
              <div class="section-title">${escapeHtml(output.label || 'Output')}</div>
              ${output.path ? `<div class="muted" style="margin-bottom:8px;">文件：${escapeHtml(output.path)}</div>` : ''}
              <pre>${escapeHtml(output.content || '')}</pre>
            </div>
          `).join('')
        : `<div class="empty">没有输出内容。</div>`;
      const gradesHtml = run.formal_grades && run.formal_grades.length
        ? `
          <div class="grade-block">
            <div class="section-title">Formal Grades</div>
            <table class="grade-table">
              <thead><tr><th>Assertion</th><th>结果</th><th>Evidence</th></tr></thead>
              <tbody>
                ${run.formal_grades.map(item => `
                  <tr>
                    <td>${escapeHtml(item.text)}</td>
                    <td><span class="pill ${item.passed ? 'good' : 'bad'}">${item.passed ? 'PASS' : 'FAIL'}</span></td>
                    <td>${escapeHtml(item.evidence || '-')}</td>
                  </tr>`).join('')}
              </tbody>
            </table>
          </div>` : `<div class="empty">没有 formal grades。</div>`;
      const findingsHtml = run.findings && run.findings.length
        ? run.findings.map(item => `
            <div class="finding-block">
              <div class="finding-title">
                <strong>${escapeHtml(item.title || '未命名问题')}</strong>
                <span class="pill ${item.severity === 'P0' ? 'bad' : (item.severity === 'P1' ? 'warn' : 'primary')}">${escapeHtml(item.severity || 'P?')}</span>
              </div>
              <div class="muted">${escapeHtml(item.detail || '')}</div>
              ${item.remediation ? `<div style="margin-top:8px;"><strong>整改：</strong>${escapeHtml(item.remediation)}</div>` : ''}
            </div>
          `).join('')
        : `<div class="empty">没有 findings。</div>`;
      const domainHtml = run.audit_result && run.audit_result.domain_verdicts && run.audit_result.domain_verdicts.length
        ? `
          <table class="grade-table">
            <thead><tr><th>一级域</th><th>结论</th><th>风险</th></tr></thead>
            <tbody>
              ${run.audit_result.domain_verdicts.map(item => `
                <tr>
                  <td>${escapeHtml(item.domain || '-')}</td>
                  <td>${escapeHtml(item.verdict || '-')}</td>
                  <td>${escapeHtml(item.risk || '-')}</td>
                </tr>`).join('')}
            </tbody>
          </table>`
        : `<div class="empty">没有一级审计域判断。</div>`;
      const metricPills = [];
      if (run.score !== null && run.score !== undefined) metricPills.push(`<span class="pill primary">Score ${formatNumber(run.score)}</span>`);
      if (run.pass_rate !== null && run.pass_rate !== undefined) metricPills.push(`<span class="pill ${run.pass_rate >= 80 ? 'good' : (run.pass_rate >= 60 ? 'warn' : 'bad')}">Pass ${formatNumber(run.pass_rate)}%</span>`);
      if (run.audit_result && run.audit_result.maturity_stage) metricPills.push(`<span class="pill primary">${escapeHtml(run.audit_result.maturity_stage)}</span>`);
      if (run.audit_result && run.audit_result.confidence) metricPills.push(`<span class="pill primary">可信度 ${escapeHtml(run.audit_result.confidence)}</span>`);
      if (run.metrics.duration_ms) metricPills.push(`<span class="pill primary">${formatInt(run.metrics.duration_ms)} ms</span>`);
      if (run.metrics.tokens) metricPills.push(`<span class="pill primary">${formatInt(run.metrics.tokens)} tokens</span>`);
      return `
        <div class="run-card">
          <div class="run-top">
            <div>
              <div class="run-title">${escapeHtml(run.config_label)}</div>
              <div class="run-desc">${escapeHtml(run.summary || run.description || '未填写运行摘要')}</div>
            </div>
            <div class="pill-row">${metricPills.join('')}</div>
          </div>
          <div class="section-title">Output</div>
          ${outputsHtml}
          <div class="section-title">Formal Grades</div>
          ${gradesHtml}
          <div class="section-title">Findings</div>
          ${findingsHtml}
          <div class="section-title">Audit Result</div>
          <div class="grid-3">
            <div class="info-block"><div class="k">成熟度</div><div>${escapeHtml((run.audit_result && run.audit_result.maturity_stage) || '-')}</div></div>
            <div class="info-block"><div class="k">可信度</div><div>${escapeHtml((run.audit_result && run.audit_result.confidence) || '-')}</div></div>
            <div class="info-block"><div class="k">问题数</div><div>${run.findings ? run.findings.length : 0}</div></div>
          </div>
          <div style="margin-top:12px;">${domainHtml}</div>
          <div class="section-title">Feedback</div>
          <div class="feedback-block">
            <textarea placeholder="在这里记录你对该输出的反馈..." oninput="updateFeedback('${escapeHtml(evalItem.id)}','${escapeHtml(run.config_key)}', this.value)">${escapeHtml(feedback)}</textarea>
          </div>
        </div>
      `;
    }

    function updateFeedback(evalId, configKey, value) {
      state.feedback[runFeedbackKey(evalId, configKey)] = value;
      saveFeedback();
    }
    function downloadFeedback() {
      const reviews = Object.entries(state.feedback).map(([runId, feedback]) => ({ run_id: runId, feedback, timestamp: new Date().toISOString() }));
      const payload = {
        skill_name: REPORT_DATA.meta.skill_name,
        evaluation_date: REPORT_DATA.meta.evaluation_date,
        reviews,
        status: 'complete'
      };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'feedback.json';
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    }
    function resetFeedback() {
      if (!confirm('确认清空当前本地反馈吗？')) return;
      state.feedback = {};
      saveFeedback();
      renderOutputs();
    }

    function renderBenchmark() {
      const root = document.getElementById('tab-benchmark');
      const benchmark = REPORT_DATA.benchmark;
      const cards = benchmark.config_summaries.length
        ? benchmark.config_summaries.map(item => `
          <div class="config-card">
            <h3>${escapeHtml(item.config_label)}</h3>
            <div class="muted">${escapeHtml(item.description || '')}</div>
            <div class="metric-grid">
              <div class="metric-box"><div class="k">Pass Rate</div><div class="v">${formatNumber(item.pass_rate)}%</div></div>
              <div class="metric-box"><div class="k">Avg Score</div><div class="v">${item.avg_score !== null && item.avg_score !== undefined ? formatNumber(item.avg_score) : '-'}</div></div>
              <div class="metric-box"><div class="k">Avg P0 Findings</div><div class="v">${item.avg_p0_findings !== null && item.avg_p0_findings !== undefined ? formatNumber(item.avg_p0_findings) : '-'}</div></div>
              <div class="metric-box"><div class="k">Avg Findings</div><div class="v">${item.avg_findings !== null && item.avg_findings !== undefined ? formatNumber(item.avg_findings) : '-'}</div></div>
              <div class="metric-box"><div class="k">Avg Duration</div><div class="v">${item.avg_duration_ms ? `${formatInt(item.avg_duration_ms)} ms` : '-'}</div></div>
              <div class="metric-box"><div class="k">Avg Tokens</div><div class="v">${item.avg_tokens ? formatInt(item.avg_tokens) : '-'}</div></div>
            </div>
            <div class="bar-row">
              <div class="bar-label"><span>通过率</span><span>${formatNumber(item.pass_rate)}%</span></div>
              <div class="bar"><div class="bar-fill ${badgeClass(item.pass_rate)}" style="width:${Math.max(0, Math.min(100, item.pass_rate || 0))}%"></div></div>
            </div>
            <div class="bar-row">
              <div class="bar-label"><span>平均分</span><span>${item.avg_score !== null && item.avg_score !== undefined ? formatNumber(item.avg_score) : '-'}</span></div>
              <div class="bar"><div class="bar-fill ${badgeClass(item.avg_score || 0)}" style="width:${Math.max(0, Math.min(100, item.avg_score || 0))}%"></div></div>
            </div>
          </div>
        `).join('')
        : `<div class="empty">没有 benchmark 配置数据。</div>`;
      const headers = benchmark.config_summaries.map(item => `<th>${escapeHtml(item.config_label)}</th>`).join('');
      const rows = benchmark.assertion_breakdown.length
        ? benchmark.assertion_breakdown.map(item => {
          const cells = benchmark.config_summaries.map(config => {
            const rate = item.rates[config.config_key];
            return `<td>${rate === null || rate === undefined ? '-' : `${formatNumber(rate)}%`}</td>`;
          }).join('');
          return `<tr><td>${escapeHtml(item.text)}</td>${cells}</tr>`;
        }).join('')
        : `<tr><td colspan="${benchmark.config_summaries.length + 1}">没有 assertion breakdown 数据。</td></tr>`;
      const stageRows = benchmark.stage_breakdown.length
        ? benchmark.stage_breakdown.map(item => {
          const cells = benchmark.config_summaries.map(config => `<td>${item.counts[config.config_key] || 0}</td>`).join('');
          return `<tr><td>${escapeHtml(item.stage)}</td>${cells}</tr>`;
        }).join('')
        : `<tr><td colspan="${benchmark.config_summaries.length + 1}">没有成熟度分布数据。</td></tr>`;
      const observations = benchmark.observations && benchmark.observations.length
        ? `<ul class="list">${benchmark.observations.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`
        : `<div class="empty">暂无分析结论。</div>`;
      root.innerHTML = `
        <div class="content-col">
          <div class="panel">
            <h2>审计对比</h2>
            <div class="muted">对比各配置在 Agent Harness 审计场景中的通过率、成熟度判断与关键问题识别能力。</div>
            <div class="benchmark-grid" style="margin-top:16px;">${cards}</div>
          </div>
          <div class="panel">
            <h3>Assertion Breakdown</h3>
            <table class="benchmark-table">
              <thead><tr><th>Assertion</th>${headers}</tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
          <div class="panel">
            <h3>成熟度分布</h3>
            <table class="benchmark-table">
              <thead><tr><th>成熟度阶段</th>${headers}</tr></thead>
              <tbody>${stageRows}</tbody>
            </table>
          </div>
          <div class="panel">
            <h3>Analyzer Notes</h3>
            ${observations}
          </div>
        </div>
      `;
    }

    function renderReview() {
      const root = document.getElementById('tab-review');
      const rows = REPORT_DATA.evals.map(item => `
        <tr>
          <td>${escapeHtml(item.id)}</td>
          <td>${escapeHtml(item.title || '')}</td>
          <td><pre>${escapeHtml(item.prompt || '')}</pre></td>
          <td>${item.assertions && item.assertions.length ? `<ul class="list">${item.assertions.map(assertion => `<li>${escapeHtml(assertion.text)}</li>`).join('')}</ul>` : '<span class="muted">无</span>'}</td>
        </tr>
      `).join('');
      root.innerHTML = `
        <div class="content-col">
          <div class="panel">
            <h2>评测集概览</h2>
            <div class="muted">这里展示本轮评测集的 Prompt 与 assertions，便于核对覆盖范围。</div>
          </div>
          <div class="panel">
            <table class="review-table">
              <thead><tr><th>ID</th><th>Title</th><th>Prompt</th><th>Assertions</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
      `;
    }

    renderHero();
    renderStats();
    renderTabs();
    renderPanels();
  </script>
</body>
</html>
"""


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("评测输入必须是 JSON 对象")
    return data


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def compute_grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def normalize_meta(data: dict[str, Any]) -> dict[str, str]:
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    return {
        "skill_name": safe_text(meta.get("skill_name")).strip() or "agent-harness-health-check",
        "version": safe_text(meta.get("version")).strip() or "-",
        "evaluator": safe_text(meta.get("evaluator")).strip() or "未知",
        "evaluation_date": safe_text(meta.get("evaluation_date")).strip() or datetime.now().strftime("%Y-%m-%d"),
        "scope": safe_text(meta.get("scope")).strip() or "评估 Agent Harness 体检技能输出质量与诊断能力",
        "summary": safe_text(meta.get("summary")).strip(),
        "audit_target": safe_text(meta.get("audit_target")).strip(),
    }


def normalize_configs(data: dict[str, Any]) -> list[dict[str, str]]:
    raw = data.get("configs")
    configs: list[dict[str, str]] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            key = safe_text(item.get("key")).strip()
            if not key:
                continue
            configs.append(
                {
                    "key": key,
                    "label": safe_text(item.get("label")).strip() or key,
                    "description": safe_text(item.get("description")).strip(),
                }
            )
    return configs or DEFAULT_CONFIGS


def normalize_assertions(raw: Any) -> list[dict[str, str]]:
    result = []
    for item in as_list(raw):
        if isinstance(item, dict):
            text = safe_text(item.get("text") or item.get("assertion") or item.get("name")).strip()
        else:
            text = safe_text(item).strip()
        if text:
            result.append({"text": text})
    return result


def normalize_outputs(raw: Any) -> list[dict[str, str]]:
    outputs = []
    for index, item in enumerate(as_list(raw), start=1):
        if isinstance(item, dict):
            outputs.append(
                {
                    "label": safe_text(item.get("label")).strip() or f"Output {index}",
                    "content": safe_text(item.get("content")),
                    "path": safe_text(item.get("path")).strip(),
                }
            )
        else:
            text = safe_text(item).strip()
            if text:
                outputs.append({"label": f"Output {index}", "content": text, "path": ""})
    return outputs


def normalize_formal_grades(raw: Any) -> list[dict[str, Any]]:
    grades = []
    for item in as_list(raw):
        if not isinstance(item, dict):
            text = safe_text(item).strip()
            if text:
                grades.append({"text": text, "passed": False, "evidence": ""})
            continue
        text = safe_text(item.get("text") or item.get("assertion") or item.get("name")).strip()
        if not text:
            continue
        grades.append(
            {
                "text": text,
                "passed": bool(item.get("passed")),
                "evidence": safe_text(item.get("evidence")).strip(),
            }
        )
    return grades


def normalize_findings(raw: Any) -> list[dict[str, str]]:
    findings = []
    for item in as_list(raw):
        if not isinstance(item, dict):
            text = safe_text(item).strip()
            if text:
                findings.append({"severity": "", "title": text, "detail": "", "remediation": ""})
            continue
        title = safe_text(item.get("title")).strip()
        detail = safe_text(item.get("detail")).strip()
        if not title and not detail:
            continue
        findings.append(
            {
                "severity": safe_text(item.get("severity")).strip().upper(),
                "title": title or "未命名问题",
                "detail": detail,
                "remediation": safe_text(item.get("remediation")).strip(),
            }
        )
    return findings


def normalize_domain_verdicts(raw: Any) -> list[dict[str, str]]:
    rows = []
    for item in as_list(raw):
        if not isinstance(item, dict):
            continue
        domain = safe_text(item.get("domain")).strip()
        verdict = safe_text(item.get("verdict")).strip()
        risk = safe_text(item.get("risk")).strip().upper()
        if domain or verdict or risk:
            rows.append({"domain": domain, "verdict": verdict, "risk": risk})
    return rows


def normalize_audit_result(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"maturity_stage": "", "confidence": "", "domain_verdicts": []}
    return {
        "maturity_stage": safe_text(raw.get("maturity_stage")).strip(),
        "confidence": safe_text(raw.get("confidence")).strip(),
        "domain_verdicts": normalize_domain_verdicts(raw.get("domain_verdicts")),
    }


def run_score_from_grades(grades: list[dict[str, Any]]) -> float | None:
    if not grades:
        return None
    passed = sum(1 for item in grades if item["passed"])
    return round(passed / len(grades) * 100, 2)


def normalize_run(raw_run: dict[str, Any], config_lookup: dict[str, dict[str, str]]) -> dict[str, Any]:
    config_key = safe_text(raw_run.get("config_key")).strip() or "with_skill"
    config_meta = config_lookup.get(config_key, {"label": config_key, "description": ""})
    formal_grades = normalize_formal_grades(raw_run.get("formal_grades"))
    score = raw_run.get("score")
    score_value = round(float(score), 2) if score is not None else run_score_from_grades(formal_grades)
    pass_rate = run_score_from_grades(formal_grades) if formal_grades else score_value
    metrics = raw_run.get("metrics") if isinstance(raw_run.get("metrics"), dict) else {}
    return {
        "config_key": config_key,
        "config_label": safe_text(raw_run.get("config_label")).strip() or config_meta.get("label", config_key),
        "description": safe_text(raw_run.get("description")).strip() or config_meta.get("description", ""),
        "summary": safe_text(raw_run.get("summary") or raw_run.get("output_summary")).strip(),
        "outputs": normalize_outputs(raw_run.get("outputs")),
        "formal_grades": formal_grades,
        "findings": normalize_findings(raw_run.get("findings")),
        "audit_result": normalize_audit_result(raw_run.get("audit_result")),
        "metrics": {
            "duration_ms": float(metrics.get("duration_ms") or raw_run.get("duration_ms") or 0),
            "tokens": float(metrics.get("tokens") or raw_run.get("tokens") or 0),
        },
        "score": score_value,
        "pass_rate": pass_rate,
    }


def normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    meta = normalize_meta(data)
    configs = normalize_configs(data)
    config_lookup = {item["key"]: item for item in configs}
    raw_evals = data.get("evals")
    if not isinstance(raw_evals, list) or not raw_evals:
        raise ValueError("evals 至少需要 1 个用例")
    evals = []
    for index, raw_eval in enumerate(raw_evals, start=1):
        if not isinstance(raw_eval, dict):
            raise ValueError(f"evals[{index - 1}] 必须是对象")
        runs = [normalize_run(item, config_lookup) for item in as_list(raw_eval.get("runs")) if isinstance(item, dict)]
        if not runs:
            raise ValueError(f"评测用例 {raw_eval.get('id') or index} 至少需要 1 个 run")
        evals.append(
            {
                "id": safe_text(raw_eval.get("id")).strip() or f"eval-{index:03d}",
                "title": safe_text(raw_eval.get("title")).strip() or f"评测用例 {index}",
                "prompt": safe_text(raw_eval.get("prompt")),
                "expected_output": safe_text(raw_eval.get("expected_output") or raw_eval.get("expected")),
                "summary": safe_text(raw_eval.get("summary")).strip(),
                "assertions": normalize_assertions(raw_eval.get("assertions")),
                "runs": runs,
            }
        )
    return {"meta": meta, "configs": configs, "evals": evals, "benchmark_input": data.get("benchmark")}


def avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def stage_sort_key(stage: str) -> tuple[int, str]:
    if stage in DEFAULT_STAGE_ORDER:
        return (DEFAULT_STAGE_ORDER.index(stage), stage)
    return (len(DEFAULT_STAGE_ORDER), stage)


def build_benchmark(normalized: dict[str, Any]) -> dict[str, Any]:
    configs = normalized["configs"]
    evals = normalized["evals"]
    benchmark_input = normalized.get("benchmark_input") if isinstance(normalized.get("benchmark_input"), dict) else {}

    config_assertions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    config_scores: dict[str, list[float]] = defaultdict(list)
    config_durations: dict[str, list[float]] = defaultdict(list)
    config_tokens: dict[str, list[float]] = defaultdict(list)
    config_findings: dict[str, list[int]] = defaultdict(list)
    config_p0_findings: dict[str, list[int]] = defaultdict(list)
    stage_counts: dict[str, Counter[str]] = defaultdict(Counter)
    assertion_matrix: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))

    for eval_item in evals:
        for run in eval_item["runs"]:
            key = run["config_key"]
            config_assertions[key].extend(run["formal_grades"])
            if run.get("score") is not None:
                config_scores[key].append(float(run["score"]))
            if run["metrics"].get("duration_ms"):
                config_durations[key].append(float(run["metrics"]["duration_ms"]))
            if run["metrics"].get("tokens"):
                config_tokens[key].append(float(run["metrics"]["tokens"]))
            config_findings[key].append(len(run["findings"]))
            config_p0_findings[key].append(sum(1 for item in run["findings"] if item.get("severity") == "P0"))
            stage = run["audit_result"].get("maturity_stage")
            if stage:
                stage_counts[stage][key] += 1
            for grade in run["formal_grades"]:
                assertion_matrix[grade["text"]][key].append(bool(grade["passed"]))

    config_summaries = []
    for config in configs:
        key = config["key"]
        grades = config_assertions.get(key, [])
        passed = sum(1 for item in grades if item["passed"])
        pass_rate = round(passed / len(grades) * 100, 2) if grades else None
        config_summaries.append(
            {
                "config_key": key,
                "config_label": config["label"],
                "description": config.get("description", ""),
                "pass_rate": pass_rate,
                "avg_score": avg(config_scores[key]),
                "avg_duration_ms": avg(config_durations[key]),
                "avg_tokens": avg(config_tokens[key]),
                "avg_findings": avg([float(x) for x in config_findings[key]]),
                "avg_p0_findings": avg([float(x) for x in config_p0_findings[key]]),
            }
        )

    assertion_breakdown = []
    for text, per_config in sorted(assertion_matrix.items(), key=lambda item: item[0]):
        rates = {}
        for config in configs:
            values = per_config.get(config["key"], [])
            rates[config["key"]] = round(sum(1 for value in values if value) / len(values) * 100, 2) if values else None
        assertion_breakdown.append({"text": text, "rates": rates})

    stage_breakdown = []
    for stage in sorted(stage_counts.keys(), key=stage_sort_key):
        stage_breakdown.append({"stage": stage, "counts": dict(stage_counts[stage])})

    observations = []
    manual_observations = benchmark_input.get("observations")
    if manual_observations:
        observations.extend(safe_text(item).strip() for item in as_list(manual_observations) if safe_text(item).strip())

    if config_summaries:
        pass_ready = [item for item in config_summaries if item["pass_rate"] is not None]
        if pass_ready:
            best = max(pass_ready, key=lambda item: item["pass_rate"])
            observations.append(f"通过率最高的是 {best['config_label']}（{best['pass_rate']:.2f}%）。")
        score_ready = [item for item in config_summaries if item["avg_score"] is not None]
        if len(score_ready) >= 2:
            best_score = max(score_ready, key=lambda item: item["avg_score"])
            worst_score = min(score_ready, key=lambda item: item["avg_score"])
            if best_score["config_key"] != worst_score["config_key"]:
                observations.append(
                    f"综合分对比中，{best_score['config_label']} 高于 {worst_score['config_label']} {best_score['avg_score'] - worst_score['avg_score']:.2f} 分。"
                )
        p0_ready = [item for item in config_summaries if item["avg_p0_findings"] is not None]
        if p0_ready:
            most_p0 = max(p0_ready, key=lambda item: item["avg_p0_findings"])
            observations.append(f"{most_p0['config_label']} 平均识别到更多 P0 问题（{most_p0['avg_p0_findings']:.2f}）。")

    failed_counter: Counter[str] = Counter()
    for eval_item in evals:
        for run in eval_item["runs"]:
            for grade in run["formal_grades"]:
                if not grade["passed"]:
                    failed_counter[grade["text"]] += 1
    for text, count in failed_counter.most_common(3):
        observations.append(f"高频失败项：{text}（出现 {count} 次失败）。")

    all_durations = [item for values in config_durations.values() for item in values]
    all_tokens = [item for values in config_tokens.values() for item in values]
    total_p0_findings = sum(sum(values) for values in config_p0_findings.values())

    deduped = []
    seen = set()
    for item in observations:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)

    return {
        "config_summaries": config_summaries,
        "assertion_breakdown": assertion_breakdown,
        "stage_breakdown": stage_breakdown,
        "observations": deduped,
        "overview": {
            "avg_duration_ms": avg(all_durations),
            "avg_tokens": avg(all_tokens),
            "total_p0_findings": total_p0_findings,
        },
    }


def summarize(data: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_input(data)
    benchmark = build_benchmark(normalized)
    total_assertions = 0
    passed_assertions = 0
    overall_scores = []
    for eval_item in normalized["evals"]:
        best_score = None
        for run in eval_item["runs"]:
            total_assertions += len(run["formal_grades"])
            passed_assertions += sum(1 for item in run["formal_grades"] if item["passed"])
            if run.get("score") is not None:
                if best_score is None or float(run["score"]) > best_score:
                    best_score = float(run["score"])
        if best_score is not None:
            overall_scores.append(best_score)
    overall_score = avg(overall_scores) if overall_scores else (round(passed_assertions / total_assertions * 100, 2) if total_assertions else 0.0)
    pass_rate = round(passed_assertions / total_assertions * 100, 2) if total_assertions else 0.0
    return {
        "meta": normalized["meta"],
        "configs": normalized["configs"],
        "evals": normalized["evals"],
        "benchmark": benchmark,
        "overall_score": overall_score or 0.0,
        "overall_grade": compute_grade(overall_score or 0.0),
        "pass_rate": pass_rate,
        "total_assertions": total_assertions,
        "passed_assertions": passed_assertions,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def render_html(summary: dict[str, Any]) -> str:
    title = escape(f"{summary['meta']['skill_name']} - Agent Harness 评测报告")
    report_json = json.dumps(summary, ensure_ascii=False)
    return HTML_TEMPLATE.replace("__TITLE__", title).replace("__REPORT_DATA__", report_json)


def main() -> int:
    parser = argparse.ArgumentParser(description="根据 Agent Harness 评测 JSON 生成 HTML 报告")
    parser.add_argument("--input", required=True, help="评测 JSON 文件路径")
    parser.add_argument("--output", required=True, help="HTML 输出路径")
    parser.add_argument("--summary-output", help="可选，输出汇总 JSON 路径")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"找不到输入文件: {input_path}")

    summary = summarize(load_json(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html(summary), encoding="utf-8")

    summary_path = Path(args.summary_output).expanduser().resolve() if args.summary_output else output_path.with_suffix(".summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"已生成 HTML 报告: {output_path}")
    print(f"已生成汇总 JSON: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
