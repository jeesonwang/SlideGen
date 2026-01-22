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
      return (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            padding: 24,
          }}
        >
          <Result
            status="error"
            icon={<WarningOutlined />}
            title="Oops! Something went wrong"
            subTitle={
              <div>
                <p>We're sorry, but an unexpected error occurred.</p>
                {this.state.error && (
                  <details style={{ marginTop: 16, textAlign: 'left' }}>
                    <summary style={{ cursor: 'pointer' }}>Error details</summary>
                    <pre
                      style={{
                        marginTop: 8,
                        padding: 12,
                        background: '#f5f5f5',
                        borderRadius: 4,
                        fontSize: 12,
                        overflow: 'auto',
                      }}
                    >
                      {this.state.error.message}
                      {'\n\n'}
                      {this.state.error.stack}
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
