export async function api<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  const data = await response.json()
  if (!response.ok)
    throw Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
  return data
}
