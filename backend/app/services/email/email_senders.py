"""
Specialized email sending functions for different use cases.
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.risk_event import RiskEvent
from app.models.email import EmailType, EmailPriority
from app.services.email.email_service import email_service

logger = logging.getLogger(__name__)


async def send_patient_invitation_email(
    db: AsyncSession,
    patient: Patient,
    doctor: Doctor,
    user: User,
    temp_password: str,
) -> None:
    """
    Send invitation email to a newly created patient account.

    Args:
        db: Database session
        patient: Patient model instance
        doctor: Doctor who created the account
        user: User model instance
        temp_password: Temporary password for first login
    """
    if not settings.EMAIL_ENABLED:
        logger.info(f"Email disabled, skipping patient invitation for {user.email}")
        return

    context = {
        "patient_name": f"{patient.first_name} {patient.last_name}".strip() or "Patient",
        "doctor_name": f"{doctor.first_name} {doctor.last_name}".strip() or "Doctor",
        "email": user.email,
        "temp_password": temp_password,
        "login_url": f"{settings.FRONTEND_URL}/login",
        "app_name": settings.APP_NAME,
    }

    try:
        html_content, text_content = email_service.render_template(
            "patient_invitation",
            context
        )
    except Exception as e:
        logger.error(f"Failed to render patient invitation template: {e}")
        # Use fallback HTML
        html_content = _get_patient_invitation_fallback_html(context)
        text_content = None

    await email_service.queue_email(
        db=db,
        email_type=EmailType.PATIENT_INVITATION,
        recipient_email=user.email,
        recipient_user_id=user.id,
        recipient_name=context["patient_name"],
        subject=f"欢迎加入{settings.APP_NAME} - 您的账户已创建",
        html_content=html_content,
        text_content=text_content,
        priority=EmailPriority.NORMAL,
        metadata={"doctor_id": doctor.id},
    )

    # Send immediately
    from sqlalchemy import select
    result = await db.execute(
        select(EmailLog).order_by(EmailLog.created_at.desc()).limit(1)
    )
    email_log = result.scalar_one_or_none()
    if email_log:
        await email_service.send_queued_email_now(db, email_log)


# Need to import EmailLog here to avoid circular import
from app.models.email import EmailLog


async def send_password_reset_email(
    db: AsyncSession,
    user: User,
    reset_token: str,
    expires_minutes: int = 30,
) -> None:
    """
    Send password reset email.

    Args:
        db: Database session
        user: User requesting password reset
        reset_token: Secure reset token
        expires_minutes: Token expiration time in minutes
    """
    if not settings.EMAIL_ENABLED:
        logger.info(f"Email disabled, skipping password reset for {user.email}")
        return

    # Get user name
    user_name = "用户"
    if hasattr(user, 'patient_profile') and user.patient_profile:
        user_name = f"{user.patient_profile.first_name} {user.patient_profile.last_name}".strip()
    elif hasattr(user, 'doctor_profile') and user.doctor_profile:
        user_name = f"{user.doctor_profile.first_name} {user.doctor_profile.last_name}".strip()

    context = {
        "user_name": user_name or "用户",
        "reset_url": f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
        "expires_minutes": expires_minutes,
        "app_name": settings.APP_NAME,
    }

    try:
        html_content, text_content = email_service.render_template(
            "password_reset",
            context
        )
    except Exception as e:
        logger.error(f"Failed to render password reset template: {e}")
        html_content = _get_password_reset_fallback_html(context)
        text_content = None

    email_log = await email_service.queue_email(
        db=db,
        email_type=EmailType.PASSWORD_RESET,
        recipient_email=user.email,
        recipient_user_id=user.id,
        recipient_name=user_name,
        subject=f"{settings.APP_NAME} - 密码重置请求",
        html_content=html_content,
        text_content=text_content,
        priority=EmailPriority.HIGH,
    )

    # Send immediately for password reset
    await email_service.send_queued_email_now(db, email_log)


async def send_risk_alert_email(
    db: AsyncSession,
    risk_event: RiskEvent,
    patient: Patient,
    doctor: Doctor,
) -> None:
    """
    Send urgent risk alert email to the doctor.

    Args:
        db: Database session
        risk_event: Detected risk event
        patient: Patient with the risk
        doctor: Doctor responsible for the patient
    """
    if not settings.EMAIL_ENABLED or not settings.EMAIL_RISK_ALERTS_ENABLED:
        logger.info(f"Risk alert emails disabled, skipping for patient {patient.id}")
        return

    # Get doctor's email
    result = await db.execute(
        select(User).where(User.id == doctor.user_id)
    )
    doctor_user = result.scalar_one_or_none()
    if not doctor_user:
        logger.error(f"Cannot find user for doctor {doctor.id}")
        return

    context = {
        "doctor_name": f"{doctor.first_name} {doctor.last_name}".strip() or "Doctor",
        "patient_name": f"{patient.first_name} {patient.last_name}".strip() or "Patient",
        "patient_id": patient.id,
        "risk_level": risk_event.risk_level.value if risk_event.risk_level else "UNKNOWN",
        "risk_type": risk_event.risk_type.value if risk_event.risk_type else "未知",
        "trigger_text": (risk_event.trigger_text[:200] + "...") if risk_event.trigger_text and len(risk_event.trigger_text) > 200 else (risk_event.trigger_text or ""),
        "detected_at": risk_event.created_at.strftime("%Y-%m-%d %H:%M") if risk_event.created_at else datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "dashboard_url": f"{settings.FRONTEND_URL}/risk-queue",
        "app_name": settings.APP_NAME,
    }

    try:
        html_content, text_content = email_service.render_template(
            "risk_alert",
            context
        )
    except Exception as e:
        logger.error(f"Failed to render risk alert template: {e}")
        html_content = _get_risk_alert_fallback_html(context)
        text_content = None

    # Determine priority based on risk level
    priority = EmailPriority.URGENT if context["risk_level"] in ["CRITICAL", "HIGH"] else EmailPriority.HIGH

    email_log = await email_service.queue_email(
        db=db,
        email_type=EmailType.RISK_ALERT,
        recipient_email=doctor_user.email,
        recipient_user_id=doctor_user.id,
        recipient_name=context["doctor_name"],
        subject=f"[紧急] {settings.APP_NAME} - 患者风险警报: {context['patient_name']}",
        html_content=html_content,
        text_content=text_content,
        priority=priority,
        related_entity_type="risk_event",
        related_entity_id=risk_event.id,
        metadata={
            "patient_id": patient.id,
            "risk_level": context["risk_level"],
        },
    )

    # Send immediately for risk alerts
    await email_service.send_queued_email_now(db, email_log)


async def send_appointment_reminder_email(
    db: AsyncSession,
    patient: Patient,
    doctor: Doctor,
    appointment_time: datetime,
    reminder_type: str = "24h",  # "24h" or "1h"
) -> None:
    """
    Send appointment reminder email to patient.

    Args:
        db: Database session
        patient: Patient with the appointment
        doctor: Doctor for the appointment
        appointment_time: Scheduled appointment time
        reminder_type: Type of reminder ("24h" or "1h")
    """
    if not settings.EMAIL_ENABLED:
        logger.info(f"Email disabled, skipping appointment reminder for patient {patient.id}")
        return

    # Get patient's email
    result = await db.execute(
        select(User).where(User.id == patient.user_id)
    )
    patient_user = result.scalar_one_or_none()
    if not patient_user:
        logger.error(f"Cannot find user for patient {patient.id}")
        return

    context = {
        "patient_name": f"{patient.first_name} {patient.last_name}".strip() or "Patient",
        "doctor_name": f"{doctor.first_name} {doctor.last_name}".strip() or "Doctor",
        "appointment_time": appointment_time.strftime("%Y年%m月%d日 %H:%M"),
        "reminder_type": "24小时" if reminder_type == "24h" else "1小时",
        "app_name": settings.APP_NAME,
    }

    try:
        html_content, text_content = email_service.render_template(
            "appointment_reminder",
            context
        )
    except Exception as e:
        logger.error(f"Failed to render appointment reminder template: {e}")
        html_content = _get_appointment_reminder_fallback_html(context)
        text_content = None

    await email_service.queue_email(
        db=db,
        email_type=EmailType.APPOINTMENT_REMINDER,
        recipient_email=patient_user.email,
        recipient_user_id=patient_user.id,
        recipient_name=context["patient_name"],
        subject=f"{settings.APP_NAME} - 预约提醒: {appointment_time.strftime('%m月%d日 %H:%M')}",
        html_content=html_content,
        text_content=text_content,
        priority=EmailPriority.NORMAL,
        metadata={
            "appointment_time": appointment_time.isoformat(),
            "reminder_type": reminder_type,
        },
    )


# ============================================
# Fallback HTML Templates
# ============================================

def _get_base_style() -> str:
    """Get base CSS styles for emails."""
    return """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2563EB; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { padding: 30px 20px; background: #ffffff; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; background: #f9f9f9; border-radius: 0 0 8px 8px; }
        .button { display: inline-block; padding: 12px 24px; background: #2563EB; color: white; text-decoration: none; border-radius: 6px; margin: 10px 0; }
        .alert { padding: 15px; border-radius: 6px; margin: 15px 0; }
        .alert-danger { background: #FEE2E2; border: 1px solid #DC2626; color: #991B1B; }
        .alert-warning { background: #FEF3C7; border: 1px solid #F59E0B; color: #92400E; }
        .info-box { background: #F3F4F6; padding: 15px; border-radius: 6px; margin: 20px 0; }
    </style>
    """


def _get_patient_invitation_fallback_html(context: dict) -> str:
    """Fallback HTML for patient invitation email."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {_get_base_style()}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{context['app_name']}</h1>
            </div>
            <div class="content">
                <h2>您好，{context['patient_name']}</h2>
                <p>您的医生 <strong>{context['doctor_name']}</strong> 已在 {context['app_name']} 平台为您创建了账户。</p>
                <p>您可以使用以下信息登录：</p>
                <div class="info-box">
                    <p><strong>登录邮箱：</strong> {context['email']}</p>
                    <p><strong>临时密码：</strong> {context['temp_password']}</p>
                </div>
                <div class="alert alert-warning">
                    <strong>安全提示：</strong> 首次登录后，请立即修改密码。
                </div>
                <p style="text-align: center;">
                    <a href="{context['login_url']}" class="button">立即登录</a>
                </p>
            </div>
            <div class="footer">
                <p>此邮件由 {context['app_name']} 自动发送，请勿直接回复</p>
            </div>
        </div>
    </body>
    </html>
    """


def _get_password_reset_fallback_html(context: dict) -> str:
    """Fallback HTML for password reset email."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {_get_base_style()}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{context['app_name']}</h1>
            </div>
            <div class="content">
                <h2>密码重置请求</h2>
                <p>您好，{context['user_name']}</p>
                <p>我们收到了您的密码重置请求。如果这不是您本人操作，请忽略此邮件。</p>
                <p>点击下方按钮重置您的密码：</p>
                <p style="text-align: center;">
                    <a href="{context['reset_url']}" class="button">重置密码</a>
                </p>
                <div class="alert alert-warning">
                    <strong>注意：</strong> 此链接将在 {context['expires_minutes']} 分钟后过期。
                </div>
            </div>
            <div class="footer">
                <p>此邮件由 {context['app_name']} 自动发送，请勿直接回复</p>
            </div>
        </div>
    </body>
    </html>
    """


def _get_risk_alert_fallback_html(context: dict) -> str:
    """Fallback HTML for risk alert email."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {_get_base_style()}
    </head>
    <body>
        <div class="container">
            <div class="header" style="background: #DC2626;">
                <h1>紧急风险警报</h1>
            </div>
            <div class="content">
                <div class="alert alert-danger">
                    <strong>风险级别：</strong> {context['risk_level']}
                </div>
                <p>尊敬的 {context['doctor_name']} 医生，</p>
                <p>系统检测到您的患者 <strong>{context['patient_name']}</strong> 存在潜在风险：</p>
                <div class="info-box">
                    <p><strong>风险类型：</strong> {context['risk_type']}</p>
                    <p><strong>检测时间：</strong> {context['detected_at']}</p>
                    <p><strong>触发内容：</strong> "{context['trigger_text']}"</p>
                </div>
                <p style="text-align: center;">
                    <a href="{context['dashboard_url']}" class="button" style="background: #DC2626;">立即查看详情</a>
                </p>
            </div>
            <div class="footer">
                <p>此警报由 {context['app_name']} 的AI风险检测系统自动生成</p>
            </div>
        </div>
    </body>
    </html>
    """


def _get_appointment_reminder_fallback_html(context: dict) -> str:
    """Fallback HTML for appointment reminder email."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        {_get_base_style()}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{context['app_name']}</h1>
            </div>
            <div class="content">
                <h2>预约提醒</h2>
                <p>您好，{context['patient_name']}</p>
                <p>您与 <strong>{context['doctor_name']}</strong> 医生的预约将在 <strong>{context['reminder_type']}</strong> 后开始。</p>
                <div class="info-box">
                    <p><strong>预约时间：</strong> {context['appointment_time']}</p>
                </div>
                <p>请准时参加，如需取消请提前与医生联系。</p>
            </div>
            <div class="footer">
                <p>此邮件由 {context['app_name']} 自动发送，请勿直接回复</p>
            </div>
        </div>
    </body>
    </html>
    """
