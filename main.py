from config import logger
from rabbitmq import RabbitMQ

if __name__ == "__main__":
    try:
        logger.info("[*] Starting RabbitMQ Agent...")
        consumer = RabbitMQ()
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("\n[!] Agent stopped by user (Ctrl+C)")
    except Exception as e:
        logger.exception(f"[!] Agent crashed: {e}")
