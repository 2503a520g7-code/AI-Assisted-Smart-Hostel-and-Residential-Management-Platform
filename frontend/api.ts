import { 
  LostAndFoundItem, 
  ItemStats, 
  CreateItemInput, 
  UpdateItemInput, 
  ItemStatus 
} from '../types/item';

const STORAGE_API_KEY = 'CAMPUS_LOST_FOUND_API_URL';

/**
 * Custom Error for when AWS API Gateway is not configured
 */
export class AwsNotConfiguredError extends Error {
  constructor(message = 'AWS API Gateway URL is not configured. Please configure VITE_API_BASE_URL in your environment or Settings.') {
    super(message);
    this.name = 'AwsNotConfiguredError';
  }
}

export class ApiError extends Error {
  public statusCode: number;
  public details?: unknown;

  constructor(message: string, statusCode: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

/**
 * Get active API Base URL.
 * Priority:
 * 1. Runtime override configured in the Settings UI (stored in localStorage)
 * 2. Vite environment variable: import.meta.env.VITE_API_BASE_URL
 */
export function getApiBaseUrl(): string {
  const customUrl = localStorage.getItem(STORAGE_API_KEY);
  if (customUrl && customUrl.trim()) {
    return customUrl.trim().replace(/\/+$/, '');
  }
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim()) {
    return envUrl.trim().replace(/\/+$/, '');
  }
  return '';
}

/**
 * Save custom API Base URL from Settings UI
 */
export function setCustomApiBaseUrl(url: string | null): void {
  if (!url || !url.trim()) {
    localStorage.removeItem(STORAGE_API_KEY);
  } else {
    localStorage.setItem(STORAGE_API_KEY, url.trim().replace(/\/+$/, ''));
  }
}

/**
 * Check if an AWS API Gateway URL is configured
 */
export function isAwsConfigured(): boolean {
  return Boolean(getApiBaseUrl());
}

/**
 * Execute standard fetch request with error handling & JSON formatting
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();

  if (!baseUrl) {
    throw new AwsNotConfiguredError();
  }

  const url = `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const contentType = response.headers.get('content-type') || '';
    let responseData: any = null;

    if (contentType.includes('application/json')) {
      responseData = await response.json();
    } else {
      const text = await response.text();
      responseData = { message: text };
    }

    if (!response.ok) {
      const errorMsg =
        responseData?.error ||
        responseData?.message ||
        `HTTP ${response.status}: ${response.statusText}`;
      throw new ApiError(errorMsg, response.status, responseData);
    }

    // If backend wrapped response in { success: true, data: ... }
    if (responseData && typeof responseData === 'object' && 'data' in responseData) {
      return responseData.data as T;
    }

    return responseData as T;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new ApiError('Request timed out after 15 seconds. Check AWS API Gateway and Lambda configuration.', 408);
    }
    if (error instanceof ApiError || error instanceof AwsNotConfiguredError) {
      throw error;
    }
    // Network or CORS failure
    throw new ApiError(
      error.message || 'Network error: Failed to reach AWS API Gateway. Check CORS and endpoint URL.',
      0
    );
  }
}

/**
 * Test connectivity to the specified or active API Gateway endpoint
 */
export async function testConnection(overrideUrl?: string): Promise<{
  ok: boolean;
  status: number;
  latencyMs: number;
  message: string;
  data?: any;
}> {
  const targetUrl = (overrideUrl || getApiBaseUrl()).trim().replace(/\/+$/, '');
  if (!targetUrl) {
    return {
      ok: false,
      status: 0,
      latencyMs: 0,
      message: 'No AWS API Gateway URL configured.',
    };
  }

  const startTime = performance.now();
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    const res = await fetch(`${targetUrl}/stats`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
    });
    clearTimeout(timeout);
    const latencyMs = Math.round(performance.now() - startTime);

    if (res.ok) {
      const json = await res.json();
      return {
        ok: true,
        status: res.status,
        latencyMs,
        message: 'Successfully connected to AWS API Gateway & DynamoDB!',
        data: json,
      };
    } else {
      return {
        ok: false,
        status: res.status,
        latencyMs,
        message: `Endpoint reachable but returned HTTP ${res.status}: ${res.statusText}`,
      };
    }
  } catch (err: any) {
    const latencyMs = Math.round(performance.now() - startTime);
    return {
      ok: false,
      status: 0,
      latencyMs,
      message: err.name === 'AbortError' 
        ? 'Connection timed out after 10s' 
        : `Connection failed: ${err.message || 'CORS error or unreachable server'}`,
    };
  }
}

/**
 * 1. GET /items - Fetch all lost & found items
 */
export async function getItems(params?: {
  status?: string;
  category?: string;
  search?: string;
}): Promise<LostAndFoundItem[]> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status', params.status);
  if (params?.category) query.append('category', params.category);
  if (params?.search) query.append('search', params.search);

  const qs = query.toString();
  const endpoint = qs ? `/items?${qs}` : '/items';
  return apiRequest<LostAndFoundItem[]>(endpoint, { method: 'GET' });
}

/**
 * 2. GET /items/{itemId} - Fetch single item details
 */
export async function getItemById(itemId: string): Promise<LostAndFoundItem> {
  return apiRequest<LostAndFoundItem>(`/items/${encodeURIComponent(itemId)}`, {
    method: 'GET',
  });
}

/**
 * 3. POST /items - Register new item
 */
export async function createItem(item: CreateItemInput): Promise<LostAndFoundItem> {
  return apiRequest<LostAndFoundItem>('/items', {
    method: 'POST',
    body: JSON.stringify(item),
  });
}

/**
 * 4. PUT /items/{itemId} - Update full item
 */
export async function updateItem(
  itemId: string,
  item: UpdateItemInput
): Promise<LostAndFoundItem> {
  return apiRequest<LostAndFoundItem>(`/items/${encodeURIComponent(itemId)}`, {
    method: 'PUT',
    body: JSON.stringify(item),
  });
}

/**
 * 5. PATCH /items/{itemId}/status - Smart Box check-in / check-out / mark status
 */
export async function updateItemStatus(
  itemId: string,
  status: ItemStatus,
  extra?: { checkInTime?: string; checkOutTime?: string }
): Promise<LostAndFoundItem> {
  return apiRequest<LostAndFoundItem>(`/items/${encodeURIComponent(itemId)}/status`, {
    method: 'PATCH',
    body: JSON.stringify({
      status,
      ...extra,
    }),
  });
}

/**
 * 6. DELETE /items/{itemId} - Remove item
 */
export async function deleteItem(
  itemId: string
): Promise<{ success: boolean; itemId: string }> {
  return apiRequest<{ success: boolean; itemId: string }>(
    `/items/${encodeURIComponent(itemId)}`,
    {
      method: 'DELETE',
    }
  );
}

/**
 * 7. GET /stats - Fetch real dashboard statistics aggregated from DynamoDB
 */
export async function getStats(): Promise<ItemStats> {
  return apiRequest<ItemStats>('/stats', {
    method: 'GET',
  });
}
