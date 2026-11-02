<script setup lang="ts">
/**
 * PapersView — 论文收集
 *
 * 存档读过的论文：按方向分类，每篇配一句话结论，方便回看时快速唤起记忆。
 */
import { computed, ref } from 'vue'
import { mockPapers } from '@/lib/mock-data'

const activeCategory = ref('全部')

const categories = computed(() => {
  const set = new Set<string>()
  for (const p of mockPapers) {
    if (p.category) set.add(p.category)
  }
  return ['全部', ...Array.from(set)]
})

const list = computed(() => {
  const papers = [...mockPapers].sort((a, b) => (a.readDate < b.readDate ? 1 : -1))
  if (activeCategory.value === '全部') return papers
  return papers.filter((p) => p.category === activeCategory.value)
})

function hostOf(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return ''
  }
}
</script>

<template>
  <div class="papers-page">
    <header class="section-header">
      <h1>
        <span class="section-header__title">论文</span>
        <span class="section-header__subtitle">&nbsp;Papers.</span>
      </h1>
    </header>

    <p class="papers-intro">
      读过的论文存档，共 <strong>{{ mockPapers.length }}</strong> 篇。每篇只记一句结论——
      半年后再看，能立刻想起它解决了什么问题。
    </p>

    <div v-if="categories.length > 1" class="papers-filters">
      <button
        v-for="cat in categories"
        :key="cat"
        type="button"
        class="papers-chip"
        :class="{ 'is-active': cat === activeCategory }"
        @click="activeCategory = cat"
      >
        {{ cat }}
      </button>
    </div>

    <ul v-if="list.length" class="paper-list">
      <li v-for="paper in list" :key="paper.id" class="paper-card">
        <div class="paper-card__head">
          <h2 class="paper-card__title">
            <a
              v-if="paper.url"
              :href="paper.url"
              target="_blank"
              rel="noopener noreferrer"
            >{{ paper.title }}</a>
            <span v-else>{{ paper.title }}</span>
          </h2>
          <span class="paper-card__year">{{ paper.year }}</span>
        </div>

        <p class="paper-card__meta">
          <span>{{ paper.authors }}</span>
          <template v-if="paper.venue">
            <span class="paper-card__dot">·</span>
            <span>{{ paper.venue }}</span>
          </template>
          <template v-if="paper.url">
            <span class="paper-card__dot">·</span>
            <a class="paper-card__host" :href="paper.url" target="_blank" rel="noopener noreferrer">
              {{ hostOf(paper.url) }}
            </a>
          </template>
        </p>

        <p class="paper-card__summary">{{ paper.summary }}</p>

        <div class="paper-card__foot">
          <span v-if="paper.category" class="paper-card__cat">{{ paper.category }}</span>
          <span
            v-for="tag in paper.tags.filter((t) => t !== paper.category)"
            :key="tag"
            class="paper-card__tag"
          >{{ tag }}</span>
          <span v-if="paper.readDate" class="paper-card__date">读于 {{ paper.readDate }}</span>
        </div>
      </li>
    </ul>

    <div v-else class="papers-empty">
      <p>这个方向还没有收录论文。</p>
      <p class="papers-empty__hint">在后台「论文」里添加即可。</p>
    </div>
  </div>
</template>

<style scoped>
.papers-page {
  padding: 25px;
}

.papers-intro {
  margin: -6px 0 22px;
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--color-muted-foreground);
}

.papers-intro strong {
  color: var(--color-foreground);
}

.papers-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.papers-chip {
  height: 30px;
  padding: 0 14px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-card);
  color: var(--color-muted-foreground);
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.18s ease;
}

.papers-chip:hover {
  color: var(--color-foreground);
  border-color: color-mix(in srgb, var(--color-primary) 32%, var(--color-border));
}

.papers-chip.is-active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-primary-foreground);
  font-weight: 600;
}

.paper-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.paper-card {
  padding: 20px 22px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-large);
  background: var(--color-card);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.paper-card:hover {
  border-color: color-mix(in srgb, var(--color-primary) 22%, var(--color-border));
  box-shadow: var(--shadow-small, 0 6px 18px -12px rgba(0, 0, 0, 0.25));
}

.paper-card__head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.paper-card__title {
  flex: 1;
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.5;
  letter-spacing: -0.2px;
}

.paper-card__title a {
  color: var(--color-foreground);
  text-decoration: none;
}

.paper-card__title a:hover {
  color: var(--color-primary);
}

.paper-card__year {
  flex: 0 0 auto;
  font-size: 12.5px;
  color: var(--color-muted-foreground);
  font-variant-numeric: tabular-nums;
  padding-top: 3px;
}

.paper-card__meta {
  margin: 6px 0 0;
  font-size: 12.5px;
  color: var(--color-muted-foreground);
  line-height: 1.7;
}

.paper-card__dot {
  margin: 0 6px;
  opacity: 0.6;
}

.paper-card__host {
  color: var(--color-muted-foreground);
  text-decoration: none;
}

.paper-card__host:hover {
  color: var(--color-primary);
  text-decoration: underline;
}

.paper-card__summary {
  margin: 12px 0 0;
  font-size: 14px;
  line-height: 1.85;
  color: var(--color-foreground-muted, var(--color-muted-foreground));
}

.paper-card__foot {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.paper-card__cat {
  padding: 2px 9px;
  border-radius: 6px;
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  color: var(--color-primary);
  font-size: 11.5px;
}

.paper-card__tag {
  padding: 2px 9px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-muted-foreground);
  font-size: 11.5px;
}

.paper-card__date {
  margin-left: auto;
  font-size: 11.5px;
  color: var(--color-muted-foreground);
  opacity: 0.8;
}

.papers-empty {
  padding: 60px 0;
  text-align: center;
  color: var(--color-muted-foreground);
  font-size: 13.5px;
}

.papers-empty__hint {
  margin-top: 6px;
  font-size: 12.5px;
  opacity: 0.75;
}

@media (max-width: 800px) {
  .papers-page {
    padding: 16px;
  }

  .paper-card {
    padding: 16px 16px 14px;
  }

  .paper-card__date {
    margin-left: 0;
  }
}
</style>
