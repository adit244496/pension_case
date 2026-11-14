const BASE = '/api'
const TOKEN_KEY = 'pension.token'

export const auth = {
  get token() {
    try { return localStorage.getItem(TOKEN_KEY) || '' } catch { return '' }
  },
  set token(value) {
    try {
      if (value) localStorage.setItem(TOKEN_KEY, value)
      else localStorage.removeItem(TOKEN_KEY)
    } catch { /* private browsing */ }
  },
}

/** Absolute URL for a path from the helpers below, for a hand-rolled fetch. */
export const apiUrl = (path) => BASE + path

/** Raised on 401 so the app can drop back to the sign-in screen. */
export class Unauthorized extends Error {}

let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json'
  if (auth.token) headers.Authorization = `Bearer ${auth.token}`

  const res = await fetch(BASE + path, { credentials: 'include', ...options, headers })

  if (res.status === 401) {
    auth.token = ''
    onUnauthorized()
    throw new Unauthorized('Your session has ended. Please sign in again.')
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch { /* non-JSON error body */ }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (res.status === 204) return null
  return res.json()
}

const json = (body) => ({ body: JSON.stringify(body) })

/**
 * Files are fetched with the bearer token and handed to the browser as a blob,
 * because a plain link in a new tab cannot carry the Authorization header.
 */
async function fetchBlob(path) {
  const headers = auth.token ? { Authorization: `Bearer ${auth.token}` } : {}
  const res = await fetch(BASE + path, { credentials: 'include', headers })
  if (res.status === 401) { auth.token = ''; onUnauthorized(); throw new Unauthorized('Sign in again') }
  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail || detail } catch { /* binary body */ }
    throw new Error(detail)
  }
  return res.blob()
}

/** Open a document in a new tab (PDFs render inline in the browser viewer). */
export async function openInTab(path) {
  const blob = await fetchBlob(path)
  const url = URL.createObjectURL(blob)
  const win = window.open(url, '_blank')
  if (!win) { URL.revokeObjectURL(url); throw new Error('Allow pop-ups to open the preview') }
  // Give the tab time to load before releasing the object URL.
  window.setTimeout(() => URL.revokeObjectURL(url), 60000)
}

/**
 * Save a document to disk under a chosen name.
 *
 * The anchor and its object URL are torn down on a timer, not straight after
 * the click: removing either synchronously cancels a blob download in
 * Chromium before it has been written.
 */
export async function download(path, filename) {
  const blob = await fetchBlob(path)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename || 'download'
  link.rel = 'noopener'
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  window.setTimeout(() => {
    link.remove()
    URL.revokeObjectURL(url)
  }, 60000)
}

export const api = {
  health: () => request('/health'),

  // -- authentication ------------------------------------------------------
  login: (username, password) =>
    request('/auth/login', { method: 'POST', ...json({ username, password }) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  changePassword: (current_password, new_password) =>
    request('/auth/password', { method: 'POST', ...json({ current_password, new_password }) }),
  listUsers: () => request('/auth/users'),
  createUser: (payload) => request('/auth/users', { method: 'POST', ...json(payload) }),
  deleteUser: (id) => request(`/auth/users/${id}`, { method: 'DELETE' }),

  // -- cases ---------------------------------------------------------------
  schema: () => request('/cases/schema'),
  listCases: (q = '') => request(`/cases?q=${encodeURIComponent(q)}`),
  getCase: (id) => request(`/cases/${id}`),
  createCase: (payload) => request('/cases', { method: 'POST', ...json(payload) }),
  updateCase: (id, payload) => request(`/cases/${id}`, { method: 'PUT', ...json(payload) }),
  deleteCase: (id) => request(`/cases/${id}`, { method: 'DELETE' }),
  generate: (id, payload = { codes: null, make_pdf: true }) =>
    request(`/cases/${id}/generate`, { method: 'POST', ...json(payload) }),
  documents: (id) => request(`/cases/${id}/documents`),
  // A short value that changes when the documents do, so the Documents tab can
  // watch for a save in Word without asking for every form's row each time.
  documentsTick: (id) => request(`/cases/${id}/documents/tick`),

  documentPath: (caseId, docId, fmt, inline = false) =>
    `/cases/${caseId}/documents/${docId}/download?fmt=${fmt}&inline=${inline}`,
  bundlePath: (caseId, kind, inline = false) =>
    `/cases/${caseId}/bundle?kind=${kind}&inline=${inline}`,

  setFormPreferences: (id, forms) =>
    request(`/cases/${id}/forms`, { method: 'PUT', ...json({ forms }) }),
  resetFormPreferences: (id) => request(`/cases/${id}/forms/reset`, { method: 'POST' }),
  documentContent: (caseId, docId) =>
    request(`/cases/${caseId}/documents/${docId}/content`),
  saveDocumentContent: (caseId, docId, edits) =>
    request(`/cases/${caseId}/documents/${docId}/content`,
      { method: 'PUT', ...json({ edits }) }),
  openInWord: (caseId, docId) =>
    request(`/cases/${caseId}/documents/${docId}/open-in-word`, { method: 'POST' }),
  adoptEdits: (caseId, docId) =>
    request(`/cases/${caseId}/documents/${docId}/adopt`, { method: 'POST' }),
  resetDocument: (caseId, docId) =>
    request(`/cases/${caseId}/documents/${docId}/reset`, { method: 'POST' }),

  transliterate: (text, direction = 'auto') =>
    request('/transliterate', { method: 'POST', ...json({ text, direction }) }),
  settings: () => request('/settings'),
  saveSetting: (key, value) =>
    request(`/settings/${key}`, { method: 'PUT', ...json({ value }) }),
  resetSetting: (key) => request(`/settings/${key}/reset`, { method: 'POST' }),

  // -- templates -----------------------------------------------------------
  listTemplates: (includeArchived = false) =>
    request(`/templates?include_archived=${includeArchived}`),
  getTemplate: (id) => request(`/templates/${id}`),
  patchTemplate: (id, payload) =>
    request(`/templates/${id}`, { method: 'PATCH', ...json(payload) }),
  saveBlocks: (id, blocks) =>
    request(`/templates/${id}/blocks`, { method: 'PUT', ...json({ blocks }) }),
  resetBlocks: (id) => request(`/templates/${id}/blocks/reset`, { method: 'POST' }),
  rebuildTemplate: (id) => request(`/templates/${id}/rebuild`, { method: 'POST' }),
  reorderTemplates: (ids) =>
    request('/templates/reorder', { method: 'POST', ...json({ ids }) }),
  deleteTemplate: (id) => request(`/templates/${id}`, { method: 'DELETE' }),
  restoreTemplate: (id) => request(`/templates/${id}/restore`, { method: 'POST' }),
  placeholders: () => request('/templates/placeholders'),
  createTemplate: ({ title_en, title_mr, language, file }) => {
    const form = new FormData()
    form.append('title_en', title_en)
    form.append('title_mr', title_mr || '')
    form.append('language', language || 'en')
    if (file) form.append('file', file)
    return request('/templates', { method: 'POST', body: form })
  },
  uploadTemplate: (id, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/templates/${id}/docx`, { method: 'POST', body: form })
  },
  backups: (id) => request(`/templates/${id}/backups`),
  restoreBackup: (id, name) =>
    request(`/templates/${id}/restore-backup/${encodeURIComponent(name)}`, { method: 'POST' }),

  templateDocxPath: (id, resolved = false) => `/templates/${id}/docx?resolved=${resolved}`,
  previewPath: (id, caseId, fmt = 'pdf') =>
    `/templates/${id}/preview?fmt=${fmt}${caseId ? `&case_id=${caseId}` : ''}`,
}
