import { Button, Switch, Select, InputNumber, Upload, message } from 'antd';
import type { UploadProps } from 'antd';
import { 
  MenuFoldOutlined,
  CloudUploadOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileTextOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { useGenerationStore } from '../../store/generationStore';
import { useTemplates } from '../../hooks/useTemplates';
import { useFiles, useUploadFile } from '../../hooks/useFiles';
import { useChatStore } from '../../store/chatStore';
import { Tone, Verbosity } from '../../api/types/slidegen.types';
import type { FileMetadataPublic } from '../../api/types/file.types';
import { cn } from '../../utils/classnames';

// Language options
const LANGUAGE_OPTIONS = [
  { value: 'English', label: 'English' },
  { value: 'Chinese', label: '中文' },
  { value: 'Japanese', label: '日本語' },
  { value: 'Korean', label: '한국어' },
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
  { value: Tone.SALES_PITCH, label: 'Sales Pitch' },
];

const VERBOSITY_OPTIONS = [
  { value: Verbosity.CONCISE, label: 'Concise' },
  { value: Verbosity.STANDARD, label: 'Standard' },
  { value: Verbosity.TEXT_HEAVY, label: 'Text Heavy' },
];

interface ConfigurationPanelProps {
  onCollapse?: () => void;
}

export const ConfigurationPanel = ({ onCollapse }: ConfigurationPanelProps) => {
  const { currentSessionId } = useChatStore();
  
  // Generation store
  const {
    slideCount,
    language,
    template,
    tone,
    verbosity,
    exportFormat,
    webSearchEnabled,
    setSlideCount,
    setLanguage,
    setTemplate,
    setTone,
    setVerbosity,
    setExportFormat,
    setWebSearchEnabled,
    addUploadedFile,
    removeUploadedFile,
  } = useGenerationStore();

  // Templates hook
  const { data: templates, isLoading: templatesLoading } = useTemplates();
  
  // Files hooks
  const { data: filesData } = useFiles(currentSessionId ? { session_id: currentSessionId } : undefined);
  const uploadFileMutation = useUploadFile();

  // File upload handler
  const handleUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options;
    if (!currentSessionId) {
      message.error('No active session');
      onError?.(new Error('No active session'));
      return;
    }
    try {
      const result = await uploadFileMutation.mutateAsync({
        file: file as File, 
        sessionId: currentSessionId 
      });
      if (result?.id) {
        addUploadedFile(result.id);
        onSuccess?.(result);
      }
    } catch (error: unknown) {
      const err = error as { detail?: string };
      onError?.(new Error(err?.detail || 'Upload failed'));
    }
  };

  const handleRemoveFile = (fileId: string) => {
    removeUploadedFile(fileId);
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return <FilePdfOutlined className="text-red-400" />;
      case 'doc':
      case 'docx':
        return <FileWordOutlined className="text-blue-400" />;
      default:
        return <FileTextOutlined className="text-gray-400" />;
    }
  };

  const uploadedFiles = filesData?.data || [];

  return (
    <div className="h-full flex flex-col bg-surface-50/40 backdrop-blur-xl border-l border-white/5 text-text-main">
      {/* Header */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between">
        <h2 className="text-sm font-bold m-0 tracking-wide text-text-main">CONFIGURATION</h2>
        <Button 
          type="text" 
          icon={<MenuFoldOutlined className="text-text-secondary" />} 
          aria-label="Collapse configuration panel"
          className="hover:bg-white/5 text-text-secondary hover:text-text-main"
          onClick={onCollapse}
        />
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-8">
        
        {/* Generation Parameters */}
        <section className="space-y-4">
          <h3 className="text-[10px] font-bold text-primary-400 uppercase tracking-widest mb-3 flex items-center gap-2">
            <span className="w-1 h-1 rounded-full bg-primary-400"></span>
            Generation Parameters
          </h3>
          
          <div className="space-y-2">
            <label className="text-xs text-text-secondary block font-medium">Pages</label>
            <InputNumber 
              className="dark-input w-full !bg-surface-100/50 !border-white/10 !text-text-main" 
              value={slideCount}
              onChange={(value) => setSlideCount(value || 8)}
              min={1}
              max={50}
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs text-text-secondary block font-medium">Language</label>
            <Select
              className="w-full !bg-transparent"
              popupClassName="!bg-surface-100/95 !backdrop-blur-xl !border !border-white/10"
              value={language}
              onChange={setLanguage}
              options={LANGUAGE_OPTIONS}
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs text-text-secondary block font-medium">Template</label>
            <Select
              className="w-full !bg-transparent"
              popupClassName="!bg-surface-100/95 !backdrop-blur-xl !border !border-white/10"
              value={template}
              onChange={setTemplate}
              loading={templatesLoading}
              options={templates?.map(t => ({ value: t.id, label: t.name })) || [
                { value: 'general', label: 'General' },
                { value: 'professional', label: 'Professional' },
                { value: 'creative', label: 'Creative' },
              ]}
            />
          </div>
        </section>

        {/* Style & Content */}
        <section className="space-y-4">
          <h3 className="text-[10px] font-bold text-primary-400 uppercase tracking-widest mb-3 flex items-center gap-2">
            <span className="w-1 h-1 rounded-full bg-primary-400"></span>
            Style & Content
          </h3>
          
          <div className="space-y-2">
            <label className="text-xs text-text-secondary block font-medium">Tone</label>
            <Select
              className="w-full !bg-transparent"
              popupClassName="!bg-surface-100/95 !backdrop-blur-xl !border !border-white/10"
              value={tone}
              onChange={setTone}
              options={TONE_OPTIONS}
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs text-text-secondary block font-medium">Verbosity</label>
            <Select
              className="w-full !bg-transparent"
              popupClassName="!bg-surface-100/95 !backdrop-blur-xl !border !border-white/10"
              value={verbosity}
              onChange={setVerbosity}
              options={VERBOSITY_OPTIONS}
            />
          </div>
        </section>

        {/* Output & References */}
        <section className="space-y-4">
          <h3 className="text-[10px] font-bold text-primary-400 uppercase tracking-widest mb-3 flex items-center gap-2">
            <span className="w-1 h-1 rounded-full bg-primary-400"></span>
            Output & References
          </h3>
          
          <div className="space-y-3">
            <label className="text-xs text-text-secondary block font-medium">Export As</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer group">
                <input 
                  type="radio" 
                  name="export" 
                  className="hidden" 
                  checked={exportFormat === 'pptx'}
                  onChange={() => setExportFormat('pptx')}
                />
                <div className={cn("w-4 h-4 rounded-full border flex items-center justify-center transition-all", exportFormat === 'pptx' ? "border-primary-500 bg-primary-500/20" : "border-text-secondary group-hover:border-primary-400")}>
                  {exportFormat === 'pptx' && <div className="w-2 h-2 rounded-full bg-primary-500 shadow-glow" />}
                </div>
                <span className={cn("text-sm transition-colors", exportFormat === 'pptx' ? "text-primary-400 font-medium" : "text-text-secondary group-hover:text-text-main")}>PPTX</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer group">
                <input 
                  type="radio" 
                  name="export" 
                  className="hidden" 
                  checked={exportFormat === 'pdf'}
                  onChange={() => setExportFormat('pdf')}
                />
                <div className={cn("w-4 h-4 rounded-full border flex items-center justify-center transition-all", exportFormat === 'pdf' ? "border-primary-500 bg-primary-500/20" : "border-text-secondary group-hover:border-primary-400")}>
                  {exportFormat === 'pdf' && <div className="w-2 h-2 rounded-full bg-primary-500 shadow-glow" />}
                </div>
                <span className={cn("text-sm transition-colors", exportFormat === 'pdf' ? "text-primary-400 font-medium" : "text-text-secondary group-hover:text-text-main")}>PDF</span>
              </label>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
               <label className="text-xs text-text-secondary block font-medium">Web Search</label>
               <Switch 
                 size="small" 
                 checked={webSearchEnabled}
                 onChange={setWebSearchEnabled}
                 className="!bg-surface-300 hover:!bg-primary-500" 
               />
            </div>
          </div>

          <div className="space-y-2 mt-4">
             <label className="text-xs text-text-secondary block font-medium">Reference Files</label>
             <Upload
               customRequest={handleUpload}
               showUploadList={false}
               multiple
               accept=".pdf,.doc,.docx,.txt,.md"
             >
               <div className="border border-dashed border-white/10 rounded-lg p-6 flex flex-col items-center justify-center text-center hover:border-primary-500/50 hover:bg-primary-500/5 hover:shadow-glow/10 transition-all duration-300 cursor-pointer group w-full">
                  <CloudUploadOutlined className="text-2xl text-text-secondary mb-2 group-hover:text-primary-400 transition-colors" />
                  <span className="text-xs text-text-secondary group-hover:text-primary-300 transition-colors">
                    {uploadFileMutation.isPending ? 'Uploading...' : 'Click to upload or drag & drop'}
                  </span>
               </div>
             </Upload>

             {/* Uploaded files list */}
             {uploadedFiles.length > 0 && (
               <div className="space-y-2 mt-2">
                 {uploadedFiles.map((file: FileMetadataPublic) => (
                   <div 
                     key={file.id} 
                     className="bg-surface-100/50 rounded border border-white/5 p-2 flex items-center gap-2 group hover:border-white/20 transition-all"
                   >
                     {getFileIcon(file.filename)}
                     <span className="text-xs flex-1 truncate">{file.filename}</span>
                     <button 
                       onClick={() => handleRemoveFile(file.id)}
                       className="text-text-secondary hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                     >
                       <DeleteOutlined />
                     </button>
                   </div>
                 ))}
               </div>
             )}
          </div>
        </section>

      </div>
    </div>
  );
};
