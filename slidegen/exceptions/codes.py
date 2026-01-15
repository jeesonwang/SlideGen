from fastapi import status
from pydantic import BaseModel

# API internal error, starts with 1101
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
FileParseErrorCode = 1115

# User error, starts with 1201
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

# Role error, starts with 1301
RoleNotExistsCode = 1301
RoleNameExistsCode = 1302
RoleChangeErrorCode = 1303
RoleDelErrorCode = 1304
RoleExistsErrorCode = 1305


class HttpErrorCode(BaseModel):
    message: str
    http_code: int


MESSAGE = {
    RequestSuccessCode: HttpErrorCode(message="Request success", http_code=status.HTTP_200_OK),
    UnknownErrorCode: HttpErrorCode(message="Unknown error", http_code=status.HTTP_500_INTERNAL_SERVER_ERROR),
    # API internal error, starts with 1101
    ParamCheckErrorCode: HttpErrorCode(message="Parameter error", http_code=status.HTTP_400_BAD_REQUEST),
    ParamTypeErrorCode: HttpErrorCode(message="Data format error", http_code=status.HTTP_400_BAD_REQUEST),
    DataBaseErrorCode: HttpErrorCode(message="Database error", http_code=status.HTTP_400_BAD_REQUEST),
    DataExistsErrorCode: HttpErrorCode(message="Data already exists", http_code=status.HTTP_400_BAD_REQUEST),
    AccessDeniedCode: HttpErrorCode(message="Request denied", http_code=status.HTTP_403_FORBIDDEN),
    RequestTimeoutCode: HttpErrorCode(message="Request timeout", http_code=status.HTTP_408_REQUEST_TIMEOUT),
    ExternalServerErrorCode: HttpErrorCode(
        message="External server error", http_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    ),
    InsideServerErrorCode: HttpErrorCode(
        message="Internal server error", http_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    ),
    ServiceUnavailableCode: HttpErrorCode(
        message="Service unavailable, please try again later", http_code=status.HTTP_503_SERVICE_UNAVAILABLE
    ),
    MethodNotAllowedCode: HttpErrorCode(message="Method not allowed", http_code=status.HTTP_405_METHOD_NOT_ALLOWED),
    DataNotFoundCode: HttpErrorCode(message="Resource not found", http_code=status.HTTP_404_NOT_FOUND),
    DataUpdateErrorCode: HttpErrorCode(message="Resource update failed", http_code=status.HTTP_400_BAD_REQUEST),
    DataChangeErrorCode: HttpErrorCode(message="Resource modification failed", http_code=status.HTTP_400_BAD_REQUEST),
    DataDelErrorCode: HttpErrorCode(message="Resource deletion failed", http_code=status.HTTP_400_BAD_REQUEST),
    FileParseErrorCode: HttpErrorCode(message="File parsing failed", http_code=status.HTTP_400_BAD_REQUEST),
    # User error, starts with 1201
    UserErrorCode: HttpErrorCode(message="User error", http_code=status.HTTP_400_BAD_REQUEST),
    ExpireTokenCode: HttpErrorCode(
        message="Token expired or permissions changed, please re-login", http_code=status.HTTP_401_UNAUTHORIZED
    ),
    TokenNotExistsCode: HttpErrorCode(
        message="Token does not exist or has expired", http_code=status.HTTP_401_UNAUTHORIZED
    ),
    PermissionDenyCode: HttpErrorCode(message="User permissions insufficient", http_code=status.HTTP_403_FORBIDDEN),
    UserNotExistsCode: HttpErrorCode(
        message="User does not exist or has been logged out, please contact the administrator",
        http_code=status.HTTP_403_FORBIDDEN,
    ),
    PasswordErrorCode: HttpErrorCode(message="Password error", http_code=status.HTTP_403_FORBIDDEN),
    UserExistsErrorCode: HttpErrorCode(message="User already exists", http_code=status.HTTP_403_FORBIDDEN),
    UserNameNotExistsCode: HttpErrorCode(message="User does not exist", http_code=status.HTTP_403_FORBIDDEN),
    UserChangeErrorCode: HttpErrorCode(message="Failed to modify user", http_code=status.HTTP_403_FORBIDDEN),
    UserDelErrorCode: HttpErrorCode(message="Failed to delete user", http_code=status.HTTP_403_FORBIDDEN),
    SourcePasswordErrorCode: HttpErrorCode(message="Original password error", http_code=status.HTTP_403_FORBIDDEN),
    ChangePasswordErrorCode: HttpErrorCode(message="Failed to modify password", http_code=status.HTTP_403_FORBIDDEN),
    RoleNotExistsCode: HttpErrorCode(message="Role does not exist", http_code=status.HTTP_403_FORBIDDEN),
    RoleNameExistsCode: HttpErrorCode(message="Role name already exists", http_code=status.HTTP_403_FORBIDDEN),
    RoleChangeErrorCode: HttpErrorCode(message="Failed to modify role", http_code=status.HTTP_403_FORBIDDEN),
    RoleDelErrorCode: HttpErrorCode(message="Failed to delete role", http_code=status.HTTP_403_FORBIDDEN),
    RoleExistsErrorCode: HttpErrorCode(message="Role exists related users", http_code=status.HTTP_403_FORBIDDEN),
    AuthDenyCode: HttpErrorCode(message="User not logged in", http_code=status.HTTP_401_UNAUTHORIZED),
}
