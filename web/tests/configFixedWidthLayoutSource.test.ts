import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const configSource = readFileSync(resolve('src/components/config/ConfigurationPanel.tsx'), 'utf8');

assert.equal(
  configSource.includes("const fieldClassName = 'flex min-w-0 items-center gap-2 xl:flex-none'"),
  true,
  'ConfigurationPanel fields should stop shrinking each other on wide viewports'
);

assert.equal(
  configSource.includes('flex w-full flex-wrap items-center gap-3 text-text-main xl:flex-nowrap xl:gap-2.5'),
  true,
  'ConfigurationPanel should keep a single fixed-width row on wide screens'
);

for (const widthClass of [
  'xl:w-[7rem]',
  'xl:w-[12rem]',
  'xl:w-[11.75rem]',
  'xl:w-[12.75rem]',
  'xl:w-[12.75rem] xl:flex-none',
]) {
  assert.equal(
    configSource.includes(widthClass),
    true,
    `ConfigurationPanel should reserve the fixed slot ${widthClass}`
  );
}

assert.equal(
  configSource.includes("const labelClassName = 'shrink-0 text-[0.875rem] font-medium text-text-secondary'"),
  true,
  'ConfigurationPanel should slightly reduce label size to fit the fixed-width layout'
);

assert.equal(
  configSource.includes(
    "const selectClassName = 'min-w-0 flex-1 [&_.ant-select-selector]:!px-2.5 [&_.ant-select-selector]:!text-[0.95rem]'"
  ),
  true,
  'ConfigurationPanel selects should tighten internal padding so values remain fully visible'
);

console.log('configFixedWidthLayoutSource.test.ts passed');
