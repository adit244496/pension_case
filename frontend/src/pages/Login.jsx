import { useEffect, useState } from 'react'
import { api, auth } from '../api'
import { STRINGS } from '../i18n'

export default function Login({ lang, setLang, onSignedIn }) {
  const i = lang === 'mr' ? 0 : 1
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [health, setHealth] = useState(null)

  useEffect(() => { api.health().then(setHealth).catch(() => setHealth(null)) }, [])

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const res = await api.login(username.trim(), password)
      auth.token = res.token
      onSignedIn(res.user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <h1 className="mr">{STRINGS.appName[0]}</h1>
        <p className="muted small">{STRINGS.appSub[1]}</p>

        <div className="lang-toggle inline">
          <button type="button" className={lang === 'mr' ? 'on' : ''}
            onClick={() => setLang('mr')}>मराठी</button>
          <button type="button" className={lang === 'en' ? 'on' : ''}
            onClick={() => setLang('en')}>English</button>
        </div>

        {error && <div className="notice err">{error}</div>}

        <label className="field">
          <span className="lbl">
            <span className="primary mr">{i === 0 ? 'वापरकर्ता नाव' : 'Username'}</span>
            <span className="secondary">{i === 0 ? 'Username' : 'वापरकर्ता नाव'}</span>
          </span>
          <input value={username} onChange={(e) => setUsername(e.target.value)}
            autoFocus autoComplete="username" required />
        </label>

        <label className="field">
          <span className="lbl">
            <span className="primary mr">{i === 0 ? 'पासवर्ड' : 'Password'}</span>
            <span className="secondary">{i === 0 ? 'Password' : 'पासवर्ड'}</span>
          </span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password" required />
        </label>

        <button className="primary" type="submit" disabled={busy} style={{ width: '100%' }}>
          {busy
            ? (i === 0 ? 'प्रवेश होत आहे…' : 'Signing in…')
            : (i === 0 ? 'प्रवेश करा' : 'Sign in')}
        </button>

        {health && !health.pdf_available && (
          <p className="notice warn small" style={{ marginTop: 14 }}>
            {i === 0
              ? 'PDF तयार करण्यासाठी या संगणकावर Word किंवा LibreOffice आवश्यक आहे.'
              : 'PDF export needs Word or LibreOffice installed on this machine.'}
          </p>
        )}
      </form>
    </div>
  )
}
