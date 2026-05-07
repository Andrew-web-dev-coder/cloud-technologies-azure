# Azure Practice 3 — Service Bus Queue Communication

## Description

This project contains three local FastAPI services connected to Azure SQL Database.

For Azure Practice 3, communication through Azure Service Bus Queue is implemented between two local applications:

- `submission-service` sends messages to Azure Service Bus
- `feedback-service` reads messages from Azure Service Bus in a background process

When a new submission is created, the submission service saves it to Azure SQL Database and sends a message to the Service Bus queue.  
The feedback service receives this message and automatically creates feedback for the submitted item.

## Services

### submission-service

Port: `8001`

Responsibilities:

- create submission records
- read submissions from Azure SQL Database
- send `submission_created` messages to Azure Service Bus

Run:

```bash
cd submission-service
uvicorn main:app --reload --port 8001

Swagger:

http://127.0.0.1:8001/docs
feedback-service

Port: 8002

Responsibilities:

read feedback records from Azure SQL Database
listen to Azure Service Bus Queue in a background process
automatically create feedback after receiving a message

Run:

cd feedback-service
uvicorn main:app --reload --port 8002

Swagger:

http://127.0.0.1:8002/docs
gallery-service

Port: 8003

Responsibilities:

create gallery records
read galleries from Azure SQL Database

Run:

cd gallery-service
uvicorn main:app --reload --port 8003

Swagger:

http://127.0.0.1:8003/docs
Azure Resources

Used Azure services:

Azure SQL Database
Azure Service Bus Queue
Environment Variables

Each service uses a local .env file.

Example for database connection:

DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_SERVER=your_server.database.windows.net
DB_DATABASE=your_database

For submission-service:

SERVICE_BUS_SEND_CONNECTION_STRING=your_send_connection_string
QUEUE_NAME=your_queue_name

For feedback-service:

SERVICE_BUS_CONNECTION=your_listen_connection_string
QUEUE_NAME=your_queue_name
Installation

Install dependencies inside each service folder:

pip install -r requirements.txt
How to Test
Start submission-service on port 8001.
Start feedback-service on port 8002.
Open Submission Swagger:
http://127.0.0.1:8001/docs
Execute:
POST /submissions

Example request:

{
  "title": "Service Bus Final Test",
  "artist": "Aleksandr Shepilov",
  "status": "pending"
}
Check the terminal of feedback-service.

Expected output:

[SERVICE BUS] Received: ...
[DATABASE] Feedback saved for submission_id=...
Open Feedback Swagger:
http://127.0.0.1:8002/docs
Execute:
GET /feedbacks

