from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import auth_service
from src.conf.config import config


conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME="Contact Systems",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Verify your email !",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)


async def send_email_reset_password(email: EmailStr, username: str, host: str):
    try:
        token_reset_password = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Reset password !",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_reset_password},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password.html")
    except ConnectionErrors as err:
        print(err)


async def send_message_password(email: EmailStr, username: str, host: str):
    try:
        message = MessageSchema(
            subject="Reset the password successfully !",
            recipients=[email],
            template_body={"host": host, "username": username},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="message.html")
    except ConnectionErrors as err:
        print(err)


async def send_random_password(email: EmailStr, username: str, host: str, password: str):
    try:
        message = MessageSchema(
            subject="New password successfully !",
            recipients=[email],
            template_body={"host": host, "username": username, "password": password},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_random_password.html")
    except ConnectionErrors as err:
        print(err)
