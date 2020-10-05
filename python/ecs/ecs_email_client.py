import json
import boto3
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError


class EmailClient:

    def __init__(
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
                "You need config.json in your pwd to use the ecs.DynamoDB class."
            ))

        self._client = boto3.client("ses", region_name=self._config_options["region-name"])


    @staticmethod
    def _plain_to_text_email(message: str) -> str:
        return ("".join([
            message,
            "\r\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-",
            "\r\nBeep beep! I'm a robot. Email my creator at Dante@elkhornservice.com if you have questions.",
            "\r\n"
        ]))


    @staticmethod
    def _plain_to_html_email(message: str) -> str:
        return """
            <html>
            <head></head>
            <body>
        """ + message.replace("\n", "<br>") + """
            <hr>
            <small>
            Beep beep! I'm a robot. Email my creator at Dante@elkhornservice.com if you have questions.
            </small>
            </body>
            </html>
        """


    def send_email(
        subject:      str,
        message:      str,
        dest_address: str,
        tmp_file_attachment_name: str = ""
    ):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._sender
        msg["To"] = dest_address
        body_text = self._plain_to_text_email(message)
        body_html = self._plain_to_html_email(message)
        textpart = MIMEText(body_text.encode(self._charset), "plain", self._charset)
        htmlpart = MIMEText(body_html.encode(self._charset), "html", self._charset)
        msg.attach(textpart)
        msg.attach(htmlpart)

        if tmp_file_attachment_name:
            part = MIMEApplication(open(f"/tmp/{file_name}", "rb").read())
            part.add_header("Content-Disposition", "attachment", filename=file_name)
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
