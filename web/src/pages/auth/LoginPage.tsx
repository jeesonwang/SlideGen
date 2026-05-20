/**
 * Login Page
 */

import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';
import { APP_NAME } from '../../utils/constants';
import type { LoginRequest } from '../../api/types/auth.types';
import { shouldRedirectFromLogin } from './loginRedirect';

const { Title, Text } = Typography;

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login, isLoggingIn, loginError, isAuthenticated, user } = useAuth();
  const [form] = Form.useForm();

  // Redirect if already authenticated
  useEffect(() => {
    if (shouldRedirectFromLogin(isAuthenticated, user)) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate, user]);

  const onFinish = async (values: LoginRequest) => {
    try {
      await login(values);
    } catch {
      // Error is handled by useAuth hook
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10 sm:px-6">
      <Card className="relative z-10 w-full max-w-md !rounded-3xl !border !border-border/70 !bg-surface-50 !shadow-soft">
        <Space direction="vertical" size="large" className="w-full">
          {/* Logo & Title */}
          <div className="text-center">
            <div className="mb-4">
              <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-primary-500/20 bg-primary-500/12 text-primary-600 shadow-glow">
                <svg className="h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-label="SlideGen application logo">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
              </div>
            </div>
            <Title level={1} className="!mb-2 !font-heading !text-text-main">
              {APP_NAME}
            </Title>
            <Text type="secondary" className="!text-text-secondary text-base">
              Sign in to your account
            </Text>
          </div>

          {loginError && (
            <Alert
              message="Login Failed"
              description={
                typeof loginError === 'object' && 'detail' in loginError
                  ? String(loginError.detail)
                  : 'Invalid email or password'
              }
              type="error"
              showIcon
              closable
              role="alert"
              className="!rounded-lg"
            />
          )}

          <Form
            form={form}
            name="login"
            onFinish={onFinish}
            layout="vertical"
            autoComplete="off"
          >
            <Form.Item
              name="username"
              label={<span className="font-medium text-text-main">Email</span>}
              rules={[
                { required: true, message: 'Please input your email!' },
                { type: 'email', message: 'Please enter a valid email!' },
              ]}
            >
              <Input
                prefix={<UserOutlined className="text-text-secondary" />}
                placeholder="you@example.com"
                size="large"
                className="!rounded-lg"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label={<span className="font-medium text-text-main">Password</span>}
              rules={[
                { required: true, message: 'Please input your password!' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined className="text-text-secondary" />}
                placeholder="Enter your password"
                size="large"
                className="!rounded-lg"
              />
            </Form.Item>

            <Form.Item className="!mb-4">
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                block
                loading={isLoggingIn}
                className="!h-12 !rounded-lg !font-medium transition-colors duration-200"
              >
                Sign In
              </Button>
            </Form.Item>
          </Form>

          <div className="border-t border-border/70 pt-4 text-center">
            <Text type="secondary" className="!text-text-secondary text-sm">
              Don't have an account?{' '}
              <Link to="/signup" className="text-primary-600 hover:text-primary-700 font-medium transition-colors">
                Sign up
              </Link>
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};
