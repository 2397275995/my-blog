<script setup lang="ts">
/**
 * AwardsView — 奖项收集
 *
 * 存档获奖证书：级别、颁发单位、时间，证书图片可选。
 */
import { computed } from 'vue'
import { mockAwards } from '@/lib/mock-data'

const list = computed(() =>
  [...mockAwards].sort((a, b) => (a.date < b.date ? 1 : -1)),
)

const counts = computed(() => {
  const map: Record<string, number> = {}
  for (const item of mockAwards) {
    const key = item.level || '其他'
    map[key] = (map[key] || 0) + 1
  }
  return map
})
</script>

<template>
  <div class="awards-page">
    <header class="section-header">
      <h1>
        <span class="section-header__title">奖项</span>
        <span class="section-header__subtitle">&nbsp;Awards.</span>
      </h1>
    </header>

    <p class="awards-intro">
      获奖记录，共 <strong>{{ mockAwards.length }}</strong> 项。
      证书原件扫描后可在后台关联图片，点开即可查看。
    </p>

    <div v-if="list.length" class="award-grid">
      <article v-for="item in list" :key="item.id" class="award-card">
        <div class="award-card__badge" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 21h8" />
            <path d="M12 17v4" />
            <path d="M7 4h10v6a5 5 0 0 1-10 0z" />
            <path d="M17 5h2a2 2 0 0 1 0 4h-2" />
            <path d="M7 5H5a2 2 0 0 0 0 4h2" />
          </svg>
        </div>

        <div class="award-card__body">
          <div class="award-card__head">
            <h2 class="award-card__name">{{ item.name }}</h2>
            <span v-if="item.level" class="award-card__level">{{ item.level }}</span>
          </div>
          <p class="award-card__meta">
            <span v-if="item.issuer">{{ item.issuer }}</span>
            <template v-if="item.issuer && item.date">
              <span class="award-card__dot">·</span>
            </template>
            <span v-if="item.date">{{ item.date }}</span>
          </p>
          <p v-if="item.summary" class="award-card__summary">{{ item.summary }}</p>

          <a
            v-if="item.certificate"
            class="award-card__file"
            :href="item.certificate"
            target="_blank"
            rel="noopener noreferrer"
          >
            查看证书
          </a>
        </div>
      </article>
    </div>

    <div v-else class="awards-empty">还没有获奖记录，去后台「奖项」里添加。</div>

    <div v-if="Object.keys(counts).length > 1" class="awards-summary">
      <span v-for="(num, level) in counts" :key="level">{{ level }} {{ num }}</span>
    </div>
  </div>
</template>

<style scoped>
.awards-page {
  padding: 25px;
}

.awards-intro {
  margin: -6px 0 22px;
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--color-muted-foreground);
}

.awards-intro strong {
  color: var(--color-foreground);
}

.award-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.award-card {
  display: flex;
  gap: 18px;
  padding: 20px 22px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-large);
  background: var(--color-card);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.award-card:hover {
  border-color: color-mix(in srgb, var(--color-primary) 22%, var(--color-border));
  box-shadow: var(--shadow-small, 0 6px 18px -12px rgba(0, 0, 0, 0.25));
}

.award-card__badge {
  flex: 0 0 auto;
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #f6c445, #e79b2b);
  color: #7a4c06;
}

.award-card__badge svg {
  width: 24px;
  height: 24px;
}

.award-card__body {
  flex: 1;
  min-width: 0;
}

.award-card__head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.award-card__name {
  margin: 0;
  font-size: 15.5px;
  font-weight: 700;
  letter-spacing: -0.2px;
}

.award-card__level {
  padding: 2px 9px;
  border-radius: 6px;
  background: color-mix(in srgb, #e79b2b 16%, transparent);
  color: #9a6512;
  font-size: 11.5px;
}

.award-card__meta {
  margin: 6px 0 0;
  font-size: 12.5px;
  color: var(--color-muted-foreground);
}

.award-card__dot {
  margin: 0 6px;
  opacity: 0.6;
}

.award-card__summary {
  margin: 10px 0 0;
  font-size: 13.5px;
  line-height: 1.85;
  color: var(--color-muted-foreground);
}

.award-card__file {
  display: inline-block;
  margin-top: 12px;
  font-size: 12.5px;
  color: var(--color-primary);
  text-decoration: none;
}

.award-card__file:hover {
  text-decoration: underline;
}

.awards-summary {
  display: flex;
  gap: 14px;
  margin-top: 18px;
  font-size: 12px;
  color: var(--color-muted-foreground);
  opacity: 0.85;
}

.awards-empty {
  padding: 60px 0;
  text-align: center;
  color: var(--color-muted-foreground);
  font-size: 13.5px;
}

@media (max-width: 800px) {
  .awards-page {
    padding: 16px;
  }

  .award-card {
    gap: 14px;
    padding: 16px;
  }
}
</style>
