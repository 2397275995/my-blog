<script setup lang="ts">
import { computed, onMounted, ref, onBeforeUnmount, watch, nextTick } from 'vue'
import { useHead } from '@unhead/vue'
import { useRoute, useRouter } from 'vue-router'
import { useSiteShell } from '@/composables/useSiteShell'
import { fetchCollection, fetchCategories, getErrorMessage } from '@/lib/wordpress'
import { withCache } from '@/lib/api-cache'
import { prefetchContent } from '@/lib/content-prefetch'
import { toInternalPath } from '@/lib/theme-config'
import { rememberPreviews } from '@/lib/content-preview'
import { useSkeletonSize } from '@/composables/useSkeletonSize'
import { getThemeConfig } from '@/lib/theme-config'
import type { PagedPostCollection, WordPressPost, WordPressCategory } from '@/types/wordpress'
import ErrorView from '@/components/ErrorView.vue'
import StaticFallback from '@/components/StaticFallback.vue'
import PostListSkeleton from '@/components/PostListSkeleton.vue'
import { useStaticFallback } from '@/composables/useStaticFallback'
import AppIcon from '@/components/AppIcon.vue'
import { StButton, useToast } from '@/ui'

const { siteInfo, ensureLoaded } = useSiteShell()
const toast = useToast()
const route = useRoute()
const router = useRouter()

const initialLoading = ref(false)
const loadingMore = ref(false)
const categoryLoading = ref(false)
const latestPosts = ref<WordPressPost[]>([])
const categories = ref<WordPressCategory[]>([])
const categoriesLoaded = ref(false)
const categoriesLoadFailed = ref(false)
const page = ref(1)
const totalPages = ref(0)
const hasMore = ref(true)
const errorMessage = ref('')
const { staticFallbackHtml } = useStaticFallback()

/**
 * 用静态存档兜底时，存档里已经带了页头与分类筛选（与 Vue 同一套结构），
 * 这里要把 SPA 自己的页头/筛选隐藏掉，否则会出现两份。
 */
const showStaticArchive = computed(() => Boolean(errorMessage.value && staticFallbackHtml.value))

/** Local category slug; '' means 'all'. Initialized from route param on mount. */
const categorySlug = ref((route.params.slug as string) || '')
const categoryNotFound = computed(
  () =>
    !!categorySlug.value &&
    categoriesLoaded.value &&
    !categoriesLoadFailed.value &&
    !categories.value.some((category) => category.slug === categorySlug.value),
)

const pageTitle = computed(() => {
  if (!categorySlug.value) return '首页'
  if (categoryNotFound.value) return '页面未找到'
  return categories.value.find((category) => category.slug === categorySlug.value)?.name || '分类'
})

useHead({ title: pageTitle })

const perPageCount = computed(() => siteInfo.value.collections?.homePostCount ?? 6)

// 骨架尺寸记忆：用上次真实卡片的高度/形态渲染骨架，避免加载完成时跳动
const { size: cardSize, measure: measureCard } = useSkeletonSize('st_sk_post_card')

const metaConfig = computed(() => getThemeConfig().features?.meta)

/** 卡片是否有任何 meta 需要展示 — 全部关闭时不渲染胶囊（否则出现空白悬浮胶囊） */
const hasCardMeta = (post: WordPressPost): boolean => {
  const m = metaConfig.value
  if (!m) return false
  return !!(
    (m.showCategory && post.categories?.[0]) ||
    m.showPublishDate ||
    (m.showModifiedDate && post.modified) ||
    (m.showCommentCount && post.commentCount !== undefined) ||
    (m.showViewCount && post.viewCount !== undefined) ||
    (m.showReadingTime && post.readingTime) ||
    (m.showWordCount && post.wordCount)
  )
}

const formatDate = (dateString: string) =>
  new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(dateString))

const formatModifiedDate = (dateString?: string) => {
  if (!dateString) return ''
  return '更新: ' + formatDate(dateString)
}

const formatWordCount = (count?: number) => {
  if (!count) return ''
  return count >= 1000 ? `${(count / 1000).toFixed(1)}k 字` : `${count} 字`
}

// ----- 无限滚动（基于 scroll + requestAnimationFrame）-----
let scrollRafId: number | null = null

function checkScrollAndLoad() {
  scrollRafId = null
  if (!hasMore.value || loadingMore.value) return
  const distFromBottom = document.documentElement.scrollHeight - (window.innerHeight + window.scrollY)
  // 距离底部 1200px 内触发加载，给足够余量应对快速滚动
  if (distFromBottom < 1200) {
    loadMorePosts()
  }
}

function onScroll() {
  if (scrollRafId !== null) return
  scrollRafId = requestAnimationFrame(checkScrollAndLoad)
}

function startInfiniteScroll() {
  window.addEventListener('scroll', onScroll, { passive: true })
  // 初始检查：如果页面已滚动过底部则立即触发
  checkScrollAndLoad()
}

function stopInfiniteScroll() {
  window.removeEventListener('scroll', onScroll)
  if (scrollRafId !== null) {
    cancelAnimationFrame(scrollRafId)
    scrollRafId = null
  }
}

onMounted(async () => {
  await loadHomepageData()
})

onBeforeUnmount(() => {
  stopInfiniteScroll()
  prefetchTimers.forEach((t) => clearTimeout(t))
  prefetchTimers.clear()
})

// Watch route param changes (category filter via /categories/:slug)
// For browser back/forward navigation — sync local ref and reload.
watch(
  () => route.params.slug,
  async (newSlug) => {
    categorySlug.value = (newSlug as string) || ''
    errorMessage.value = ''
    latestPosts.value = []
    page.value = 1
    hasMore.value = true
    totalPages.value = 0
    categoryLoading.value = true
    try {
      await loadPage(1)
    } finally {
      categoryLoading.value = false
    }
  },
)

let categoriesLoadPromise: Promise<void> | null = null

function loadCategories(): Promise<void> {
  if (!categoriesLoadPromise) {
    categoriesLoadPromise = withCache(fetchCategories, 'categories')()
      .then((data) => {
        categories.value = data
        categoriesLoadFailed.value = false
      })
      .catch(() => {
        // Categories are optional on the home page. A category URL must still
        // not fall back to an unfiltered post list when this request fails.
        categories.value = []
        categoriesLoadFailed.value = true
      })
      .finally(() => {
        categoriesLoaded.value = true
      })
  }

  return categoriesLoadPromise
}

function onCategoryClick(slug: string) {
  const newSlug = slug === 'all' ? '' : slug
  if (newSlug === categorySlug.value) return
  void router.push(newSlug ? `/categories/${encodeURIComponent(newSlug)}` : '/')
}

async function loadHomepageData() {
  initialLoading.value = true
  errorMessage.value = ''
  page.value = 1
  latestPosts.value = []

  try {
    await ensureLoaded()
    // Home can render immediately. A category route waits for its term ID below.
    const catPromise = loadCategories()
    await loadPage(1)
    await catPromise
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '首页内容加载失败，请稍后再试。')
    toast.error(errorMessage.value)
  } finally {
    initialLoading.value = false
  }
}

async function loadMorePosts() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true

  try {
    await loadPage(page.value + 1)
  } catch (error) {
    toast.error(getErrorMessage(error, '加载更多文章失败，请稍后再试。'))
  } finally {
    loadingMore.value = false
    requestAnimationFrame(checkScrollAndLoad)
  }
}

async function loadPage(pageNum: number, append = true) {
  // Capture slug at call time — if it changes mid-fetch, discard results
  const capturedSlug = categorySlug.value
  const slug = capturedSlug || undefined

  if (slug) {
    await loadCategories()
    if (capturedSlug !== categorySlug.value) return
  }

  let termId: number | undefined
  if (slug) {
    const found = categories.value.find((c) => c.slug === slug)
    if (found) termId = found.id
  }

  // Never turn an unknown or unavailable category into the all-posts view.
  if (slug && !termId) {
    if (pageNum === 1) latestPosts.value = []
    page.value = pageNum
    totalPages.value = 0
    hasMore.value = false
    if (categoriesLoadFailed.value) {
      errorMessage.value = '分类数据加载失败，请稍后再试。'
    }
    return
  }

  const postsResponse: PagedPostCollection = await fetchCollection('post', {
    limit: perPageCount.value,
    page: pageNum,
    taxonomy: termId ? 'category' : undefined,
    termId,
  })

  const newItems = postsResponse.items || []

  // append=false 时用整页替换（翻页模式）；append=true 时追加（无限滚动模式）
  if (pageNum === 1 || !append) {
    // Stale check: if user clicked another category while we were fetching, discard
    if (capturedSlug !== categorySlug.value) return
    latestPosts.value = newItems
    // 测量首张真实卡片，供下次骨架使用真实尺寸
    void measureCard('.post-list__grid .post-card', '.post-card__cover')
  } else {
    latestPosts.value = [...latestPosts.value, ...newItems]
  }

  // 写入详情页预览缓存（标题/特色图），让文章页骨架精准渲染
  rememberPreviews(newItems)

  page.value = pageNum
  totalPages.value = postsResponse.totalPages
  hasMore.value = pageNum < postsResponse.totalPages
}

// ----- 分页（翻页模式，替换掉无限滚动）-----
const pagingLoading = ref(false)

/** 当前页码两侧的窗口，最多 7 个，超出则滑动 */
const pageNumbers = computed(() => {
  const total = totalPages.value
  const current = page.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const start = Math.max(1, Math.min(current - 3, total - 6))
  return Array.from({ length: 7 }, (_, i) => start + i)
})

async function goToPage(target: number) {
  if (pagingLoading.value) return
  if (target < 1) return
  if (totalPages.value && target > totalPages.value) return
  if (target === page.value) return

  pagingLoading.value = true
  try {
    await loadPage(target, false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (error) {
    toast.error(getErrorMessage(error, '翻页失败，请稍后再试。'))
  } finally {
    pagingLoading.value = false
  }
}

// ----- 悬停预取文章内容 (hover prefetch) -----
const prefetchTimers = new Map<number, ReturnType<typeof setTimeout>>()

function prefetchPost(post: WordPressPost) {
  const t = prefetchTimers.get(post.id)
  if (t) clearTimeout(t)
  prefetchTimers.set(
    post.id,
    setTimeout(() => {
      prefetchContent(toInternalPath(post.link))
    }, 200),
  )
}

function cancelPrefetch(post: WordPressPost) {
  const t = prefetchTimers.get(post.id)
  if (t) { clearTimeout(t); prefetchTimers.delete(post.id) }
}

</script>

<template>
  <div class="home-content">
    <!-- Page Header -->
    <header v-if="!showStaticArchive" class="section-header">
      <h1>
        <span class="section-header__title">{{ pageTitle }}</span>
        <span class="section-header__subtitle">{{ categorySlug ? 'Category.' : 'Home.' }}</span>
      </h1>
      <a
        v-if="!categorySlug"
        class="write-entry"
        href="/write.html"
        target="_blank"
        rel="noopener noreferrer"
      >
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 20h4l10-10a2.8 2.8 0 0 0-4-4L4 16z" />
          <path d="M13.5 6.5 17.5 10.5" />
        </svg>
        写博客
      </a>
    </header>



    <!-- Latest Posts -->
    <section>
      <!-- Filter bar -->
      <div v-if="!showStaticArchive" class="home-content__filters">
        <StButton
          size="small"
          round
          :type="categorySlug === '' ? 'primary' : 'default'"
          @click="onCategoryClick('all')"
        >
          全部
        </StButton>
        <StButton
          v-for="cat in categories"
          :key="cat.id"
          size="small"
          round
          :type="categorySlug === cat.slug ? 'primary' : 'default'"
          @click="onCategoryClick(cat.slug)"
        >
          {{ cat.name }}
        </StButton>
      </div>

      <!-- Error state overlays everything -->
      <StaticFallback
        v-if="errorMessage && staticFallbackHtml"
        :html="staticFallbackHtml"
      />
      <ErrorView
        v-else-if="errorMessage"
        illustration="warning"
        title="首页加载失败"
        :description="errorMessage"
      />

      <!-- Progressively rendered post cards: skeleton → real cards -->
      <template v-else>
        <!-- Skeleton grid (initial load only — category transitions skip skeleton) -->
        <PostListSkeleton
          v-if="initialLoading && latestPosts.length === 0"
          :count="perPageCount"
          :card-height="cardSize?.h"
          :show-cover="cardSize?.cover !== false"
        />

        <!-- Real post cards -->
        <div v-else class="post-list">
          <div class="post-list__grid">
            <article
              v-for="post in latestPosts"
              :key="post.id"
              class="post-card"
              @mouseenter="prefetchPost(post)"
              @mouseleave="cancelPrefetch(post)"
            >
              <router-link
                v-if="post.featuredImage"
                :to="toInternalPath(post.link)"
                class="post-card__cover-link"
                tabindex="-1"
                aria-hidden="true"
              >
                <img
                  :src="post.featuredImage"
                  alt=""
                  loading="lazy"
                  class="post-card__cover"
                />
              </router-link>
              <div v-if="hasCardMeta(post)" class="post-card__meta">
                <span v-if="metaConfig?.showCategory && post.categories?.[0]" class="post-card__meta-item">{{ post.categories[0] }}</span>
                <time v-if="metaConfig?.showPublishDate" :datetime="post.date" class="post-card__meta-item">{{ formatDate(post.date) }}</time>
                <time v-if="metaConfig?.showModifiedDate && post.modified" :datetime="post.modified" class="post-card__meta-item">{{ formatModifiedDate(post.modified) }}</time>
                <span v-if="metaConfig?.showCommentCount && post.commentCount !== undefined" class="post-card__meta-item">{{ post.commentCount }} 评论</span>
                <span v-if="metaConfig?.showViewCount && post.viewCount !== undefined" class="post-card__meta-item">{{ post.viewCount }} 热度</span>
                <span v-if="metaConfig?.showReadingTime && post.readingTime" class="post-card__meta-item">{{ post.readingTime }} 分钟</span>
                <span v-if="metaConfig?.showWordCount && post.wordCount" class="post-card__meta-item">{{ formatWordCount(post.wordCount) }}</span>
              </div>
              <div class="post-card__body">
                <h2 class="post-card__title">
                  <span v-if="post.isSticky" class="post-card__sticky">
                    <AppIcon name="pin" filled :size="13" />置顶
                  </span>
                  <router-link :to="toInternalPath(post.link)">
                    <span v-html="post.title.rendered"></span>
                  </router-link>
                </h2>
                <p v-if="post.excerpt?.rendered" class="post-card__excerpt" v-html="post.excerpt.rendered"></p>
              </div>
            </article>
          </div>
        </div>

        <!-- Empty state (not during initial load or category loading) -->
        <ErrorView
          v-if="!initialLoading && !categoryLoading && latestPosts.length === 0"
          :illustration="categoryNotFound ? 'searching' : 'blank-canvas'"
          :title="categoryNotFound ? '未找到该分类' : '还没有文章'"
          :description="categoryNotFound ? '这个分类不存在或已被删除。' : '还没有文章，稍后回来看看吧。'"
        />

        <!-- Loading more skeleton (appended below existing posts) -->
        <PostListSkeleton
          v-if="loadingMore"
          class="post-list--more"
          :count="3"
          :card-height="cardSize?.h"
          :show-cover="cardSize?.cover !== false"
        />

      </template>

      <!-- 翻页 -->
      <nav v-if="totalPages > 1 && !initialLoading" class="pager" aria-label="分页导航">
        <button
          type="button"
          class="pager__arrow"
          :disabled="page <= 1 || pagingLoading"
          @click="goToPage(page - 1)"
        >
          上一页
        </button>

        <button
          v-for="n in pageNumbers"
          :key="n"
          type="button"
          class="pager__num"
          :class="{ 'is-current': n === page }"
          :disabled="pagingLoading"
          :aria-current="n === page ? 'page' : undefined"
          @click="goToPage(n)"
        >
          {{ n }}
        </button>

        <button
          type="button"
          class="pager__arrow"
          :disabled="page >= totalPages || pagingLoading"
          @click="goToPage(page + 1)"
        >
          下一页
        </button>
      </nav>
    </section>

    <!-- End note (only meaningful when everything fits on one page) -->
    <p v-if="!hasMore && latestPosts.length > 0 && totalPages <= 1" class="end-note">{{ siteInfo.endNote || '好像就这么多' }}</p>
  </div>
</template>

<style scoped>
.home-content {
  padding: 25px;
}

@media (max-width: 800px) {
  .home-content {
    padding: 20px;
  }
}

@media (max-width: 37.5rem) {
  .home-content {
    padding: 15px;
  }
}

.home-content__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 24px;
}

.post-list--more {
  margin-top: 24px;
}

/* ----- 翻页 ----- */
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  margin: 32px 0 8px;
}

.pager__arrow,
.pager__num {
  min-width: 38px;
  height: 38px;
  padding: 0 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-small, 8px);
  border: 1px solid var(--color-border);
  background: var(--color-card);
  color: var(--color-muted-foreground);
  font-size: 13.5px;
  line-height: 1;
  cursor: pointer;
  transition:
    background 0.18s ease,
    color 0.18s ease,
    border-color 0.18s ease;
}

.pager__arrow:hover:not(:disabled),
.pager__num:hover:not(:disabled) {
  color: var(--color-foreground);
  background: var(--color-secondary);
  border-color: color-mix(in srgb, var(--color-primary) 32%, var(--color-border));
}

.pager__num.is-current {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-primary-foreground);
  font-weight: 600;
}

.pager__arrow:disabled,
.pager__num:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 560px) {
  .pager__arrow,
  .pager__num {
    height: 34px;
    min-width: 34px;
    padding: 0 10px;
    font-size: 12.5px;
  }
}
</style>

<style scoped>
/* 首页右上角「写博客」入口 */
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.write-entry {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 14px;
  margin-left: auto;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-card);
  color: var(--color-muted-foreground);
  font-size: 12.5px;
  text-decoration: none;
  white-space: nowrap;
  transition:
    color 0.18s ease,
    border-color 0.18s ease,
    background-color 0.18s ease;
}

.write-entry:hover {
  color: var(--color-primary);
  border-color: color-mix(in srgb, var(--color-primary) 34%, var(--color-border));
  background: color-mix(in srgb, var(--color-primary) 6%, var(--color-card));
}

@media (max-width: 640px) {
  .write-entry {
    padding: 0 10px;
  }
}
</style>
