import subprocess

import pika

from config import settings, logger


class RabbitMQ:
    def __init__(self):
        self.queue = f"nftables.{settings.AGENT_IP}"
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=settings.RABBITMQ_HOSTNAME,
            credentials=pika.PlainCredentials(settings.RABBITMQ_USERNAME, settings.RABBITMQ_PASSWORD)
        ))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=True)

    def start_consuming(self):
        def callback(ch, method, properties, body):
            command = body.decode()
            logger.info(f"[x] Received: {command}")
            result = self.execute_shell_command_linux(command)
            self.send_result_to_producer(result, settings.AGENT_IP)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(queue=self.queue, on_message_callback=callback)
        logger.info(f"[*] Waiting for messages in {self.queue}. To exit press CTRL+C")
        self.channel.start_consuming()

    @staticmethod
    def execute_shell_command_linux(command):
        try:
            completed = subprocess.run(
                ["/bin/bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=30
            )
            if completed.returncode != 0:
                logger.error(f"[!] Shell command failed: {completed.stderr}")
                return completed.stderr
            logger.info(f"[✓] {completed.stdout}")
            return completed.stdout
        except subprocess.TimeoutExpired:
            logger.warning("[!] Shell command timed out.")
            return "Shell command timed out"

    @staticmethod
    def execute_shell_command_windows(command):
        try:
            completed = subprocess.run(
                ["cmd.exe", "/c", command],
                capture_output=True,
                text=True,
                timeout=10
            )
            if completed.returncode != 0:
                logger.error(f"Windows command failed: {completed.stderr}")
                return completed.stderr
            print(completed.stdout)
            return completed.stdout
        except subprocess.TimeoutExpired:
            logger.warning("[!] Windows command timed out.")
            return "Windows command timed out"

    def send_result_to_producer(self, result, routing_key):
        self.channel.basic_publish(
            exchange=settings.EXCHANGE_NAME,
            routing_key=f"*{routing_key}",
            body=result.encode(),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        logger.info(f"[→] Sent result to exchange '{settings.EXCHANGE_NAME}' with routing_key '*{routing_key}'")
