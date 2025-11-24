# VulnTrack Pro

VulnTrack Pro is a comprehensive vulnerability tracking and management tool designed for security professionals. It integrates with Nmap and OpenVAS to provide a unified view of your security posture.

## Features

- **Target Management**: Organize targets into groups.
- **Scanning**: Integrated Nmap and OpenVAS scanning.
- **Vulnerability Tracking**: Parse and manage vulnerabilities.
- **Ticketing**: Assign remediation tasks to users.
- **Reporting**: Generate HTML and PDF reports.
- **Dashboard**: Visualize security metrics.

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL (optional, SQLite used by default)
- Nmap

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/vulntrack-pro.git
    cd vulntrack-pro
    ```

2.  Run the setup script:
    ```bash
    ./setup.sh
    ```

3.  Start the application:
    ```bash
    ./start.sh
    ```

## Docker

Run with Docker Compose:

```bash
docker-compose up --build
```

## Testing

Run tests:

```bash
./venv/bin/pytest tests/
```
