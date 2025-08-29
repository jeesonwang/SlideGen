from fastapi import status
from pydantic import BaseModel

# API内部错误，以1101开头
RequestSuccessCode = 0
UnknownErrorCode = 1001
ParamCheckErrorCode = 1101
ParamTypeErrorCode = 1102
DataBaseErrorCode = 1103
DataExistsErrorCode = 1104
AccessDeniedCode = 1105
RequestTimeoutCode = 1106
ExternalServerErrorCode = 1107
InsideServerErrorCode = 1108
ServiceUnavailableCode = 1109
MethodNotAllowedCode = 1110
DataNotFoundCode = 1111
DataUpdateErrorCode = 1112
DataChangeErrorCode = 1113
DataDelErrorCode = 1114


# 用户错误，以1200开头
UserErrorCode = 1201
ExpireTokenCode = 1202
TokenNotExistsCode = 1203
PermissionDenyCode = 1204
UserNotExistsCode = 1205
PasswordErrorCode = 1206
UserExistsErrorCode = 1207
UserNameNotExistsCode = 1208
UserChangeErrorCode = 1209
UserDelErrorCode = 1210
SourcePasswordErrorCode = 1211
ChangePasswordErrorCode = 1212
UserLockErrorCode = 1213
SystemLockErrorCode = 1214
AuthDenyCode = 1215

# 角色错误，以1300开头
RoleNotExistsCode = 1301
RoleNameExistsCode = 1302
RoleChangeErrorCode = 1303
RoleDelErrorCode = 1304
RoleExistsErrorCode = 1305


class HttpErrorCode(BaseModel):
    message: str
    http_code: int


MESSAGE = {
    RequestSuccessCode: HttpErrorCode(message="请求成功", http_code=status.HTTP_200_OK),
    UnknownErrorCode: HttpErrorCode(message="未知错误", http_code=status.HTTP_500_INTERNAL_SERVER_ERROR),
    # API内部错误，以1101开头
    ParamCheckErrorCode: HttpErrorCode(message="参数错误", http_code=status.HTTP_400_BAD_REQUEST),
    ParamTypeErrorCode: HttpErrorCode(message="数据格式不正确", http_code=status.HTTP_400_BAD_REQUEST),
    DataBaseErrorCode: HttpErrorCode(message="数据库错误", http_code=status.HTTP_400_BAD_REQUEST),
    DataExistsErrorCode: HttpErrorCode(message="数据已存在", http_code=status.HTTP_400_BAD_REQUEST),
    AccessDeniedCode: HttpErrorCode(message="请求被拒绝", http_code=status.HTTP_403_FORBIDDEN),
    RequestTimeoutCode: HttpErrorCode(message="等待超时", http_code=status.HTTP_408_REQUEST_TIMEOUT),
    ExternalServerErrorCode: HttpErrorCode(message="外部服务异常", http_code=status.HTTP_500_INTERNAL_SERVER_ERROR),
    InsideServerErrorCode: HttpErrorCode(message="内部服务异常", http_code=status.HTTP_500_INTERNAL_SERVER_ERROR),
    ServiceUnavailableCode: HttpErrorCode(
        message="接口异常，请稍后再试", http_code=status.HTTP_503_SERVICE_UNAVAILABLE
    ),
    MethodNotAllowedCode: HttpErrorCode(message="方法不允许", http_code=status.HTTP_405_METHOD_NOT_ALLOWED),
    DataNotFoundCode: HttpErrorCode(message="资源不存在", http_code=status.HTTP_404_NOT_FOUND),
    DataUpdateErrorCode: HttpErrorCode(message="资源更新失败", http_code=status.HTTP_400_BAD_REQUEST),
    DataChangeErrorCode: HttpErrorCode(message="资源修改失败", http_code=status.HTTP_400_BAD_REQUEST),
    DataDelErrorCode: HttpErrorCode(message="资源删除失败", http_code=status.HTTP_400_BAD_REQUEST),
    # 用户错误，以1200开头
    UserErrorCode: HttpErrorCode(message="用户错误", http_code=status.HTTP_400_BAD_REQUEST),
    ExpireTokenCode: HttpErrorCode(message="令牌过期或权限变动，请重新登录", http_code=status.HTTP_401_UNAUTHORIZED),
    TokenNotExistsCode: HttpErrorCode(message="token不存在或已失效", http_code=status.HTTP_401_UNAUTHORIZED),
    PermissionDenyCode: HttpErrorCode(message="用户权限不足", http_code=status.HTTP_403_FORBIDDEN),
    UserNotExistsCode: HttpErrorCode(message="用户不存在或已注销，请联系管理员", http_code=status.HTTP_403_FORBIDDEN),
    PasswordErrorCode: HttpErrorCode(message="密码错误", http_code=status.HTTP_403_FORBIDDEN),
    UserExistsErrorCode: HttpErrorCode(message="用户已存在", http_code=status.HTTP_403_FORBIDDEN),
    UserNameNotExistsCode: HttpErrorCode(message="用户不存在", http_code=status.HTTP_403_FORBIDDEN),
    UserChangeErrorCode: HttpErrorCode(message="修改用户失败", http_code=status.HTTP_403_FORBIDDEN),
    UserDelErrorCode: HttpErrorCode(message="删除用户失败", http_code=status.HTTP_403_FORBIDDEN),
    SourcePasswordErrorCode: HttpErrorCode(message="原密码错误", http_code=status.HTTP_403_FORBIDDEN),
    ChangePasswordErrorCode: HttpErrorCode(message="修改密码失败", http_code=status.HTTP_403_FORBIDDEN),
    RoleNotExistsCode: HttpErrorCode(message="角色不存在", http_code=status.HTTP_403_FORBIDDEN),
    RoleNameExistsCode: HttpErrorCode(message="角色名已存在", http_code=status.HTTP_403_FORBIDDEN),
    RoleChangeErrorCode: HttpErrorCode(message="角色修改失败", http_code=status.HTTP_403_FORBIDDEN),
    RoleDelErrorCode: HttpErrorCode(message="角色删除失败", http_code=status.HTTP_403_FORBIDDEN),
    RoleExistsErrorCode: HttpErrorCode(message="角色存在相关用户", http_code=status.HTTP_403_FORBIDDEN),
    AuthDenyCode: HttpErrorCode(message="用户未登录", http_code=status.HTTP_401_UNAUTHORIZED),
}
