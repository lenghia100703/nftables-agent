import os
import json
import time
import subprocess
import pika


class RabbitMQ:
    def __init__(self):
        self.host_name = os.getenv("RABBITMQ_HOSTNAME")
        self.username = os.getenv("RABBITMQ_USERNAME")
        self.password = os.getenv("RABBITMQ_PASSWORD")
        self.host = os.getenv("AGENT_IP")
        self.queue = f"nfttables.{self.host}"
        self.exchange = "nfttables"

        credentials = pika.PlainCredentials(self.username, self.password)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=self.host_name,
            credentials=credentials
        ))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue=self.queue, durable=True)

    def start_consuming(self):
        def callback(ch, method, properties, body):
            command = body.decode()
            print(f"[x] Received: {command}")
            result = self.execute_shell_command(command)
            self.send_result_to_producer(result, self.host)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(queue=self.queue, on_message_callback=callback)
        print(f"[*] Waiting for messages in {self.queue}. To exit press CTRL+C")
        self.channel.start_consuming()

    def execute_shell_command(self, command):
        try:
            completed = subprocess.run(
                ["/bin/bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=30
            )
            if completed.returncode != 0:
                print(f"[!] Shell command failed: {completed.stderr}")
                return completed.stderr
            print(f"[✓] {completed.stdout}")
            return completed.stdout
        except subprocess.TimeoutExpired:
            print("[!] Shell command timed out.")
            return "Shell command timed out"

    def send_result_to_producer(self, result, routing_key):
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=f"*{routing_key}",
            body=result.encode(),
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            )
        )
        print(f"[→] Sent result to exchange '{self.exchange}' with routing_key '*{routing_key}'")
