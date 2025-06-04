import platform
import subprocess

import pika

from config import settings, logger


class RabbitMQ:
    def __init__(self):
        self.queue = f"nftables.{settings.AGENT_IP}"
        self.os_type = platform.system().lower()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=settings.RABBITMQ_HOSTNAME,
            credentials=pika.PlainCredentials(settings.RABBITMQ_USERNAME, settings.RABBITMQ_PASSWORD)
        ))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=True)
        self.command_executors = {
            'linux': self._execute_shell_command_linux,
            'darwin': self._execute_shell_command_darwin,
            'windows': self._execute_shell_command_windows
        }

    def start_consuming(self):
        def callback(ch, method, properties, body):
            routing_key = method.routing_key
            command = body.decode()
            logger.info(f"[x] Received: {command}")
            if routing_key.startswith("command."):
                result = self.execute_command(command)
                self.send_result_to_producer(result, settings.AGENT_IP)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(queue=self.queue, on_message_callback=callback)
        logger.info(f"[*] Waiting for messages in {self.queue}. To exit press CTRL+C")
        self.channel.start_consuming()

    def execute_command(self, command: str) -> str:
        """Execute command based on current OS type"""
        executor = self.command_executors.get(self.os_type)
        if executor is None:
            error_msg = f"Unsupported operating system: {self.os_type}"
            logger.error(error_msg)
            return error_msg
        return executor(command)

    @staticmethod
    def _execute_shell_command_linux(command: str) -> str:
        """Execute command on Linux systems"""
        try:
            completed = subprocess.run(
                ["/bin/bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=10
            )
            if completed.returncode != 0:
                logger.error(f"[!] Linux command failed: {completed.stderr}")
                return f"Error: {completed.stderr}"
            logger.info(f"[✓] {completed.stdout}")
            return completed.stdout
        except subprocess.TimeoutExpired:
            logger.warning("[!] Linux command timed out")
            return "Error: Command timed out"
        except Exception as e:
            logger.error(f"[!] Linux command error: {str(e)}")
            return f"Error: {str(e)}"

    @staticmethod
    def _execute_shell_command_darwin(command: str) -> str:
        """Execute command on MacOS systems"""
        try:
            completed = subprocess.run(
                ["/bin/zsh", "-c", command],
                capture_output=True,
                text=True,
                timeout=10
            )
            if completed.returncode != 0:
                logger.error(f"[!] MacOS command failed: {completed.stderr}")
                return f"Error: {completed.stderr}"
            logger.info(f"[✓] {completed.stdout}")
            return completed.stdout
        except subprocess.TimeoutExpired:
            logger.warning("[!] MacOS command timed out")
            return "Error: Command timed out"
        except Exception as e:
            logger.error(f"[!] MacOS command error: {str(e)}")
            return f"Error: {str(e)}"

    @staticmethod
    def _execute_shell_command_windows(command: str) -> str:
        """Execute command on Windows systems"""
        try:
            completed = subprocess.run(
                ["cmd.exe", "/c", command],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='cp437'
            )
            if completed.returncode != 0:
                logger.error(f"[!] Windows command failed: {completed.stderr}")
                return f"Error: {completed.stderr}"
            logger.info(f"[✓] {completed.stdout}")
            return completed.stdout
        except subprocess.TimeoutExpired:
            logger.warning("[!] Windows command timed out")
            return "Error: Command timed out"
        except Exception as e:
            logger.error(f"[!] Windows command error: {str(e)}")
            return f"Error: {str(e)}"

    def send_result_to_producer(self, result: str, routing_key: str):
        try:
            self.channel.basic_publish(
                exchange=settings.EXCHANGE_NAME,
                routing_key=f"*{routing_key}",
                body=result.encode(),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            logger.info(f"[→] Sent result to exchange '{settings.EXCHANGE_NAME}' with routing_key '*{routing_key}'")
        except Exception as e:
            logger.error(f"[!] Failed to send result: {str(e)}")
