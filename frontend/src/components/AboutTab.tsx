import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { BookOpen, ExternalLink, Github, Globe, Rocket } from 'lucide-react'
import { getMeta } from '@/api/meta'

// Labels resolve at render time via `t(\`about.links.${id}\`)`; href/icon are code.
const LINKS: { id: string; href: string; icon: typeof Globe }[] = [
  { id: 'repo', href: 'https://github.com/VectifyAI/OpenKB', icon: Github },
  { id: 'pageindex', href: 'https://github.com/VectifyAI/PageIndex', icon: Github },
  { id: 'docs', href: 'https://docs.pageindex.ai', icon: BookOpen },
  { id: 'company', href: 'https://vectify.ai', icon: Globe },
]

// Ported-code credits — kept in sync with the release Acknowledgements (#86).
const THANKS: { name: string; href: string }[] = [
  { name: 'kalyan-fireweave', href: 'https://github.com/kalyan-fireweave' },
  { name: 'sebastianbraun25', href: 'https://github.com/sebastianbraun25' },
  { name: 'runmanfm-bit', href: 'https://github.com/runmanfm-bit' },
  { name: 'pes-innovation-lab', href: 'https://github.com/pes-innovation-lab' },
  { name: 'jidechao', href: 'https://github.com/jidechao' },
]

export default function AboutTab() {
  const { t } = useTranslation('settings')
  const [version, setVersion] = useState<string | null>(null)
  const [build, setBuild] = useState<string | null>(null)
  const [channel, setChannel] = useState<string | null>(null)
  useEffect(() => {
    let cancelled = false
    getMeta()
      .then((m) => {
        if (!cancelled) {
          setVersion(m.version)
          setBuild(m.build ?? null)
          setChannel(m.channel ?? null)
        }
      })
      .catch(() => { /* leave as null → shows — */ })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="mt-5 max-w-[560px] space-y-6 anim-fade-up">
      <div className="flex items-center gap-3">
        <span className="grid h-11 w-11 place-items-center rounded-2xl bg-accent-brand text-[18px] font-black text-white shrink-0">K</span>
        <div className="min-w-0">
          <div className="text-[16px] font-bold text-foreground">OpenKB</div>
          <div className="text-[12.5px] text-muted-foreground">
            Open LLM Knowledge Base · <span className="tabular-nums">v{version ?? '—'}</span> · Apache-2.0
          </div>
          {build && (
            <div className="text-[12.5px] text-muted-foreground tabular-nums">
              build: {build}
              {channel ? ` · ${channel}` : ''}
            </div>
          )}
        </div>
      </div>

      <p className="text-[13.5px] leading-relaxed text-muted-foreground">
        {t('about.blurb')}
      </p>
      <p className="text-[12.5px] text-muted-foreground">{t('about.byline')}</p>
      <p className="text-[12.5px] text-muted-foreground">
        fork: OpenKB Community Edition by sysadmins
      </p>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {LINKS.map((l) => (
          <a
            key={l.href}
            href={l.href}
            target="_blank"
            rel="noopener noreferrer"
            className="group inline-flex items-center gap-2 rounded-apple-md border border-[hsl(var(--glass-border))] glass-2 px-3 py-2 text-[13px] text-foreground transition hover:shadow-glass"
          >
            <l.icon className="w-4 h-4 shrink-0 text-muted-foreground transition-colors group-hover:text-accent-brand" />
            <span className="truncate">{t(`about.links.${l.id}`)}</span>
            <ExternalLink className="ml-auto w-3.5 h-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
          </a>
        ))}
      </div>

      <a
        href="https://github.com/VectifyAI/OpenKB/releases"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-accent-brand hover:underline"
      >
        <Rocket className="w-4 h-4" /> {t('about.latestRelease')}
      </a>

      <a
        href="https://github.com/mike-011/OpenKB"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-accent-brand hover:underline"
      >
        <Github className="w-4 h-4" /> Forked repo — mike-011/OpenKB
      </a>

      <div className="text-[12.5px] text-muted-foreground">
        Thanks to:{' '}
        {THANKS.map((a, i) => (
          <span key={a.href}>
            {i > 0 && ', '}
            <a
              href={a.href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent-brand hover:underline"
            >
              {a.name}
            </a>
          </span>
        ))}
      </div>
    </div>
  )
}
