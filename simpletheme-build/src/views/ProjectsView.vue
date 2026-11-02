<script setup lang="ts">
/**
 * ProjectsView — 项目收集
 *
 * 存档做过的项目：角色、周期、状态、做了什么、用了什么。
 */
import { computed } from 'vue'
import { mockProjects } from '@/lib/mock-data'

const list = computed(() =>
  [...mockProjects].sort((a, b) => (a.period < b.period ? 1 : -1)),
)

function statusTone(status: string) {
  if (/运行|进行|开发中/.test(status)) return 'is-live'
  if (/交付|上线|完成|已发布/.test(status)) return 'is-done'
  return ''
}
</script>

<template>
  <div class="projects-page">
    <header class="section-header">
      <h1>
        <span class="section-header__title">项目</span>
        <span class="section-header__subtitle">&nbsp;Projects.</span>
      </h1>
    </header>

    <p class="projects-intro">
      做过的项目存档，共 <strong>{{ mockProjects.length }}</strong> 个。
      每个只写清楚三件事：我负责什么、解决了什么问题、用了什么技术。
    </p>

    <div v-if="list.length" class="project-grid">
      <article v-for="item in list" :key="item.id" class="project-card">
        <div class="project-card__head">
          <h2 class="project-card__name">{{ item.name }}</h2>
          <span v-if="item.status" class="project-card__status" :class="statusTone(item.status)">
            {{ item.status }}
          </span>
        </div>

        <p class="project-card__meta">
          <span v-if="item.role">{{ item.role }}</span>
          <template v-if="item.role && item.period">
            <span class="project-card__dot">·</span>
          </template>
          <span v-if="item.period">{{ item.period }}</span>
        </p>

        <p class="project-card__summary">{{ item.summary }}</p>

        <div class="project-card__foot">
          <span v-for="tech in item.stack" :key="tech" class="project-card__tag">{{ tech }}</span>
          <a
            v-if="item.url"
            class="project-card__link"
            :href="item.url"
            target="_blank"
            rel="noopener noreferrer"
          >
            查看 →
          </a>
        </div>
      </article>
    </div>

    <div v-else class="projects-empty">还没有项目，去后台「项目」里添加。</div>
  </div>
</template>

<style scoped>
.projects-page {
  padding: 25px;
}

.projects-intro {
  margin: -6px 0 22px;
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--color-muted-foreground);
}

.projects-intro strong {
  color: var(--color-foreground);
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.project-card {
  display: flex;
  flex-direction: column;
  padding: 20px 22px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-large);
  background: var(--color-card);
  transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.project-card:hover {
  border-color: color-mix(in srgb, var(--color-primary) 22%, var(--color-border));
  box-shadow: var(--shadow-small, 0 6px 18px -12px rgba(0, 0, 0, 0.25));
  transform: translateY(-2px);
}

.project-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.project-card__name {
  margin: 0;
  font-size: 15.5px;
  font-weight: 700;
  line-height: 1.5;
  letter-spacing: -0.2px;
}

.project-card__status {
  flex: 0 0 auto;
  padding: 2px 9px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--color-muted-foreground) 12%, transparent);
  color: var(--color-muted-foreground);
  font-size: 11.5px;
  white-space: nowrap;
}

.project-card__status.is-live {
  background: color-mix(in srgb, #12936f 12%, transparent);
  color: #12936f;
}

.project-card__status.is-done {
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  color: var(--color-primary);
}

.project-card__meta {
  margin: 6px 0 0;
  font-size: 12.5px;
  color: var(--color-muted-foreground);
}

.project-card__dot {
  margin: 0 6px;
  opacity: 0.6;
}

.project-card__summary {
  flex: 1;
  margin: 12px 0 0;
  font-size: 13.5px;
  line-height: 1.85;
  color: var(--color-muted-foreground);
}

.project-card__foot {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 16px;
}

.project-card__tag {
  padding: 2px 9px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-muted-foreground);
  font-size: 11.5px;
}

.project-card__link {
  margin-left: auto;
  font-size: 12.5px;
  color: var(--color-primary);
  text-decoration: none;
}

.project-card__link:hover {
  text-decoration: underline;
}

.projects-empty {
  padding: 60px 0;
  text-align: center;
  color: var(--color-muted-foreground);
  font-size: 13.5px;
}

@media (max-width: 1000px) {
  .project-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 800px) {
  .projects-page {
    padding: 16px;
  }
}
</style>
