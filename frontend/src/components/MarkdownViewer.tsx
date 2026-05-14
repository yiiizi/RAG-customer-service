import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Button, App } from 'antd';
import { CopyOutlined } from '@ant-design/icons';
import { copyText } from '@/utils/markdown';

interface Props {
  content: string;
}

export default function MarkdownViewer({ content }: Props) {
  const { message } = App.useApp();

  const handleCopy = (text: string) => {
    copyText(text);
    message.success('已复制');
  };

  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          pre: ({ children, ...props }) => {
            // Extract language from className
            const codeChild = Array.isArray(children) ? children[0] : children;
            let lang = '';
            if (codeChild && typeof codeChild === 'object' && 'props' in codeChild) {
              const className = (codeChild as React.ReactElement).props?.className || '';
              const match = className.match(/language-(\w+)/);
              if (match) lang = match[1];
            }
            return (
              <div className="code-block-wrapper" style={{ position: 'relative', marginTop: 8, marginBottom: 8 }}>
                {lang && (
                  <span className="code-block-lang">{lang}</span>
                )}
                <pre {...props}>{children}</pre>
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  style={{ position: 'absolute', top: 4, right: 4, color: 'var(--text-muted)', zIndex: 2 }}
                  onClick={() => {
                    const text = extractText(children);
                    handleCopy(text);
                  }}
                />
              </div>
            );
          },
          code: ({ className, children, ...props }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code style={{ background: 'var(--bg-hover)', padding: '2px 6px', borderRadius: 4 }} {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function extractText(children: React.ReactNode): string {
  if (typeof children === 'string') return children;
  if (Array.isArray(children)) return children.map(extractText).join('');
  if (children && typeof children === 'object' && 'props' in children) {
    return extractText((children as React.ReactElement).props.children);
  }
  return '';
}
