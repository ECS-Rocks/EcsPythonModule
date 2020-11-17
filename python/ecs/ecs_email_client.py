import json
import boto3
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError


class EmailClient:
    """This class makes it easier to send emails in your code.

    ----

    This class has a method, send_email, with which you can easily send an email message from your Lambda function.
    This class's ctor requires you to have a config.json in your Lambda function's directory to specify the Amazon
    region name.
    """

    def __init__(
            self,
            sender_email_address: str,
            charset: str = "UTF-8"
    ):
        self._sender = sender_email_address
        self._charset = charset
        try:
            config_file = open("config.json")
            self._config_options = json.loads(config_file.read())
        except FileNotFoundError:
            raise FileNotFoundError((
                "Unable to find config.json. "
                "You need config.json in your pwd to use the ecs.EmailClient class."
            ))

        self._client = boto3.client("ses", region_name=self._config_options["region-name"])

    def _plain_to_text_email(self, message: str) -> str:
        return ("".join([
            message,
            "\r\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-",
            f"\r\nBeep beep! I'm a robot. Email my creator at {self._config_options['admin-email']} if you have questions.",
            "\r\n"
        ]))

    def _plain_to_html_email(self, message: str) -> str:
        return """
            <html>
            <head></head>
            <body>
        """ + message.replace("\n", "<br>") + f"""
            <hr>
            <small>
            Beep beep! I'm a robot. Email my creator at {self._config_options['admin-email']} if you have questions.
            </small>
            </body>
            </html>
        """

    def send_email(
            self,
            subject: str,
            message: str,
            dest_address: str,
            tmp_file_attachment_name: str = ""
    ):
        """The send_email method. This method attempts to send an email when it is called.

        :param subject: the subject line of the email
        :param message: the body of the email
        :param dest_address: the address to which the email should be sent
        :param tmp_file_attachment_name: (optional) a file located in /tmp which should be attached to the email
        :return: response from Amazon's SES API
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._sender
        msg["To"] = dest_address
        body_text = self._plain_to_text_email(message)
        body_html = self._plain_to_html_email(message)
        text_part = MIMEText(body_text.encode(self._charset), "plain", self._charset)
        html_part = MIMEText(body_html.encode(self._charset), "html", self._charset)
        msg.attach(text_part)
        msg.attach(html_part)

        if tmp_file_attachment_name:
            part = MIMEApplication(open(f"/tmp/{tmp_file_attachment_name}", "rb").read())
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=tmp_file_attachment_name
            )
            msg.attach(part)

        response = self._client.send_raw_email(
            Source=msg["From"],
            Destinations=[
                msg["To"]
            ],
            RawMessage={
                "Data": msg.as_string()
            }
        )

        return response
