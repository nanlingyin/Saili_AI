<template>
  <section class="page">
    <div class="panel hero">
      <div>
        <p class="eyebrow">SaiLi AI / V1</p>
        <h1 class="page-title">把竞赛信息变成可行动的机会</h1>
        <p class="page-subtitle">
          聚合稳定数据源与人工录入，统一审核与发布流程，再用规则推荐与提醒，帮你把关键信息推进到下一步。
        </p>
        <div class="hero-actions">
          <router-link class="btn btn-primary" to="/competitions">浏览竞赛</router-link>
          <router-link class="btn btn-ghost" to="/recommendations">查看推荐</router-link>
        </div>
        <div class="chips">
          <span class="chip">入库 + 审核</span>
          <span class="chip">收藏订阅</span>
          <span class="chip">邮件提醒</span>
        </div>
      </div>
      <div class="hero-metrics">
        <div class="metric-card">
          <div class="metric-title">稳定数据源</div>
          <div class="metric-value">1 条已接入</div>
          <p class="page-subtitle">支持后台一键导入与去重更新。</p>
        </div>
        <div class="metric-card">
          <div class="metric-title">规则推荐</div>
          <div class="metric-value">V1 已启用</div>
          <p class="page-subtitle">按标签、截止与热度打分排序。</p>
        </div>
        <div class="metric-card">
          <div class="metric-title">审核流程</div>
          <div class="metric-value">人工兜底</div>
          <p class="page-subtitle">手动录入进入待审核后再发布。</p>
        </div>
      </div>
    </div>

    <ul class="list-grid cols-3">
      <li class="card">
        <h3 class="card-title">竞赛库与筛选</h3>
        <p class="page-subtitle">列表、详情、标签与关键词搜索，让信息可检索。</p>
      </li>
      <li class="card">
        <h3 class="card-title">收藏与订阅</h3>
        <p class="page-subtitle">关注竞赛或标签，形成你的长期信息池。</p>
      </li>
      <li class="card">
        <h3 class="card-title">提醒与推荐</h3>
        <p class="page-subtitle">按规则打分与截止提醒，让机会可触达。</p>
      </li>
    </ul>
  </section>
</template>
