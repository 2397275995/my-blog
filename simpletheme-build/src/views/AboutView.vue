<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useHead } from '@unhead/vue'
import { useSiteShell } from '@/composables/useSiteShell'
import { fetchPage, getErrorMessage } from '@/lib/wordpress'
import { useContentEnhancer } from '@/composables/useContentEnhancer'
import type { WordPressPost } from '@/types/wordpress'
import ErrorView from '@/components/ErrorView.vue'
import { StCard, StStack, StSkeleton, useToast } from '@/ui'
import { BlockContent } from '@/blocks'

const { siteInfo } = useSiteShell()
const toast = useToast()

useHead({ title: '关于' })

const aboutPage = ref<WordPressPost | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const aboutContent = computed(() => aboutPage.value?.content?.rendered ?? null)
useContentEnhancer(aboutContent)

onMounted(async () => {
  try {
    aboutPage.value = await fetchPage('about')
  } catch (err) {
    errorMessage.value = getErrorMessage(err, '关于页面加载失败')
    toast.error(errorMessage.value)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="about-page">
    <StCard v-if="loading">
      <StStack gap="2">
        <StSkeleton />
        <StSkeleton />
        <StSkeleton width="60%" />
      </StStack>
    </StCard>

    <template v-else-if="aboutPage">
      <div class="content-area">
        <BlockContent class="prose-content" :html="aboutPage.content?.rendered" />
      </div>
    </template>

    <ErrorView
      v-else-if="errorMessage"
      illustration="warning"
      title="关于页面加载失败"
      :description="errorMessage"
    />

    <template v-else>
      <div class="content-area">
        <article class="prose-content">
          <div class="about-page__fallback">
            <h2>{{ siteInfo.name ? `欢迎来到 ${siteInfo.name}` : '关于本站' }}</h2>
            <p>记录技术、实践与思考。</p>
            <h3>关于本站</h3>
            <p>聚焦虚拟化、系统运维与效率工具，把复杂问题整理成可以复用的经验。这里记录踩过的坑、验证过的方案，以及那些值得写下来的思考。</p>
            <h3>联系方式</h3>
            <p>目前通过 RSS 订阅获取更新，其他联系方式待补充。</p>









































          </div>
        </article>
      </div>
    </template>
  </div>
</template>

<style scoped>
.about-page {
  padding: 25px;
}
</style>
