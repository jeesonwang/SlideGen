/**
 * Signup Page
 */

import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, Alert, Space, message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';
import { APP_NAME } from '../../utils/constants';
import type { UserRegister } from '../../api/types/auth.types';

const { Title, Text } = Typography;

export const SignupPage = () => {
  const navigate = useNavigate();
  const { signup, isSigningUp, signupError, isAuthenticated } = useAuth();
  const [form] = Form.useForm();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const onFinish = async (values: UserRegister & { confirmPassword: string }) => {
    try {
      await signup({
        email: values.email,
        password: values.password,
        username: values.username,
      });
      message.success('Account created successfully! Please login.');
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
              Create your account
            </Text>
          </div>

          {signupError && (
            <Alert
              message="Signup Failed"
              description={
                typeof signupError === 'object' && 'detail' in signupError
                  ? String(signupError.detail)
                  : 'Failed to create account'
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
            name="signup"
            onFinish={onFinish}
            layout="vertical"
            autoComplete="off"
          >
            <Form.Item
              name="email"
              label={<span className="font-medium text-text-main">Email</span>}
              rules={[
                { required: true, message: 'Please input your email!' },
                { type: 'email', message: 'Please enter a valid email!' },
              ]}
            >
              <Input
                prefix={<MailOutlined className="text-text-secondary" />}
                placeholder="you@example.com"
                size="large"
                className="!rounded-lg"
              />
            </Form.Item>

            <Form.Item
              name="username"
              label={<span className="font-medium text-text-main">Username (Optional)</span>}
            >
              <Input
                prefix={<UserOutlined className="text-text-secondary" />}
                placeholder="Your username"
                size="large"
                className="!rounded-lg"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label={<span className="font-medium text-text-main">Password</span>}
              rules={[
                { required: true, message: 'Please input your password!' },
                {
                  min: 8,
                  message: 'Password must be at least 8 characters!',
                },
                {
                  max: 40,
                  message: 'Password must not exceed 40 characters!',
                },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined className="text-text-secondary" />}
                placeholder="Password (8-40 characters)"
                size="large"
                className="!rounded-lg"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              label={<span className="font-medium text-text-main">Confirm Password</span>}
              dependencies={['password']}
              rules={[
                { required: true, message: 'Please confirm your password!' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve();
                    }
                    return Promise.reject(
                      new Error('The two passwords do not match!')
                    );
                  },
                }),
              ]}
            >
              <Input.Password
                prefix={<LockOutlined className="text-text-secondary" />}
                placeholder="Confirm your password"
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
                loading={isSigningUp}
                className="!h-12 !rounded-lg !font-medium transition-colors duration-200"
              >
                Sign Up
              </Button>
            </Form.Item>
          </Form>

          <div className="border-t border-border/70 pt-4 text-center">
            <Text type="secondary" className="!text-text-secondary text-sm">
              Already have an account?{' '}
              <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium transition-colors">
                Sign in
              </Link>
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};
