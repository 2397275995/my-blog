import {
  mockSiteInfo,
  mockMenuItems,
  mockPosts,
  mockShuoshuo,
  mockCategories,
  mockLinkCategories,
} from '@/lib/mock-data'
import type {
  MenuCollectionResponse,
  PagedPostCollection,
  ResolveResponse,
  SiteInfo,
  WordPressPost,
  WordPressCategory,
  WordPressLinkCategory,
} from '@/types/wordpress'

const isMockMode = import.meta.env.VITE_USE_MOCK === 'true'

export function shouldUseMock() {
  return isMockMode
}

export async function mockFetchSiteInfo(): Promise<SiteInfo> {
  await simulateDelay(300)
  return mockSiteInfo
}

export async function mockFetchNavigation(_location: string): Promise<MenuCollectionResponse['items']> {
  await simulateDelay(200)
  return mockMenuItems
}

export async function mockFetchCollection(
  type: 'post' | 'page' | 'shuoshuo',
  options?: { limit?: number; page?: number; taxonomy?: string; termId?: number },
): Promise<PagedPostCollection> {
  await simulateDelay(400)

  const limit = options?.limit || 6
  const page = options?.page || 1

  let allItems: WordPressPost[] = []
  if (type === 'post') {
    allItems = mockPosts
  } else if (type === 'shuoshuo') {
    allItems = mockShuoshuo
  }

  // Filter by category if taxonomy and termId are provided
  let items = allItems
  if (options?.taxonomy === 'category' && options.termId) {
    const category = mockCategories.find((c) => c.id === options.termId)
    if (category) {
      items = allItems.filter((post) => post.categories?.includes(category.name))
    }
  }

  const start = (page - 1) * limit
  const end = start + limit
  const pagedItems = items.slice(start, end)

  return {
    items: pagedItems,
    total: items.length,
    totalPages: Math.ceil(items.length / limit),
    page,
    perPage: limit,
  }
}

export async function mockFetchCategories(): Promise<WordPressCategory[]> {
  await simulateDelay(200)
  return mockCategories
}

export async function mockFetchLinks(): Promise<WordPressLinkCategory[]> {
  await simulateDelay(300)
  return mockLinkCategories
}

/**
 * 取路径最后一段作为 slug 并统一解码。
 *
 * 传进来的 path 已经过 new URL()，中文会变成 %E6%89%98%E7%AE%A1… 的百分号编码，
 * 而 mock 数据里的 link 是原始中文。不解码就会把所有中文标题的文章判成 404。
 */
function slugOf(value: string): string {
  const last = value.split('/').filter(Boolean).pop() || ''
  try {
    return decodeURIComponent(last).toLowerCase()
  } catch {
    return last.toLowerCase()
  }
}

export async function mockResolveThemePath(path: string): Promise<ResolveResponse> {
  await simulateDelay(100)

  const slug = slugOf(path)

  if (!slug) {
    return { type: '404', message: 'Mock: 内容不存在' }
  }

  const allContent: WordPressPost[] = [...mockPosts, ...mockShuoshuo]
  for (const post of allContent) {
    const postSlug = slugOf(post.link)
    if (postSlug === slug) {
      return {
        type: (post.type as 'post' | 'shuoshuo') || 'post',
        restUrl: `mock://wp/v2/${post.type === 'shuoshuo' ? 'shuoshuo' : 'posts'}/${post.id}?_embed=1`,
        id: post.id,
      }
    }
  }

  return { type: '404', message: 'Mock: 内容不存在' }
}

export async function mockFetchContentByRestUrl(restUrl: string): Promise<WordPressPost | null> {
  await simulateDelay(200)

  const match = restUrl.match(/mock:\/\/wp\/v2\/(?:posts|shuoshuo)\/(\d+)/)
  if (!match) return null

  const id = Number(match[1])
  return [...mockPosts, ...mockShuoshuo].find((p) => p.id === id) || null
}

function simulateDelay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
