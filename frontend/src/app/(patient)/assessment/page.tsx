'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { useI18n } from '@/lib/i18n'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { ArrowLeft, FileText, Brain, ShieldAlert, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

type AssessmentType = 'PHQ9' | 'GAD7' | 'PCL5'

interface Question {
  id: string
  text: string
  text_en: string
}

// PHQ-9 - Depression screening (bilingual)
const PHQ9_QUESTIONS: Question[] = [
  {
    id: 'q1',
    text: '做事时提不起劲或没有兴趣',
    text_en: 'Little interest or pleasure in doing things',
  },
  { id: 'q2', text: '感到心情低落、沮丧或绝望', text_en: 'Feeling down, depressed, or hopeless' },
  {
    id: 'q3',
    text: '入睡困难、睡不安稳或睡眠过多',
    text_en: 'Trouble falling or staying asleep, or sleeping too much',
  },
  { id: 'q4', text: '感觉疲倦或没有活力', text_en: 'Feeling tired or having little energy' },
  { id: 'q5', text: '食欲不振或吃太多', text_en: 'Poor appetite or overeating' },
  {
    id: 'q6',
    text: '觉得自己很糟，或觉得自己很失败，或让自己或家人失望',
    text_en:
      'Feeling bad about yourself - or that you are a failure or have let yourself or your family down',
  },
  {
    id: 'q7',
    text: '难以集中精神，例如看报或看电视时',
    text_en: 'Trouble concentrating on things, such as reading or watching TV',
  },
  {
    id: 'q8',
    text: '动作或说话缓慢到别人可能注意到，或相反，烦躁或坐立不安',
    text_en:
      'Moving or speaking so slowly that other people could have noticed, or being so fidgety or restless',
  },
  {
    id: 'q9',
    text: '有想到死亡或伤害自己的念头',
    text_en: 'Thoughts that you would be better off dead, or of hurting yourself',
  },
]

// GAD-7 - Anxiety screening (bilingual)
const GAD7_QUESTIONS: Question[] = [
  { id: 'q1', text: '感到紧张、焦虑或急切', text_en: 'Feeling nervous, anxious, or on edge' },
  { id: 'q2', text: '不能停止或控制担忧', text_en: 'Not being able to stop or control worrying' },
  {
    id: 'q3',
    text: '对各种各样的事情担忧过多',
    text_en: 'Worrying too much about different things',
  },
  { id: 'q4', text: '很难放松下来', text_en: 'Trouble relaxing' },
  {
    id: 'q5',
    text: '烦躁不安，很难静坐',
    text_en: 'Being so restless that it is hard to sit still',
  },
  { id: 'q6', text: '变得容易烦恼或易怒', text_en: 'Becoming easily annoyed or irritable' },
  {
    id: 'q7',
    text: '感到好像有什么可怕的事情会发生',
    text_en: 'Feeling afraid, as if something awful might happen',
  },
]

// PCL-5 Simplified - PTSD screening for trauma survivors (bilingual)
const PCL5_QUESTIONS: Question[] = [
  {
    id: 'p1',
    text: '反复出现关于创伤事件的痛苦记忆、想法或画面',
    text_en: 'Repeated, disturbing memories, thoughts, or images of a stressful experience',
  },
  {
    id: 'p2',
    text: '反复做关于创伤事件的噩梦',
    text_en: 'Repeated, disturbing dreams of a stressful experience',
  },
  {
    id: 'p3',
    text: '避免与创伤事件相关的想法、感受或话题',
    text_en:
      'Avoiding thinking about or talking about a stressful experience or avoiding having feelings related to it',
  },
  {
    id: 'p4',
    text: '避免会让你想起创伤事件的活动或情境',
    text_en:
      'Avoiding activities or situations because they reminded you of a stressful experience',
  },
  {
    id: 'p5',
    text: '对自己、他人或世界有持续的负面信念',
    text_en: 'Having strong negative beliefs about yourself, other people, or the world',
  },
  {
    id: 'p6',
    text: '感到与他人疏远或隔离',
    text_en: 'Feeling distant or cut off from other people',
  },
  { id: 'p7', text: '过度警觉或警惕', text_en: 'Being "superalert" or watchful or on guard' },
  {
    id: 'p8',
    text: '感到易怒或有愤怒爆发',
    text_en: 'Feeling irritable or having angry outbursts',
  },
]

const SEVERITY_COLORS: Record<string, string> = {
  MINIMAL: 'text-success bg-success/10',
  MILD: 'text-warning bg-warning/10',
  MODERATE: 'text-orange-600 dark:text-orange-400 bg-orange-500/10',
  MODERATELY_SEVERE: 'text-destructive bg-destructive/10',
  SEVERE: 'text-destructive bg-destructive/20',
}

export default function AssessmentPage() {
  const [selectedType, setSelectedType] = useState<AssessmentType | null>(null)
  const [responses, setResponses] = useState<Record<string, number>>({})
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [result, setResult] = useState<{
    score: number
    severity: string
  } | null>(null)
  const [loading, setLoading] = useState(false)
  const { locale } = useI18n()
  const t = useTranslations('patient.assessment')
  const common = useTranslations('common')

  const questions =
    selectedType === 'PHQ9'
      ? PHQ9_QUESTIONS
      : selectedType === 'GAD7'
        ? GAD7_QUESTIONS
        : PCL5_QUESTIONS

  const getQuestionText = (q: Question) => (locale === 'en' ? q.text_en : q.text)

  // Get options based on assessment type
  const getOptions = () => {
    if (selectedType === 'PCL5') {
      return [
        { value: 0, label: t('pcl5Options.notAtAll') },
        { value: 1, label: t('pcl5Options.aLittleBit') },
        { value: 2, label: t('pcl5Options.moderately') },
        { value: 3, label: t('pcl5Options.quiteBit') },
        { value: 4, label: t('pcl5Options.extremely') },
      ]
    }
    return [
      { value: 0, label: t('options.notAtAll') },
      { value: 1, label: t('options.severalDays') },
      { value: 2, label: t('options.moreThanHalf') },
      { value: 3, label: t('options.nearlyEveryDay') },
    ]
  }

  const getSeverityLabel = (severity: string) => {
    const key = severity.toLowerCase().replace('_', '')
    const labelMap: Record<string, string> = {
      minimal: t('severity.minimal'),
      mild: t('severity.mild'),
      moderate: t('severity.moderate'),
      moderatelysevere: t('severity.moderatelySevere'),
      severe: t('severity.severe'),
    }
    return labelMap[key] || severity
  }

  const handleSelectOption = (questionId: string, value: number) => {
    setResponses((prev) => ({ ...prev, [questionId]: value }))

    // Auto-advance to next question
    if (currentQuestion < questions.length - 1) {
      setTimeout(() => {
        setCurrentQuestion((prev) => prev + 1)
      }, 300)
    }
  }

  const handleSubmit = async () => {
    if (!selectedType) return

    setLoading(true)
    try {
      const res = await api.submitAssessment(selectedType, responses)
      setResult({
        score: res.total_score,
        severity: res.severity,
      })
    } catch (error) {
      console.error('Assessment error:', error)
      alert(common('error'))
    } finally {
      setLoading(false)
    }
  }

  const resetAssessment = () => {
    setSelectedType(null)
    setResponses({})
    setCurrentQuestion(0)
    setResult(null)
  }

  // Type selection screen
  if (!selectedType) {
    return (
      <div className="h-full overflow-y-auto p-4 space-y-4 max-w-2xl md:mx-auto pb-24 md:pb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="bg-primary/10 p-2.5 rounded-xl">
            <FileText className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold">{t('title')}</h1>
            <p className="text-muted-foreground text-sm">{t('subtitle')}</p>
          </div>
        </div>

        {/* Privacy notice */}
        <div className="bg-info/10 rounded-xl p-4 border border-info/20">
          <p className="text-xs text-info">🔒 {t('privacyNotice')}</p>
        </div>

        <div className="space-y-3 mt-4">
          <button
            onClick={() => setSelectedType('PHQ9')}
            className="w-full bg-card border border-border rounded-xl p-5 text-left hover:border-primary/40 hover:shadow-md transition-all group"
          >
            <div className="flex items-start gap-4">
              <div className="bg-blue-500/10 p-2.5 rounded-xl shrink-0 group-hover:scale-105 transition-transform">
                <Brain className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">{t('phq9Title')}</h3>
                <p className="text-muted-foreground text-sm mt-1">{t('phq9Desc')}</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => setSelectedType('GAD7')}
            className="w-full bg-card border border-border rounded-xl p-5 text-left hover:border-primary/40 hover:shadow-md transition-all group"
          >
            <div className="flex items-start gap-4">
              <div className="bg-amber-500/10 p-2.5 rounded-xl shrink-0 group-hover:scale-105 transition-transform">
                <ShieldAlert className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">{t('gad7Title')}</h3>
                <p className="text-muted-foreground text-sm mt-1">{t('gad7Desc')}</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => setSelectedType('PCL5')}
            className="w-full bg-card border border-purple-500/30 rounded-xl p-5 text-left hover:border-purple-500/50 hover:shadow-md transition-all group"
          >
            <div className="flex items-start gap-4">
              <div className="bg-purple-500/10 p-2.5 rounded-xl shrink-0 group-hover:scale-105 transition-transform">
                <FileText className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h3 className="font-semibold text-purple-700 dark:text-purple-400">
                  {t('pcl5Title')}
                </h3>
                <p className="text-muted-foreground text-sm mt-1">{t('pcl5Desc')}</p>
                <p className="text-purple-600 dark:text-purple-400 text-xs mt-2">
                  {t('pcl5Recommend')}
                </p>
              </div>
            </div>
          </button>
        </div>

        <p className="text-xs text-muted-foreground mt-8">{t('disclaimer')}</p>
      </div>
    )
  }

  // Result screen
  if (result) {
    const severityColor = SEVERITY_COLORS[result.severity] || 'text-gray-600 bg-gray-100'

    const getAssessmentName = () => {
      if (selectedType === 'PHQ9') return t('phq9Score')
      if (selectedType === 'GAD7') return t('gad7Score')
      return t('pcl5Score')
    }

    const getMaxScore = () => {
      if (selectedType === 'PHQ9') return '27'
      if (selectedType === 'GAD7') return '21'
      return '32'
    }

    return (
      <div className="h-full overflow-y-auto p-4 space-y-6 max-w-2xl md:mx-auto">
        <h1 className="text-xl font-bold">{t('resultTitle')}</h1>

        <div className="bg-card border border-border rounded-xl p-6 shadow-sm text-center">
          <p className="text-muted-foreground mb-2">{getAssessmentName()}</p>
          <p className="text-5xl font-bold text-info">{result.score}</p>
          <p className="text-muted-foreground text-sm mt-1">{t('outOf', { max: getMaxScore() })}</p>
          <span
            className={`inline-block mt-4 px-4 py-1 rounded-full text-sm font-medium ${severityColor}`}
          >
            {getSeverityLabel(result.severity)}
          </span>
        </div>

        <div className="bg-info/10 rounded-xl p-4 border border-info/20">
          <p className="text-sm text-info">{t('resultNote')}</p>
        </div>

        {/* Crisis resources for high scores */}
        {(result.severity === 'SEVERE' || result.severity === 'MODERATELY_SEVERE') && (
          <div className="bg-destructive/10 rounded-xl p-4 border border-destructive/20">
            <p className="text-sm text-destructive font-medium mb-2">{t('supportResources')}</p>
            <p className="text-sm text-destructive whitespace-pre-line">{t('crisisResources')}</p>
          </div>
        )}

        <Button onClick={resetAssessment} className="w-full py-5">
          {common('done')}
        </Button>
      </div>
    )
  }

  // Questions screen
  const progress = Object.keys(responses).length / questions.length
  const allAnswered = Object.keys(responses).length === questions.length
  const currentQ = questions[currentQuestion]
  const currentOptions = getOptions()

  const getTimeFrameText = () => {
    if (selectedType === 'PCL5') {
      return t('timeframePCL')
    }
    return t('timeframePHQ')
  }

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4 max-w-2xl md:mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={resetAssessment}
          className="text-muted-foreground hover:text-foreground gap-1 -ml-2"
        >
          <ArrowLeft className="w-4 h-4" />
          {common('back')}
        </Button>
        <span className="text-sm font-medium text-muted-foreground">
          {currentQuestion + 1} / {questions.length}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      {/* Question */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
        <p className="text-sm text-muted-foreground mb-2">{getTimeFrameText()}</p>
        <p className="text-lg font-medium text-foreground">{getQuestionText(currentQ)}</p>
      </div>

      {/* Options */}
      <div className="space-y-2.5">
        {currentOptions.map((opt) => (
          <button
            key={opt.value}
            onClick={() => handleSelectOption(currentQ.id, opt.value)}
            className={cn(
              'w-full py-4 px-4 rounded-xl text-left transition-all text-sm',
              responses[currentQ.id] === opt.value
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'bg-card border border-border text-foreground hover:bg-muted hover:border-primary/30'
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Navigation */}
      <div className="flex gap-3 mt-6">
        {currentQuestion > 0 && (
          <Button
            variant="outline"
            onClick={() => setCurrentQuestion((prev) => prev - 1)}
            className="flex-1 py-5"
          >
            {t('previous')}
          </Button>
        )}
        {currentQuestion < questions.length - 1 ? (
          <Button
            onClick={() => setCurrentQuestion((prev) => prev + 1)}
            disabled={responses[currentQ.id] === undefined}
            className="flex-1 py-5"
          >
            {common('next')}
          </Button>
        ) : (
          <Button onClick={handleSubmit} disabled={!allAnswered || loading} className="flex-1 py-5">
            {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            {loading ? t('submitting') : common('submit')}
          </Button>
        )}
      </div>
    </div>
  )
}
