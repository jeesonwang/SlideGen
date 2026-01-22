/**
 * User Profile Page
 */

import { Card, Descriptions, Form, Input, Button, Space, Typography, Divider } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../store/authStore';
import { useUpdatePassword } from '../../hooks/useUser';

const { Title, Text } = Typography;

export const ProfilePage = () => {
  const { user } = useAuthStore();
  const [passwordForm] = Form.useForm();
  const updatePasswordMutation = useUpdatePassword();

  const handlePasswordUpdate = async (values: any) => {
    try {
      await updatePasswordMutation.mutateAsync({
        current_password: values.currentPassword,
        new_password: values.newPassword,
      });
      passwordForm.resetFields();
    } catch (error) {
      // Error is handled by the mutation hook
    }
  };

  if (!user) {
    return (
      <div style={{ padding: 24 }}>
        <Text type="secondary">Loading user information...</Text>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Title level={2}>Profile</Title>
      <Text type="secondary">Manage your account information and settings</Text>

      <Card
        title={
          <Space>
            <UserOutlined />
            <span>User Information</span>
          </Space>
        }
        style={{ marginTop: 24 }}
      >
        <Descriptions column={1} bordered>
          <Descriptions.Item label="Username">
            <Space>
              <UserOutlined />
              {user.username || 'N/A'}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="Email">
            <Space>
              <MailOutlined />
              {user.email}
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="User ID">
            <Text type="secondary" copyable>
              {user.id}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="Account Status">
            <Text type={user.is_active ? 'success' : 'danger'}>
              {user.is_active ? 'Active' : 'Inactive'}
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="Superuser">
            <Text type={user.is_superuser ? 'warning' : 'secondary'}>
              {user.is_superuser ? 'Yes' : 'No'}
            </Text>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card
        title={
          <Space>
            <LockOutlined />
            <span>Change Password</span>
          </Space>
        }
        style={{ marginTop: 24 }}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordUpdate}
          autoComplete="off"
        >
          <Form.Item
            name="currentPassword"
            label="Current Password"
            rules={[
              { required: true, message: 'Please enter your current password' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Enter current password"
            />
          </Form.Item>

          <Form.Item
            name="newPassword"
            label="New Password"
            rules={[
              { required: true, message: 'Please enter a new password' },
              {
                min: 8,
                message: 'Password must be at least 8 characters',
              },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Enter new password"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="Confirm New Password"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: 'Please confirm your new password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(
                    new Error('The passwords do not match')
                  );
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Confirm new password"
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={updatePasswordMutation.isPending}
              >
                Update Password
              </Button>
              <Button onClick={() => passwordForm.resetFields()}>Reset</Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Divider />

      <Card>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text strong>Account Security Tips</Text>
          <ul style={{ marginLeft: 20, color: '#8c8c8c' }}>
            <li>Use a strong password with at least 8 characters</li>
            <li>Avoid using the same password across multiple sites</li>
            <li>Change your password regularly</li>
            <li>Never share your password with anyone</li>
          </ul>
        </Space>
      </Card>
    </div>
  );
};
