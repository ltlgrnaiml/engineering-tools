/**
 * Profile Editor Component
 *
 * Per SPEC-0007: Profile File Management
 * Per ADR-0028: DevTools Page Architecture
 *
 * Features:
 * - JSON editor with syntax highlighting
 * - Schema validation against profile contract
 * - Live preview of profile changes
 * - Save/Load profiles from file system
 * - Profile version display and management
 * - Error highlighting for invalid JSON
 * - Profile template selection
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import {
  Save,
  Upload,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  FileJson,
  Copy,
  Trash2,
  FileText,
} from 'lucide-react';

/**
 * Profile metadata.
 */
export interface ProfileMetadata {
  /** Profile ID */
  id: string;
  /** Profile name */
  name: string;
  /** Profile version */
  version: string;
  /** Creation timestamp */
  createdAt: string;
  /** Last modified timestamp */
  updatedAt: string;
  /** Profile description */
  description?: string;
}

/**
 * Validation error.
 */
export interface ValidationError {
  /** Error path in JSON */
  path: string;
  /** Error message */
  message: string;
  /** Line number (if applicable) */
  line?: number;
}

/**
 * Profile template.
 */
export interface ProfileTemplate {
  /** Template ID */
  id: string;
  /** Template name */
  name: string;
  /** Template description */
  description: string;
  /** Template content (JSON string) */
  content: string;
}

/**
 * Props for ProfileEditor.
 */
export interface ProfileEditorProps {
  /** Initial profile content (JSON string) */
  initialContent?: string;
  /** Profile metadata */
  metadata?: ProfileMetadata;
  /** Available templates */
  templates?: ProfileTemplate[];
  /** Callback when content changes */
  onChange?: (content: string) => void;
  /** Callback when save is requested */
  onSave?: (content: string, metadata: ProfileMetadata) => Promise<void>;
  /** Callback to load a profile */
  onLoad?: () => Promise<{ content: string; metadata: ProfileMetadata }>;
  /** Callback to validate content */
  onValidate?: (content: string) => Promise<ValidationError[]>;
  /** Read-only mode */
  readOnly?: boolean;
}

/**
 * Simple JSON syntax highlighter.
 */
function highlightJSON(json: string): string {
  return json
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(
      /("(\\u[\da-fA-F]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
      (match) => {
        let cls = 'text-emerald-600'; // number
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'text-blue-600'; // key
          } else {
            cls = 'text-amber-600'; // string
          }
        } else if (/true|false/.test(match)) {
          cls = 'text-purple-600'; // boolean
        } else if (/null/.test(match)) {
          cls = 'text-slate-400'; // null
        }
        return `<span class="${cls}">${match}</span>`;
      }
    );
}

/**
 * Format JSON with indentation.
 */
function formatJSON(json: string): string {
  try {
    const parsed = JSON.parse(json);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return json;
  }
}

/**
 * Profile Editor Component
 *
 * A JSON editor for DAT extraction profiles with syntax highlighting,
 * validation, and template support.
 *
 * @example
 * ```tsx
 * <ProfileEditor
 *   initialContent={profileJson}
 *   templates={availableTemplates}
 *   onSave={handleSave}
 *   onValidate={validateProfile}
 * />
 * ```
 */
export function ProfileEditor({
  initialContent = '{}',
  metadata,
  templates = [],
  onChange,
  onSave,
  onLoad,
  onValidate,
  readOnly = false,
}: ProfileEditorProps) {
  const [content, setContent] = useState(initialContent);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  // Parse JSON for preview
  const parsedContent = useMemo(() => {
    try {
      return JSON.parse(content);
    } catch {
      return null;
    }
  }, [content]);

  // Check if content is valid JSON
  const isValidJSON = parsedContent !== null;

  // Validate content
  const validateContent = useCallback(async () => {
    if (!onValidate) return;

    setIsValidating(true);
    try {
      const validationErrors = await onValidate(content);
      setErrors(validationErrors);
    } catch (err) {
      setErrors([
        {
          path: '',
          message: err instanceof Error ? err.message : 'Validation failed',
        },
      ]);
    } finally {
      setIsValidating(false);
    }
  }, [content, onValidate]);

  // Handle content change
  const handleContentChange = useCallback(
    (newContent: string) => {
      setContent(newContent);
      setIsDirty(true);
      onChange?.(newContent);
    },
    [onChange]
  );

  // Handle format
  const handleFormat = useCallback(() => {
    const formatted = formatJSON(content);
    handleContentChange(formatted);
  }, [content, handleContentChange]);

  // Handle save
  const handleSave = useCallback(async () => {
    if (!onSave || !metadata) return;

    setIsSaving(true);
    try {
      await onSave(content, {
        ...metadata,
        updatedAt: new Date().toISOString(),
      });
      setIsDirty(false);
      setSavedMessage('Profile saved successfully');
      setTimeout(() => setSavedMessage(null), 3000);
    } catch (err) {
      setErrors([
        {
          path: '',
          message: err instanceof Error ? err.message : 'Save failed',
        },
      ]);
    } finally {
      setIsSaving(false);
    }
  }, [content, metadata, onSave]);

  // Handle load
  const handleLoad = useCallback(async () => {
    if (!onLoad) return;

    try {
      const { content: loadedContent } = await onLoad();
      handleContentChange(loadedContent);
      setIsDirty(false);
    } catch (err) {
      setErrors([
        {
          path: '',
          message: err instanceof Error ? err.message : 'Load failed',
        },
      ]);
    }
  }, [onLoad, handleContentChange]);

  // Handle template selection
  const handleSelectTemplate = useCallback(
    (template: ProfileTemplate) => {
      handleContentChange(template.content);
      setShowTemplates(false);
    },
    [handleContentChange]
  );

  // Handle copy
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(content);
  }, [content]);

  // Handle clear
  const handleClear = useCallback(() => {
    handleContentChange('{}');
  }, [handleContentChange]);

  // Validate on content change (debounced)
  useEffect(() => {
    if (!onValidate || !isValidJSON) return;

    const timer = setTimeout(() => {
      validateContent();
    }, 500);

    return () => clearTimeout(timer);
  }, [content, isValidJSON, onValidate, validateContent]);

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-slate-200">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-slate-200 bg-slate-50">
        <div className="flex items-center gap-2">
          <FileJson className="w-5 h-5 text-slate-500" />
          <span className="font-medium text-slate-700">
            {metadata?.name || 'Profile Editor'}
          </span>
          {metadata?.version && (
            <span className="text-xs text-slate-400 bg-slate-200 px-2 py-0.5 rounded">
              v{metadata.version}
            </span>
          )}
          {isDirty && (
            <span className="text-xs text-amber-500">• Unsaved changes</span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {/* Template selector */}
          {templates.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setShowTemplates(!showTemplates)}
                className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors"
                title="Templates"
              >
                <FileText className="w-4 h-4" />
              </button>
              {showTemplates && (
                <div className="absolute right-0 top-full mt-1 w-64 bg-white border border-slate-200 rounded-lg shadow-lg z-10">
                  <div className="p-2 border-b border-slate-100">
                    <span className="text-xs font-medium text-slate-500">
                      Templates
                    </span>
                  </div>
                  {templates.map((template) => (
                    <button
                      key={template.id}
                      onClick={() => handleSelectTemplate(template)}
                      className="w-full text-left px-3 py-2 hover:bg-slate-50 transition-colors"
                    >
                      <div className="font-medium text-sm text-slate-700">
                        {template.name}
                      </div>
                      <div className="text-xs text-slate-500 truncate">
                        {template.description}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          <button
            onClick={handleFormat}
            disabled={readOnly || !isValidJSON}
            className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors disabled:opacity-50"
            title="Format JSON"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={handleCopy}
            className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors"
            title="Copy to clipboard"
          >
            <Copy className="w-4 h-4" />
          </button>

          <button
            onClick={handleClear}
            disabled={readOnly}
            className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors disabled:opacity-50"
            title="Clear"
          >
            <Trash2 className="w-4 h-4" />
          </button>

          <div className="w-px h-5 bg-slate-200 mx-1" />

          {onLoad && (
            <button
              onClick={handleLoad}
              disabled={readOnly}
              className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors disabled:opacity-50"
              title="Load profile"
            >
              <Upload className="w-4 h-4" />
            </button>
          )}

          {onSave && (
            <button
              onClick={handleSave}
              disabled={readOnly || !isValidJSON || isSaving}
              className="p-2 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded transition-colors disabled:opacity-50"
              title="Save profile"
            >
              {isSaving ? (
                <span className="w-4 h-4 border-2 border-slate-300 border-t-emerald-500 rounded-full animate-spin inline-block" />
              ) : (
                <Save className="w-4 h-4" />
              )}
            </button>
          )}

          <button
            onClick={() => {
              const blob = new Blob([content], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `${metadata?.name || 'profile'}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded transition-colors"
            title="Download JSON"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 flex min-h-0">
        {/* Code editor */}
        <div className="flex-1 relative">
          <textarea
            value={content}
            onChange={(e) => handleContentChange(e.target.value)}
            disabled={readOnly}
            className={`
              w-full h-full p-4 font-mono text-sm resize-none
              bg-slate-900 text-slate-100
              focus:outline-none focus:ring-2 focus:ring-inset focus:ring-emerald-500
              disabled:opacity-75 disabled:cursor-not-allowed
            `}
            spellCheck={false}
            placeholder="Enter JSON content..."
          />

          {/* Line numbers overlay (simplified) */}
          <div
            className="absolute left-0 top-0 bottom-0 w-10 bg-slate-800 border-r border-slate-700 pointer-events-none"
            aria-hidden
          >
            <div className="p-4 font-mono text-xs text-slate-500 leading-5">
              {content.split('\n').map((_, i) => (
                <div key={i}>{i + 1}</div>
              ))}
            </div>
          </div>
        </div>

        {/* Preview panel */}
        <div className="w-80 border-l border-slate-200 bg-slate-50 overflow-auto">
          <div className="p-3 border-b border-slate-200">
            <span className="text-xs font-medium text-slate-500">
              Preview
            </span>
          </div>
          <div className="p-3">
            {isValidJSON ? (
              <pre
                className="text-xs font-mono whitespace-pre-wrap break-words"
                dangerouslySetInnerHTML={{
                  __html: highlightJSON(JSON.stringify(parsedContent, null, 2)),
                }}
              />
            ) : (
              <div className="text-red-500 text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Invalid JSON
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-slate-200 bg-slate-50 text-xs">
        <div className="flex items-center gap-4">
          {/* Validation status */}
          {isValidating ? (
            <span className="text-slate-500 flex items-center gap-1">
              <RefreshCw className="w-3 h-3 animate-spin" />
              Validating...
            </span>
          ) : errors.length > 0 ? (
            <span className="text-red-500 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.length} error{errors.length > 1 ? 's' : ''}
            </span>
          ) : isValidJSON ? (
            <span className="text-emerald-500 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              Valid
            </span>
          ) : (
            <span className="text-red-500 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              Invalid JSON syntax
            </span>
          )}

          {/* Character count */}
          <span className="text-slate-400">
            {content.length.toLocaleString()} characters
          </span>

          {/* Line count */}
          <span className="text-slate-400">
            {content.split('\n').length} lines
          </span>
        </div>

        <div>
          {savedMessage && (
            <span className="text-emerald-500 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              {savedMessage}
            </span>
          )}
        </div>
      </div>

      {/* Error panel */}
      {errors.length > 0 && (
        <div className="border-t border-red-200 bg-red-50 max-h-32 overflow-auto">
          <div className="p-2">
            {errors.map((error, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-red-700 py-1">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  {error.path && (
                    <span className="font-mono text-red-500">{error.path}: </span>
                  )}
                  {error.message}
                  {error.line && (
                    <span className="text-red-400 ml-2">(line {error.line})</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ProfileEditor;
