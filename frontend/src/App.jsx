import { useCallback, useEffect, useState } from 'react'
import { NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { api, auth, setUnauthorizedHandler } from './api'
import { LangContext, STRINGS, useT } from './i18n'
import CaseEditor from './pages/CaseEditor'
import CaseList from './pages/CaseList'
import Login from './pages/Login'
import Settings from './pages/Settings'
import TemplateAdmin from './pages/TemplateAdmin'

export default function App() {
  const [lang, setLang] = useState(() => localStorage.getItem('lang') || 'mr')
  const [toast, setToast] = useState(null)
  const [health, setHealth] = useState(null)
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(true)

  const [mrFont, setMrFont] = useState(
    () => localStorage.getItem('mrFont.v2') || "'Noto Sans Devanagari'")

  useEffect(() => { localStorage.setItem('lang', lang) }, [lang])
  useEffect(() => {
    localStorage.setItem('mrFont.v2', mrFont)
    document.documentElement.style.setProperty(
      '--mr', [mrFont, "'Noto Sans Devanagari'", "'Nirmala UI'", "'Mangal'", 'sans-serif']
        .filter((face, i, all) => all.indexOf(face) === i).join(', '))
  }, [mrFont])

  // Resume a session, or sign straight in when the API is running in local
  // desktop mode (start.bat on the clerk's own machine).
  useEffect(() => {
    let cancelled = false
    const resume = async () => {
      try {
        const status = await api.health()
        if (!cancelled) setHealth(status)
        if (auth.token || status.auth_required === false) {
          const me = await api.me()
          if (!cancelled) setUser(me)
        }
      } catch {
        auth.token = ''
      } finally {
        if (!cancelled) setChecking(false)
      }
    }
    resume()
    return () => { cancelled = true }
  }, [])

  useEffect(() => { setUnauthorizedHandler(() => setUser(null)) }, [])

  const notify = useCallback((message, kind = 'ok') => {
    setToast({ message, kind })
    window.setTimeout(() => setToast(null), kind === 'err' ? 7000 : 3000)
  }, [])

  if (checking) return null

  if (!user) {
    return (
      <LangContext.Provider value={{ lang, setLang }}>
        <Login lang={lang} setLang={setLang} onSignedIn={setUser} />
      </LangContext.Provider>
    )
  }

  return (
    <LangContext.Provider value={{ lang, setLang }}>
      <div className="app">
        <Header lang={lang} setLang={setLang} health={health} user={user}
          setUser={setUser} />
        <main>
          <Routes>
            <Route path="/" element={<CaseList notify={notify} />} />
            <Route path="/cases/:id"
              element={<CaseEditor notify={notify} health={health} />} />
            <Route path="/templates"
              element={<TemplateAdmin notify={notify} user={user} />} />
            <Route path="/settings"
              element={<Settings notify={notify} user={user}
                mrFont={mrFont} setMrFont={setMrFont} />} />
            <Route path="/account"
              element={<Account user={user} setUser={setUser} notify={notify} />} />
          </Routes>
        </main>
        {toast && <div className={'toast ' + toast.kind}>{toast.message}</div>}
      </div>
    </LangContext.Provider>
  )
}

function Header({ lang, setLang, health, user, setUser }) {
  const t = useT()
  const index = lang === 'mr' ? 0 : 1

  const signOut = async () => {
    try { await api.logout() } catch { /* the token is dropped either way */ }
    auth.token = ''
    setUser(null)
  }

  return (
    <header className="topbar">
      <h1>
        {STRINGS.appName[index]}
        <small>{STRINGS.appSub[index === 0 ? 1 : 0]}</small>
      </h1>
      <nav>
        <NavLink to="/" end>{t('cases')}</NavLink>
        <NavLink to="/templates">{t('templates')}</NavLink>
        <NavLink to="/settings">{t('settings')}</NavLink>
        <NavLink to="/account">
          {t('account')}
          {user.using_default_password && <span className="dot" title={t('defaultPasswordWarning')} />}
        </NavLink>
        {health && !health.pdf_available && (
          <span className="badge err" title={t('pdfEngine')}>{t('pdfUnavailable')}</span>
        )}
        <div className="lang-toggle">
          <button className={lang === 'mr' ? 'on' : ''}
            onClick={() => setLang('mr')}>मराठी</button>
          <button className={lang === 'en' ? 'on' : ''}
            onClick={() => setLang('en')}>EN</button>
        </div>
        {health?.auth_required !== false && (
          <button className="signout" onClick={signOut} title={user.username}>
            {t('signOut')}
          </button>
        )}
      </nav>
    </header>
  )
}

function Account({ user, setUser, notify }) {
  const t = useT()
  const navigate = useNavigate()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [repeat, setRepeat] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (next !== repeat) { notify(t('passwordMismatch'), 'err'); return }
    setBusy(true)
    try {
      await api.changePassword(current, next)
      const me = await api.me()
      setUser(me)
      setCurrent(''); setNext(''); setRepeat('')
      notify(t('passwordChanged'), 'ok')
      navigate('/')
    } catch (err) {
      notify(err.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ maxWidth: 460 }}>
      {user.using_default_password && (
        <div className="notice warn">{t('defaultPasswordWarning')}</div>
      )}
      <div className="card">
        <h2>{t('account')}<span className="sub">{user.username} · {user.role}</span></h2>
        <form onSubmit={submit}>
          <label className="field" style={{ marginBottom: 10 }}>
            <span className="lbl"><span className="primary">{t('currentPassword')}</span></span>
            <input type="password" value={current} autoComplete="current-password"
              onChange={(e) => setCurrent(e.target.value)} required />
          </label>
          <label className="field" style={{ marginBottom: 10 }}>
            <span className="lbl"><span className="primary">{t('newPassword')}</span></span>
            <input type="password" value={next} minLength={8} autoComplete="new-password"
              onChange={(e) => setNext(e.target.value)} required />
          </label>
          <label className="field" style={{ marginBottom: 14 }}>
            <span className="lbl"><span className="primary">{t('confirmPassword')}</span></span>
            <input type="password" value={repeat} minLength={8} autoComplete="new-password"
              onChange={(e) => setRepeat(e.target.value)} required />
          </label>
          <button className="primary" type="submit" disabled={busy}>
            {busy ? t('saving') : t('changePassword')}
          </button>
        </form>
      </div>
    </div>
  )
}
