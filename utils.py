import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header



def send_email(subject, message, to_email=None):
    """发送邮件

    Args:
        subject: 邮件主题
        message: 邮件内容
        to_email: 收件人邮箱，如果为None则发送给管理员邮箱
    """
    try:
        # 邮件发送配置
        smtp_server = "smtp.163.com"
        smtp_port = 465

        # 发件人信息
        from_email = os.environ.get("EMAIL_ADDRESS", "aswemaythink@163.com")
        password = os.environ.get("EMAIL_PASSWORD", "")

        # 如果没有指定收件人，则发给管理员邮箱
        if to_email is None:
            to_email = os.environ.get("ADMIN_EMAIL", "")

        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')

        # 添加邮件正文
        msg.attach(MIMEText(message, 'plain', 'utf-8'))

        # 连接SMTP服务器并发送邮件
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())

        print(f"邮件已成功发送到 {to_email}")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"发送邮件失败: {str(e)}")
        return False


def send_reset_email(to_email, reset_url):
    """发送密码重置邮件"""
    subject = "六爻AI排盘 — 密码重置"
    message = f"""您好，

您正在申请重置六爻AI排盘的登录密码。

请点击以下链接重置密码（30分钟内有效）：
{reset_url}

如果您没有发起此操作，请忽略本邮件。

—— 六爻AI排盘"""
    return send_email(subject, message, to_email=to_email)


