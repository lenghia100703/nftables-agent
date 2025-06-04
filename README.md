# RabbitMQ NFTables Agent

The agent receives commands from the RabbitMQ Server to execute NFTables commands on the Linux system. This agent will register a private queue based on the IP of the server where the agent is installed, listen for commands from the RabbitMQ Server, execute them on the system and return the results to the RabbitMQ Server.

## System Requirements

- Ubuntu/Debian Linux
- Python >= 3.10

## Quick Start

1. Clone repository:
```
git clone https://github.com/lenghia100703/nftables-agent.git
```
```
cd nftables-agent
```

2. Setup:
- Setup enviroments
```
cp .env.example .env
```
Then you edit the `.env` file with the appropriate parameters:

| Name              | Type   | Description                                                |
|-------------------|--------|------------------------------------------------------------|
| RABBITMQ_HOSTNAME | String | The IP address where you place the RabbitMQ Server         |
| RABBITMQ_USERNAME | String | Username of that RabbitMQ Server                           |
| RABBITMQ_PASSWORD | String | Password of that RabbitMQ Server                           |
| AGENT_IP          | String | Agent IP address (IP of the server where the agent is installed) |
| EXCHANGE_NAME     | String | The name of the RabbitMQ Server Exchange                       |

- Run script setup
```
sudo ./deploy/install.sh
```
3. Agent actions:
- Check status
```
sudo supervisorctl status nftables_agent
```
- Restart agent
```
sudo supervisorctl restart nftables_agent
```

- Stop agent
```
sudo supervisorctl stop nftables_agent
```

- Start agent
```
sudo supervisorctl start nftables_agent
```

- Check logs of agent

View output log
```
tail -f /var/log/nftables_agent/out.log
```
View error log
```
tail -f /var/log/nftables_agent/err.log
```
## License

[MIT License](LICENSE)

## Contact

- Email: lenghia1007@gmail.com
- Project Link: https://github.com/lenghia100703/nftables-agent

## Acknowledgments

- RabbitMQ Team
- Python Pika Library
- Supervisor Project
