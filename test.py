import threading
import time

import pika

from config import settings, logger


class CommandClient:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ_HOSTNAME,
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ_USERNAME,
                    settings.RABBITMQ_PASSWORD
                )
            )
        )
        self.channel = self.connection.channel()
        self.exchange = settings.EXCHANGE_NAME
        self.agent_ip = settings.AGENT_IP
        self.command_routing_key = f"command.{self.agent_ip}"
        self.reply_queue = f"nftables.{self.agent_ip}"

        # Declare exchange and reply queue
        self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct', durable=True)
        self.channel.queue_declare(queue=self.reply_queue, durable=True)
        self.channel.queue_bind(
            exchange=self.exchange,
            queue=self.reply_queue,
            routing_key=self.reply_queue
        )

    def send_command(self, command):
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.command_routing_key,
            body=command.encode(),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        logger.info(f"[→] Sent command: '{command}'")

    def start_listening_for_response(self):
        def callback(ch, method, properties, body):
            logger.info(f"\n[✓] Result from agent:\n{body.decode()}\n")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(
            queue=self.reply_queue,
            on_message_callback=callback
        )

        logger.info(f"[*] Listening for response in '{self.reply_queue}'...")
        self.channel.start_consuming()


def main():
    client = CommandClient()

    # Start listener in background thread
    listener_thread = threading.Thread(target=client.start_listening_for_response, daemon=True)
    listener_thread.start()

    logger.info("Type a shell command to send to agent. Type 'exit' to quit.")
    while True:
        try:
            cmd = input(">> ")
            if cmd.strip().lower() == "exit":
                break
            client.send_command(cmd)
            time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("\n[!] Interrupted by user")
            break

    client.connection.close()


if __name__ == "__main__":
    main()
