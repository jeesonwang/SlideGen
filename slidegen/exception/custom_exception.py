from slidegen.exception.base import ApiError
from slidegen.exception.error_code import (
    AccessDeniedCode,
    AuthDenyCode,
    DataBaseErrorCode,
    DataNotFoundCode,
    ExpireTokenCode,
    ExternalServerErrorCode,
    FileParseErrorCode,
    InsideServerErrorCode,
    ParamCheckErrorCode,
    PasswordErrorCode,
    PermissionDenyCode,
    SystemLockErrorCode,
    TokenNotExistsCode,
    UserErrorCode,
    UserExistsErrorCode,
    UserLockErrorCode,
    UserNotExistsCode,
)


class NotFoundError(ApiError):
    default_code = DataNotFoundCode


class TokenNotExistsError(ApiError):
    default_code = TokenNotExistsCode


class ParamsCheckError(ApiError):
    default_code = ParamCheckErrorCode


class DatasBaseError(ApiError):
    default_code = DataBaseErrorCode


class InsideServerError(ApiError):
    default_code = InsideServerErrorCode


class UserError(ApiError):
    default_code = UserErrorCode


class UserNotExistsError(ApiError):
    default_code = UserNotExistsCode


class UserExistsError(ApiError):
    default_code = UserExistsErrorCode


class PasswordError(ApiError):
    default_code = PasswordErrorCode


class ExpireTokenError(ApiError):
    """该错误的默认错误码将返回401弹回到登录页"""

    default_code = ExpireTokenCode


class PermissionDenyError(ApiError):
    default_code = PermissionDenyCode


class UserLockError(ApiError):
    default_code = UserLockErrorCode


class SystemLockError(ApiError):
    default_code = SystemLockErrorCode


class ServiceConnectionError(ApiError):
    default_code = ExternalServerErrorCode


class AccessDeniedError(ApiError):
    default_code = AccessDeniedCode


class AuthDenyError(ApiError):
    default_code = AuthDenyCode


class FileParseError(ApiError):
    default_code = FileParseErrorCode


class FileTypeError(ApiError):
    default_code = InsideServerErrorCode


class PPTGenError(ApiError):
    default_code = InsideServerErrorCode


class PPTTemplateError(ApiError):
    default_code = InsideServerErrorCode


class MarkdownDocumentError(ApiError):
    default_code = InsideServerErrorCode
