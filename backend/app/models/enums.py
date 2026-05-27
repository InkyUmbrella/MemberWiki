from enum import Enum


class UserRole(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class VerificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"


class VerificationPurpose(str, Enum):
    REGISTER = "register"
    LOGIN = "login"
    RESET_PASSWORD = "reset_password"


class ProfileVisibility(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"


class DraftReviewStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AchievementCategory(str, Enum):
    AWARD = "award"
    EXPERIENCE = "experience"
