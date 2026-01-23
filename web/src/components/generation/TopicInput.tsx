/**
 * Topic Input Component for PPT Generation
 */

import { Form, Input, Select, InputNumber, Collapse, Switch, Space, Typography } from 'antd';
import { useLLMConfigs } from '../../hooks/useLLMConfigs';
import { useEmbeddingConfigs } from '../../hooks/useEmbeddingConfigs';
import { useFiles } from '../../hooks/useFiles';
import { useTemplates } from '../../hooks/useTemplates';
import { Tone, Verbosity } from '../../api/types/slidegen.types';
import type { Template } from '../../api/types/slidegen.types';
import { GENERATION_DEFAULTS } from '../../utils/constants';

const { TextArea } = Input;
const { Panel } = Collapse;
const { Text } = Typography;

interface TemplateSelectorProps {
  value?: string;
  onChange?: (value: string) => void;
  templates: Template[];
}

const TemplateSelector: React.FC<TemplateSelectorProps> = ({ value, onChange, templates }) => {
  return (
    <div className="grid grid-cols-2 gap-4">
      {templates.map((t) => {
        const isSelected = value === t.id;
        return (
          <div
            key={t.id}
            className={`
              cursor-pointer rounded-lg border-2 p-4 transition-all hover:shadow-md
              ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-blue-300'}
            `}
            onClick={() => onChange?.(t.id)}
          >
            <div className="flex items-center gap-3">
              {t.thumbnail ? (
                <div className="h-12 w-12 overflow-hidden rounded-lg border border-gray-200">
                  <img
                    src={t.thumbnail}
                    alt={t.name}
                    className="h-full w-full object-cover"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      e.currentTarget.nextElementSibling?.classList.remove('hidden');
                    }}
                  />
                  <div
                    className={`
                      hidden flex h-full w-full items-center justify-center
                      ${t.id.includes('purple') ? 'bg-purple-100 text-purple-600' : 'bg-gray-100 text-gray-600'}
                    `}
                  >
                    <div className={`h-6 w-6 rounded-full ${t.id.includes('purple') ? 'bg-purple-500' : 'bg-gray-500'}`} />
                  </div>
                </div>
              ) : (
                <div
                  className={`
                    flex h-12 w-12 items-center justify-center rounded-lg
                    ${t.id.includes('purple') ? 'bg-purple-100 text-purple-600' : 'bg-gray-100 text-gray-600'}
                  `}
                >
                  <div className={`h-6 w-6 rounded-full ${t.id.includes('purple') ? 'bg-purple-500' : 'bg-gray-500'}`} />
                </div>
              )}
              <div>
                <div className="font-medium">{t.name}</div>
                <div className="text-xs text-gray-500">
                  {t.id === 'general' ? 'Clean & Professional' : 'Modern & Vibrant'}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

interface TopicInputProps {
  sessionId?: string;
}

export const TopicInput: React.FC<TopicInputProps> = ({ sessionId }) => {
  const { data: llmConfigsData } = useLLMConfigs();
  const { data: embeddingConfigsData } = useEmbeddingConfigs();
  const { data: filesData } = useFiles({ session_id: sessionId });
  const { data: templates } = useTemplates();

  const llmConfigs = llmConfigsData?.data || [];
  const embeddingConfigs = embeddingConfigsData?.data || [];
  const files = filesData?.data || [];

  // Get default configs
  const defaultLLM = llmConfigs.find((c) => c.is_default);
  const defaultEmbedding = embeddingConfigs.find((c) => c.is_default);

  return (
    <>
      <Form.Item
        name="content"
        label="Topic / Content"
        rules={[{ required: true, message: 'Please enter a topic or content' }]}
      >
        <TextArea
          rows={4}
          placeholder="Enter the topic or content for your presentation. For example: 'AI and Machine Learning Overview' or paste your content here..."
        />
      </Form.Item>

      <Form.Item
        name="llm_config_id"
        label="LLM Configuration"
        rules={[{ required: true, message: 'Please select an LLM configuration' }]}
        initialValue={defaultLLM?.id}
      >
        <Select placeholder="Select LLM configuration">
          {llmConfigs
            .filter((c) => c.is_active)
            .map((config) => (
              <Select.Option key={config.id} value={config.id}>
                {config.name} ({config.provider} - {config.model_id})
                {config.is_default && ' ⭐'}
              </Select.Option>
            ))}
        </Select>
      </Form.Item>

      <Form.Item
        name="embedding_config_id"
        label="Embedding Configuration (Optional)"
        tooltip="Used for knowledge base search"
        initialValue={defaultEmbedding?.id}
      >
        <Select placeholder="Select embedding configuration" allowClear>
          {embeddingConfigs
            .filter((c) => c.is_active)
            .map((config) => (
              <Select.Option key={config.id} value={config.id}>
                {config.name} ({config.provider} - {config.model_id})
                {config.is_default && ' ⭐'}
              </Select.Option>
            ))}
        </Select>
      </Form.Item>

      {files.length > 0 && (
        <Form.Item
          name="files"
          label="Knowledge Base Files (Optional)"
          tooltip="Select files to use as reference material"
        >
          <Select
            mode="multiple"
            placeholder="Select files to include"
            showSearch
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
            options={files
              .filter((f) => f.parsed)
              .map((file) => ({
                label: file.filename,
                value: file.id,
              }))}
          />
        </Form.Item>
      )}

      <Form.Item
        label="Presentation Template"
        required
        style={{ marginBottom: 0 }}
      >
        <Form.Item
          name="template"
          initialValue={GENERATION_DEFAULTS.TEMPLATE}
          rules={[{ required: true, message: 'Please select a template' }]}
          noStyle
        >
          <TemplateSelector templates={templates || []} />
        </Form.Item>
      </Form.Item>

      <Collapse ghost>
        <Panel header="Advanced Options" key="advanced">
          <Form.Item
            name="instructions"
            label="Additional Instructions (Optional)"
          >
            <TextArea
              rows={3}
              placeholder="Any specific instructions or requirements for the presentation..."
            />
          </Form.Item>

          <Space direction="vertical" className="w-full" size="large">
            <Form.Item name="tone" label="Tone">
              <Select>
                <Select.Option value={Tone.DEFAULT}>Default</Select.Option>
                <Select.Option value={Tone.CASUAL}>Casual</Select.Option>
                <Select.Option value={Tone.PROFESSIONAL}>
                  Professional
                </Select.Option>
                <Select.Option value={Tone.FUNNY}>Funny</Select.Option>
                <Select.Option value={Tone.EDUCATIONAL}>
                  Educational
                </Select.Option>
                <Select.Option value={Tone.SALES_PITCH}>
                  Sales Pitch
                </Select.Option>
              </Select>
            </Form.Item>

            <Form.Item name="verbosity" label="Verbosity">
              <Select>
                <Select.Option value={Verbosity.CONCISE}>Concise</Select.Option>
                <Select.Option value={Verbosity.STANDARD}>
                  Standard
                </Select.Option>
                <Select.Option value={Verbosity.TEXT_HEAVY}>
                  Text Heavy
                </Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="n_slides"
              label="Number of Slides"
              tooltip="Approximate number of content slides (excluding title)"
            >
              <InputNumber min={3} max={50} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item name="language" label="Language">
              <Input placeholder="English, Chinese, Spanish, etc." />
            </Form.Item>

            <Form.Item
              name="web_search"
              label="Enable Web Search"
              valuePropName="checked"
              tooltip="Allow the AI to search the web for additional information"
            >
              <Switch />
            </Form.Item>

            <Form.Item
              name="include_title_slide"
              label="Include Title Slide"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item
              name="include_table_of_contents"
              label="Include Table of Contents"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          </Space>

          <div className="mt-4 p-3 bg-gray-100 rounded">
            <Text type="secondary" className="text-xs">
              These settings control how the AI generates your presentation content.
              Adjust them based on your needs.
            </Text>
          </div>
        </Panel>
      </Collapse>
    </>
  );
};
