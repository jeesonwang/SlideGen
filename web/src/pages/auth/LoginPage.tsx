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
    } catch (error) {
      // Error is handled by useAuth hook
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center gradient-bg relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-accent-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Glass Card */}
      <Card className="w-full max-w-md glass-card relative z-10 border-0 animate-scale-in">
        <Space direction="vertical" size="large" className="w-full">
          {/* Logo & Title */}
          <div className="text-center">
            <div className="mb-4">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-600 to-primary-700 shadow-soft-lg mb-4">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-label="SlideGen application logo">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
              </div>
            </div>
            <Title level={2} className="!mb-2 !font-heading !text-secondary-900">
              {APP_NAME}
            </Title>
            <Text type="secondary" className="text-base">
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
              label={<span className="text-secondary-700 font-medium">Email</span>}
              rules={[
                { required: true, message: 'Please input your email!' },
                { type: 'email', message: 'Please enter a valid email!' },
              ]}
            >
              <Input
                prefix={<UserOutlined className="text-secondary-400" />}
                placeholder="you@example.com"
                size="large"
                className="!rounded-lg"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label={<span className="text-secondary-700 font-medium">Password</span>}
              rules={[
                { required: true, message: 'Please input your password!' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined className="text-secondary-400" />}
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
                className="!h-12 !rounded-lg !bg-primary-600 hover:!bg-primary-700 !font-medium !shadow-soft hover:!shadow-soft-lg transition-all duration-200"
              >
                Sign In
              </Button>
            </Form.Item>
          </Form>

          <div className="text-center pt-4 border-t border-secondary-200/50">
            <Text type="secondary" className="text-sm">
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
