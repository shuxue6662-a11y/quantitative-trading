"""
邮件发送模块
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from pathlib import Path
from jinja2 import Template

from src.utils.logger import logger
from src.utils.config_loader import config_loader


class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        """初始化"""
        # 加载配置
        secrets = config_loader.load('secrets')
        email_config = secrets['email']
        
        self.smtp_host = email_config['smtp_host']
        self.smtp_port = email_config['smtp_port']
        self.use_ssl = email_config['use_ssl']
        self.sender = email_config['sender']
        self.password = email_config['password']
        self.receiver = email_config['receiver']
        
        logger.info(f"邮件发送器初始化: {self.sender} -> {self.receiver}")
    
    def send_html_email(
        self,
        subject: str,
        html_content: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        发送HTML邮件
        
        Args:
            subject: 邮件主题
            html_content: HTML内容
            attachments: 附件路径列表
            
        Returns:
            是否成功
        """
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = self.receiver
            msg['Subject'] = subject
            
            # 添加HTML内容
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 添加附件
            if attachments:
                for filepath in attachments:
                    self._attach_file(msg, filepath)
            
            # 发送
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            
            server.login(self.sender, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def _attach_file(self, msg: MIMEMultipart, filepath: str):
        """添加附件"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            logger.warning(f"附件不存在: {filepath}")
            return
        
        with open(filepath, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={filepath.name}'
        )
        
        msg.attach(part)