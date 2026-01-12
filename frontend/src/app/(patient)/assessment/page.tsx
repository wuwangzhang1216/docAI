'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useI18n } from '@/lib/i18n';
import { api } from '@/lib/api';

type AssessmentType = 'PHQ9' | 'GAD7' | 'PCL5';

interface Question {
  id: string;
  text: string;
  text_en: string;
}

// PHQ-9 - Depression screening (bilingual)
const PHQ9_QUESTIONS: Question[] = [
  { id: 'q1', text: '做事时提不起劲或没有兴趣', text_en: 'Little interest or pleasure in doing things' },
  { id: 'q2', text: '感到心情低落、沮丧或绝望', text_en: 'Feeling down, depressed, or hopeless' },
  { id: 'q3', text: '入睡困难、睡不安稳或睡眠过多', text_en: 'Trouble falling or staying asleep, or sleeping too much' },
  { id: 'q4', text: '感觉疲倦或没有活力', text_en: 'Feeling tired or having little energy' },
  { id: 'q5', text: '食欲不振或吃太多', text_en: 'Poor appetite or overeating' },
  { id: 'q6', text: '觉得自己很糟，或觉得自己很失败，或让自己或家人失望', text_en: 'Feeling bad about yourself - or that you are a failure or have let yourself or your family down' },
  { id: 'q7', text: '难以集中精神，例如看报或看电视时', text_en: 'Trouble concentrating on things, such as reading or watching TV' },
  { id: 'q8', text: '动作或说话缓慢到别人可能注意到，或相反，烦躁或坐立不安', text_en: 'Moving or speaking so slowly that other people could have noticed, or being so fidgety or restless' },
  { id: 'q9', text: '有想到死亡或伤害自己的念头', text_en: 'Thoughts that you would be better off dead, or of hurting yourself' },
];

// GAD-7 - Anxiety screening (bilingual)
const GAD7_QUESTIONS: Question[] = [
  { id: 'q1', text: '感到紧张、焦虑或急切', text_en: 'Feeling nervous, anxious, or on edge' },
  { id: 'q2', text: '不能停止或控制担忧', text_en: 'Not being able to stop or control worrying' },
  { id: 'q3', text: '对各种各样的事情担忧过多', text_en: 'Worrying too much about different things' },
  { id: 'q4', text: '很难放松下来', text_en: 'Trouble relaxing' },
  { id: 'q5', text: '烦躁不安，很难静坐', text_en: 'Being so restless that it is hard to sit still' },
  { id: 'q6', text: '变得容易烦恼或易怒', text_en: 'Becoming easily annoyed or irritable' },
  { id: 'q7', text: '感到好像有什么可怕的事情会发生', text_en: 'Feeling afraid, as if something awful might happen' },
];

// PCL-5 Simplified - PTSD screening for trauma survivors (bilingual)
const PCL5_QUESTIONS: Question[] = [
  { id: 'p1', text: '反复出现关于创伤事件的痛苦记忆、想法或画面', text_en: 'Repeated, disturbing memories, thoughts, or images of a stressful experience' },
  { id: 'p2', text: '反复做关于创伤事件的噩梦', text_en: 'Repeated, disturbing dreams of a stressful experience' },
  { id: 'p3', text: '避免与创伤事件相关的想法、感受或话题', text_en: 'Avoiding thinking about or talking about a stressful experience or avoiding having feelings related to it' },
  { id: 'p4', text: '避免会让你想起创伤事件的活动或情境', text_en: 'Avoiding activities or situations because they reminded you of a stressful experience' },
  { id: 'p5', text: '对自己、他人或世界有持续的负面信念', text_en: 'Having strong negative beliefs about yourself, other people, or the world' },
  { id: 'p6', text: '感到与他人疏远或隔离', text_en: 'Feeling distant or cut off from other people' },
  { id: 'p7', text: '过度警觉或警惕', text_en: 'Being "superalert" or watchful or on guard' },
  { id: 'p8', text: '感到易怒或有愤怒爆发', text_en: 'Feeling irritable or having angry outbursts' },
];

const SEVERITY_COLORS: Record<string, string> = {
  MINIMAL: 'text-green-600 dark:text-green-400 bg-green-500/10',
  MILD: 'text-yellow-600 dark:text-yellow-400 bg-yellow-500/10',
  MODERATE: 'text-orange-600 dark:text-orange-400 bg-orange-500/10',
  MODERATELY_SEVERE: 'text-red-500 dark:text-red-400 bg-red-500/10',
  SEVERE: 'text-red-700 dark:text-red-400 bg-red-500/20',
};

export default function AssessmentPage() {
  const [selectedType, setSelectedType] = useState<AssessmentType | null>(null);
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [result, setResult] = useState<{
    score: number;
    severity: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const { locale } = useI18n();
  const t = useTranslations('patient.assessment');
  const common = useTranslations('common');

  const questions =
    selectedType === 'PHQ9' ? PHQ9_QUESTIONS :
    selectedType === 'GAD7' ? GAD7_QUESTIONS :
    PCL5_QUESTIONS;

  const getQuestionText = (q: Question) => locale === 'en' ? q.text_en : q.text;

  // Get options based on assessment type
  const getOptions = () => {
    if (selectedType === 'PCL5') {
      return [
        { value: 0, label: t('pcl5Options.notAtAll') },
        { value: 1, label: t('pcl5Options.aLittleBit') },
        { value: 2, label: t('pcl5Options.moderately') },
        { value: 3, label: t('pcl5Options.quiteBit') },
        { value: 4, label: t('pcl5Options.extremely') },
      ];
    }
    return [
      { value: 0, label: t('options.notAtAll') },
      { value: 1, label: t('options.severalDays') },
      { value: 2, label: t('options.moreThanHalf') },
      { value: 3, label: t('options.nearlyEveryDay') },
    ];
  };

  const getSeverityLabel = (severity: string) => {
    const key = severity.toLowerCase().replace('_', '');
    const labelMap: Record<string, string> = {
      'minimal': t('severity.minimal'),
      'mild': t('severity.mild'),
      'moderate': t('severity.moderate'),
      'moderatelysevere': t('severity.moderatelySevere'),
      'severe': t('severity.severe'),
    };
    return labelMap[key] || severity;
  };

  const handleSelectOption = (questionId: string, value: number) => {
    setResponses((prev) => ({ ...prev, [questionId]: value }));

    // Auto-advance to next question
    if (currentQuestion < questions.length - 1) {
      setTimeout(() => {
        setCurrentQuestion((prev) => prev + 1);
      }, 300);
    }
  };

  const handleSubmit = async () => {
    if (!selectedType) return;

    setLoading(true);
    try {
      const res = await api.submitAssessment(selectedType, responses);
      setResult({
        score: res.total_score,
        severity: res.severity,
      });
    } catch (error) {
      console.error('Assessment error:', error);
      alert(common('error'));
    } finally {
      setLoading(false);
    }
  };

  const resetAssessment = () => {
    setSelectedType(null);
    setResponses({});
    setCurrentQuestion(0);
    setResult(null);
  };

  // Type selection screen
  if (!selectedType) {
    return (
      <div className="h-full overflow-y-auto p-4 space-y-4">
        <h1 className="text-xl font-bold">
          {t('title')}
        </h1>
        <p className="text-muted-foreground text-sm">
          {t('subtitle')}
        </p>

        {/* Privacy notice */}
        <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-500/20">
          <p className="text-xs text-blue-700 dark:text-blue-400">
            🔒 {t('privacyNotice')}
          </p>
        </div>

        <div className="space-y-4 mt-6">
          <button
            onClick={() => setSelectedType('PHQ9')}
            className="w-full bg-card border border-border rounded-xl p-6 shadow-sm text-left hover:shadow-md transition-shadow"
          >
            <h3 className="font-semibold text-lg text-foreground">
              {t('phq9Title')}
            </h3>
            <p className="text-muted-foreground text-sm mt-1">
              {t('phq9Desc')}
            </p>
          </button>

          <button
            onClick={() => setSelectedType('GAD7')}
            className="w-full bg-card border border-border rounded-xl p-6 shadow-sm text-left hover:shadow-md transition-shadow"
          >
            <h3 className="font-semibold text-lg text-foreground">
              {t('gad7Title')}
            </h3>
            <p className="text-muted-foreground text-sm mt-1">
              {t('gad7Desc')}
            </p>
          </button>

          <button
            onClick={() => setSelectedType('PCL5')}
            className="w-full bg-card border-2 border-purple-500/30 rounded-xl p-6 shadow-sm text-left hover:shadow-md transition-shadow"
          >
            <h3 className="font-semibold text-lg text-purple-700 dark:text-purple-400">
              {t('pcl5Title')}
            </h3>
            <p className="text-muted-foreground text-sm mt-1">
              {t('pcl5Desc')}
            </p>
            <p className="text-purple-600 dark:text-purple-400 text-xs mt-2">
              {t('pcl5Recommend')}
            </p>
          </button>
        </div>

        <p className="text-xs text-muted-foreground mt-8">
          {t('disclaimer')}
        </p>
      </div>
    );
  }

  // Result screen
  if (result) {
    const severityColor = SEVERITY_COLORS[result.severity] || 'text-gray-600 bg-gray-100';

    const getAssessmentName = () => {
      if (selectedType === 'PHQ9') return t('phq9Score');
      if (selectedType === 'GAD7') return t('gad7Score');
      return t('pcl5Score');
    };

    const getMaxScore = () => {
      if (selectedType === 'PHQ9') return '27';
      if (selectedType === 'GAD7') return '21';
      return '32';
    };

    return (
      <div className="h-full overflow-y-auto p-4 space-y-6">
        <h1 className="text-xl font-bold">
          {t('resultTitle')}
        </h1>

        <div className="bg-card border border-border rounded-xl p-6 shadow-sm text-center">
          <p className="text-muted-foreground mb-2">{getAssessmentName()}</p>
          <p className="text-5xl font-bold text-blue-600 dark:text-blue-400">{result.score}</p>
          <p className="text-muted-foreground text-sm mt-1">
            {t('outOf', { max: getMaxScore() })}
          </p>
          <span
            className={`inline-block mt-4 px-4 py-1 rounded-full text-sm font-medium ${severityColor}`}
          >
            {getSeverityLabel(result.severity)}
          </span>
        </div>

        <div className="bg-blue-500/10 rounded-xl p-4 border border-blue-500/20">
          <p className="text-sm text-blue-700 dark:text-blue-400">
            {t('resultNote')}
          </p>
        </div>

        {/* Crisis resources for high scores */}
        {(result.severity === 'SEVERE' || result.severity === 'MODERATELY_SEVERE') && (
          <div className="bg-red-500/10 rounded-xl p-4 border border-red-500/20">
            <p className="text-sm text-red-700 dark:text-red-400 font-medium mb-2">
              {t('supportResources')}
            </p>
            <p className="text-sm text-red-600 dark:text-red-400 whitespace-pre-line">
              {t('crisisResources')}
            </p>
          </div>
        )}

        <button
          onClick={resetAssessment}
          className="w-full bg-primary text-primary-foreground py-3 rounded-xl font-medium hover:bg-primary/90 transition-colors"
        >
          {common('done')}
        </button>
      </div>
    );
  }

  // Questions screen
  const progress = Object.keys(responses).length / questions.length;
  const allAnswered = Object.keys(responses).length === questions.length;
  const currentQ = questions[currentQuestion];
  const currentOptions = getOptions();

  const getTimeFrameText = () => {
    if (selectedType === 'PCL5') {
      return t('timeframePCL');
    }
    return t('timeframePHQ');
  };

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button onClick={resetAssessment} className="text-muted-foreground hover:text-foreground transition-colors">
          ← {common('back')}
        </button>
        <span className="text-sm text-muted-foreground">
          {currentQuestion + 1} / {questions.length}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="h-1 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-300"
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      {/* Question */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
        <p className="text-sm text-muted-foreground mb-2">{getTimeFrameText()}</p>
        <p className="text-lg font-medium text-foreground">
          {getQuestionText(currentQ)}
        </p>
      </div>

      {/* Options */}
      <div className="space-y-3">
        {currentOptions.map((opt) => (
          <button
            key={opt.value}
            onClick={() => handleSelectOption(currentQ.id, opt.value)}
            className={`w-full py-4 px-4 rounded-xl text-left transition-colors ${responses[currentQ.id] === opt.value
                ? 'bg-primary text-primary-foreground'
                : 'bg-card border border-border text-foreground hover:bg-muted'
              }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Navigation */}
      <div className="flex space-x-4 mt-6">
        {currentQuestion > 0 && (
          <button
            onClick={() => setCurrentQuestion((prev) => prev - 1)}
            className="flex-1 py-3 border border-border rounded-xl text-muted-foreground hover:bg-muted transition-colors"
          >
            {t('previous')}
          </button>
        )}
        {currentQuestion < questions.length - 1 ? (
          <button
            onClick={() => setCurrentQuestion((prev) => prev + 1)}
            disabled={responses[currentQ.id] === undefined}
            className="flex-1 py-3 bg-primary text-primary-foreground rounded-xl disabled:opacity-50 hover:bg-primary/90 transition-colors"
          >
            {common('next')}
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!allAnswered || loading}
            className="flex-1 py-3 bg-primary text-primary-foreground rounded-xl disabled:opacity-50 hover:bg-primary/90 transition-colors"
          >
            {loading ? t('submitting') : common('submit')}
          </button>
        )}
      </div>
    </div>
  );
}
