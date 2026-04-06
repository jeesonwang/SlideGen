/**
 * Error Boundary Component
 * Catches JavaScript errors in child components and displays fallback UI
 */

import React, { Component } from 'react';
import type { ReactNode } from 'react';
import { Result, Button } from 'antd';
import { WarningOutlined } from '@ant-design/icons';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
    });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      const devError = import.meta.env.DEV ? this.state.error : null;

      return (
        <div className="flex justify-center items-center min-h-screen p-6">
          <Result
            status="error"
            icon={<WarningOutlined />}
            title="Oops! Something went wrong"
            subTitle={
              <div>
                <p>We're sorry, but an unexpected error occurred.</p>
                {devError && (
                  <details className="mt-4 text-left">
                    <summary className="cursor-pointer">Error details</summary>
                    <pre className="mt-2 p-3 bg-surface-100 rounded text-xs overflow-auto">
                      {devError.message}
                      {'\n\n'}
                      {devError.stack}
                    </pre>
                  </details>
                )}
              </div>
            }
            extra={[
              <Button type="primary" key="home" onClick={this.handleReset}>
                Go to Dashboard
              </Button>,
              <Button key="reload" onClick={() => window.location.reload()}>
                Reload Page
              </Button>,
            ]}
          />
        </div>
      );
    }

    return this.props.children;
  }
}
