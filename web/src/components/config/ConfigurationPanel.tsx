import { Switch, Select, InputNumber } from 'antd';
import { useGenerationStore } from '../../store/generationStore';
import { Tone, Verbosity } from '../../api/types/slidegen.types';
import { cn } from '../../utils/classnames';

const LANGUAGE_OPTIONS = [
  { value: 'English', label: 'English' },
  { value: 'Chinese', label: 'Chinese' },
  { value: 'Japanese', label: 'Japanese' },
  { value: 'Korean', label: 'Korean' },
  { value: 'Spanish', label: 'Español' },
  { value: 'French', label: 'Français' },
  { value: 'German', label: 'Deutsch' },
];

const TONE_OPTIONS = [
  { value: Tone.DEFAULT, label: 'Default' },
  { value: Tone.PROFESSIONAL, label: 'Professional' },
  { value: Tone.CASUAL, label: 'Casual' },
  { value: Tone.EDUCATIONAL, label: 'Educational' },
  { value: Tone.FUNNY, label: 'Funny' },
  { value: Tone.SALES_PITCH, label: 'Sales pitch' },
];

const VERBOSITY_OPTIONS = [
  { value: Verbosity.CONCISE, label: 'Concise' },
  { value: Verbosity.STANDARD, label: 'Standard' },
  { value: Verbosity.TEXT_HEAVY, label: 'Text heavy' },
];

const fieldClassName = 'flex min-w-0 items-center gap-2';
const labelClassName = 'shrink-0 text-[0.95rem] font-medium text-text-secondary';
const selectClassName = 'w-full min-w-0';

export const ConfigurationPanel = () => {
  const {
    slideCount,
    language,
    tone,
    verbosity,
    webSearchEnabled,
    setSlideCount,
    setLanguage,
    setTone,
    setVerbosity,
    setWebSearchEnabled,
  } = useGenerationStore();

  return (
    <div className="flex w-full flex-wrap items-center gap-3 text-text-main xl:grid xl:grid-cols-[7.5rem_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_11rem] xl:gap-3">
      <div className={cn(fieldClassName, 'xl:w-[7.5rem]')}>
        <label htmlFor="generation-slide-count" className={labelClassName}>
          Pages
        </label>
        <InputNumber
          id="generation-slide-count"
          aria-label="Slide count"
          className="!w-[4.75rem]"
          value={slideCount}
          onChange={(value) => setSlideCount(value || 8)}
          min={1}
          max={50}
          controls={false}
        />
      </div>

      <div className={fieldClassName}>
        <label htmlFor="generation-language" className={labelClassName}>
          Language
        </label>
        <Select
          id="generation-language"
          aria-label="Presentation language"
          className={selectClassName}
          value={language}
          onChange={setLanguage}
          options={LANGUAGE_OPTIONS}
        />
      </div>

      <div className={fieldClassName}>
        <label htmlFor="generation-tone" className={labelClassName}>
          Tone
        </label>
        <Select
          id="generation-tone"
          aria-label="Presentation tone"
          className={selectClassName}
          value={tone}
          onChange={setTone}
          options={TONE_OPTIONS}
        />
      </div>

      <div className={fieldClassName}>
        <label htmlFor="generation-verbosity" className={labelClassName}>
          Text Volume
        </label>
        <Select
          id="generation-verbosity"
          aria-label="Content density"
          className={selectClassName}
          value={verbosity}
          onChange={setVerbosity}
          options={VERBOSITY_OPTIONS}
        />
      </div>

      <div className="flex h-11 min-w-0 items-center justify-between gap-2 rounded-2xl border border-border/70 bg-surface-50 px-3.5">
        <label htmlFor="generation-web-search" className={labelClassName}>
          Web research
        </label>
        <Switch
          id="generation-web-search"
          aria-label="Web research"
          checked={webSearchEnabled}
          onChange={setWebSearchEnabled}
        />
      </div>
    </div>
  );
};
