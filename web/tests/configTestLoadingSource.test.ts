import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const llmListSource = readFileSync(
  resolve('web/src/components/config/LLMConfigList.tsx'),
  'utf8'
);
const embeddingListSource = readFileSync(
  resolve('web/src/components/config/EmbeddingConfigList.tsx'),
  'utf8'
);
const llmPageSource = readFileSync(
  resolve('web/src/pages/config/LLMConfigPage.tsx'),
  'utf8'
);
const embeddingPageSource = readFileSync(
  resolve('web/src/pages/config/EmbeddingConfigPage.tsx'),
  'utf8'
);

for (const [name, source] of [
  ['LLMConfigList', llmListSource],
  ['EmbeddingConfigList', embeddingListSource],
] as const) {
  assert.match(
    source,
    /testingConfigId\?: string \| null/,
    `${name} should accept the active testing config id`
  );

  assert.match(
    source,
    /loading=\{isTesting\}/,
    `${name} should show a loading spinner on the active test button`
  );

  assert.match(
    source,
    /isTesting \? 'Testing\.\.\.' : 'Test'/,
    `${name} should switch the button copy while a test is running`
  );

  assert.match(
    source,
    /Waiting for model response\.\.\./,
    `${name} should render an in-card waiting hint while a test is running`
  );
}

assert.match(
  llmPageSource,
  /const \[testingConfigId, setTestingConfigId\] = useState<string \| null>\(null\);/,
  'LLMConfigPage should track which config is being tested'
);

assert.match(
  llmPageSource,
  /setTestingConfigId\(config\.id\)/,
  'LLMConfigPage should set the active testing config before starting the request'
);

assert.match(
  llmPageSource,
  /finally \{\s*setTestingConfigId\(null\);?\s*\}/,
  'LLMConfigPage should always clear the active testing config after the request finishes'
);

assert.match(
  embeddingPageSource,
  /const \[testingConfigId, setTestingConfigId\] = useState<string \| null>\(null\);/,
  'EmbeddingConfigPage should track which config is being tested'
);

assert.match(
  embeddingPageSource,
  /setTestingConfigId\(config\.id\)/,
  'EmbeddingConfigPage should set the active testing config before starting the request'
);

assert.match(
  embeddingPageSource,
  /finally \{\s*setTestingConfigId\(null\);?\s*\}/,
  'EmbeddingConfigPage should always clear the active testing config after the request finishes'
);

console.log('configTestLoadingSource.test.ts passed');
