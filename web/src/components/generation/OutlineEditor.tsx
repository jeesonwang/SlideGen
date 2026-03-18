import React, { useState, useEffect, useRef } from 'react';
import { Input, Button, Tooltip } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { cn } from '../../utils/classnames';

interface OutlineItem {
  id: string;
  title: string;
  points: string[];
}

interface OutlineEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export const OutlineEditor: React.FC<OutlineEditorProps> = ({ value, onChange }) => {
  const [items, setItems] = useState<OutlineItem[]>([]);
  const [presentationTitle, setPresentationTitle] = useState<string>('');
  const isInternalUpdate = useRef(false);

  // Parse markdown to outline items on init or when value changes externally
  useEffect(() => {
    if (value && !isInternalUpdate.current) {
      const { title, items: parsedItems } = parseMarkdown(value);
      setPresentationTitle(title);
      setItems(parsedItems);
    }
    isInternalUpdate.current = false;
  }, [value]);

  const parseMarkdown = (md: string): { title: string, items: OutlineItem[] } => {
    const lines = md.split('\n');
    const newItems: OutlineItem[] = [];
    let currentItem: OutlineItem | null = null;
    let title = '';
    let idCounter = 0;

    const generateId = () => `outline-item-${Date.now()}-${idCounter++}`;

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('# ')) {
        title = trimmed.replace(/^#\s+/, '');
      } else if (trimmed.startsWith('## ')) {
        if (currentItem) {
          newItems.push(currentItem);
        }
        currentItem = {
            id: generateId(),
            title: trimmed.replace(/^##\s+/, ''),
            points: []
        };
      } else if (trimmed.startsWith('### ')) {
        // User request: Slide content are Level 3 headers
        if (currentItem) {
          currentItem.points.push(trimmed.replace(/^###\s+/, ''));
        }
      } else if ((trimmed.startsWith('- ') || trimmed.startsWith('* ')) && currentItem) {
        // Fallback: still support standard bullets if mixed or old format
        currentItem.points.push(trimmed.replace(/^[-*]\s+/, ''));
      }
    });
    if (currentItem) {
      newItems.push(currentItem);
    }
    return { title, items: newItems };
  };

  const generateMarkdown = (currentItems: OutlineItem[], pTitle: string): string => {
    let md = '';
    if (pTitle) {
      md += `# ${pTitle}\n\n`;
    }
    md += currentItems.map(item => {
      // User request: Slide title = ##, Content = ###
      const pointsMd = item.points.map(p => `### ${p}`).join('\n');
      return `## ${item.title}\n${pointsMd}`;
    }).join('\n\n');
    return md;
  };

  const updateMarkdown = (newItems: OutlineItem[], pTitle: string) => {
    const md = generateMarkdown(newItems, pTitle);
    isInternalUpdate.current = true;
    onChange(md);
  };

  const handleTitleChange = (id: string, newTitle: string) => {
    const newItems = items.map(item => 
      item.id === id ? { ...item, title: newTitle } : item
    );
    setItems(newItems);
    updateMarkdown(newItems, presentationTitle);
  };

  const handlePointChange = (id: string, pointIndex: number, newPoint: string) => {
    const newItems = items.map(item => {
      if (item.id === id) {
        const newPoints = [...item.points];
        newPoints[pointIndex] = newPoint;
        return { ...item, points: newPoints };
      }
      return item;
    });
    setItems(newItems);
    updateMarkdown(newItems, presentationTitle);
  };
  
  const handleAddPoint = (id: string) => {
      const newItems = items.map(item => 
        item.id === id ? { ...item, points: [...item.points, 'New Point'] } : item
      );
      setItems(newItems);
      updateMarkdown(newItems, presentationTitle);
  }

  const handleDeletePoint = (id: string, pointIndex: number) => {
    const newItems = items.map(item => {
        if (item.id === id) {
            const newPoints = item.points.filter((_, idx) => idx !== pointIndex);
            return { ...item, points: newPoints };
        }
        return item;
    });
    setItems(newItems);
    updateMarkdown(newItems, presentationTitle);
  }

  const handleDeleteCard = (id: string) => {
    const newItems = items.filter(item => item.id !== id);
    setItems(newItems);
    updateMarkdown(newItems, presentationTitle);
  };
  
  const handleAddCard = (index: number) => {
      const newItem: OutlineItem = {
          id: Date.now().toString(),
          title: 'New Slide',
          points: ['New Point']
      };
      const newItems = [...items];
      newItems.splice(index + 1, 0, newItem);
      setItems(newItems);
      updateMarkdown(newItems, presentationTitle);
  }

  const handlePresentationTitleChange = (newTitle: string) => {
    setPresentationTitle(newTitle);
    updateMarkdown(items, newTitle);
  };

  return (
    <div className={cn("flex flex-col gap-6 max-w-4xl mx-auto p-4")}>
        {/* Presentation Title Input */}
        <div className={cn(
          "bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-2",
          "hover:shadow-md transition-shadow"
        )}>
            <label className={cn("block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2")}>Presentation Title</label>
            <Input
                value={presentationTitle}
                onChange={(e) => handlePresentationTitleChange(e.target.value)}
                className={cn(
                  "text-2xl font-bold border-none px-0",
                  "bg-transparent hover:bg-gray-50 focus:bg-gray-50",
                  "focus:shadow-none rounded transition-colors"
                )}
                placeholder="Enter Presentation Title"
            />
        </div>

        {items.map((item, index) => (
            <React.Fragment key={item.id}>
                <div className={cn("relative group")}>
                    <div className={cn(
                      "flex bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden",
                      "hover:shadow-md transition-shadow"
                    )}>
                        {/* Number Column */}
                        <div className={cn(
                          "w-16 bg-purple-50 flex items-center justify-center",
                          "border-r border-purple-100 flex-shrink-0"
                        )}>
                            <span className={cn("text-xl font-bold text-purple-600")}>{index + 1}</span>
                        </div>

                        {/* Content Column */}
                        <div className={cn("flex-1 p-6")}>
                            <div className={cn("flex justify-between items-start mb-4")}>
                                <Input
                                    value={item.title}
                                    onChange={(e) => handleTitleChange(item.id, e.target.value)}
                                    className={cn(
                                      "text-lg font-bold border-none px-0",
                                      "bg-transparent hover:bg-gray-50 focus:bg-gray-50",
                                      "focus:shadow-none rounded transition-colors"
                                    )}
                                    placeholder="Slide Title"
                                />
                                <Button
                                    type="text"
                                    danger
                                    icon={<DeleteOutlined />}
                                    onClick={() => handleDeleteCard(item.id)}
                                    className={cn("opacity-0 group-hover:opacity-100 transition-opacity")}
                                />
                            </div>

                            <div className={cn("space-y-2")}>
                                {item.points.map((point, pIndex) => (
                                    <div key={pIndex} className={cn("flex items-center gap-2 group/point")}>
                                        <div className={cn("w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0")} />
                                        <Input
                                            value={point}
                                            onChange={(e) => handlePointChange(item.id, pIndex, e.target.value)}
                                            className={cn(
                                              "border-none px-2 py-1 text-gray-600 flex-1",
                                              "hover:bg-gray-50 focus:bg-gray-50",
                                              "focus:shadow-none rounded"
                                            )}
                                            placeholder="Point"
                                        />
                                        <Button
                                            type="text"
                                            size="small"
                                            icon={<DeleteOutlined className={cn("text-gray-400 hover:text-red-500")} />}
                                            onClick={() => handleDeletePoint(item.id, pIndex)}
                                            className={cn("opacity-0 group-hover/point:opacity-100")}
                                        />
                                    </div>
                                ))}
                                <Button
                                    type="dashed"
                                    size="small"
                                    icon={<PlusOutlined />}
                                    onClick={() => handleAddPoint(item.id)}
                                    className={cn("mt-2 text-xs text-gray-400")}
                                >
                                    Add Point
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* Add Card Button (Between items) */}
                <div className={cn("flex justify-center -my-3 z-10 relative opacity-0 hover:opacity-100 transition-opacity")}>
                    <Tooltip title="Add new slide">
                        <Button
                            shape="circle"
                            type="primary"
                            icon={<PlusOutlined />}
                            className={cn("shadow-lg transform scale-125 border-4 border-gray-50")}
                            onClick={() => handleAddCard(index)}
                        />
                    </Tooltip>
                </div>
            </React.Fragment>
        ))}
        
        {items.length === 0 && (
             <div className={cn("text-center py-10")}>
                <Button type="primary" onClick={() => handleAddCard(-1)}>Add First Slide</Button>
             </div>
        )}
    </div>
  );
};
