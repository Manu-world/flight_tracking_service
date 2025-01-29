
# boardandgo-notification-service

![logo](https://github.com/user-attachments/assets/29e52ad5-ab5f-4c6a-820f-63f067f4ce01)

# Flight Notification Service

## Overview

This project implements a real-time flight notification service using `langgraph`, `langchain`, and `groq`. It integrates with [Aviation Stack](https://aviationstack.com/) for real-time flight data and Twilio for SMS notifications. The service takes a flight code (e.g., `RJA3813`) and a recipient's phone number, then sends automated SMS updates about the flight status.

## Features

- Real-time flight tracking via Aviation Stack API
- Automated SMS notifications via Twilio

## Prerequisites

- Python 3.8+
- Twilio Account
- Groq API Key
- Aviation Stack API Key

## Environment Variables

Add the following to your `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
AVIATION_STACK_API_KEY=your_aviation_stack_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
```

## Installation

1. Clone the repository:

```bash
git clone [your-private-repo-url]
cd boardandgo-notification-service
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your environment variables in `.env`

## Usage

To send notifications programmatically:

```python
from notification_agent import send_notification_for_flight

# Send a notification
result = send_notification_for_flight(
    flight_code="RJA3813",  # Example flight code
    recipient_number="+233532419012"  # Example number with country code
)

# Get the notification result
message_content = result["messages"][-1].content if result and "messages" in result else "Notification sent successfully"
```

## Notification Types

The service sends different types of notifications based on flight status:

- Landing notifications (when status is "landed" or "arrived")
- Delay notifications (when flight is delayed)
- On-track notifications (for normal flight progress)

Each notification includes:

- Flight number
- Current status
- Arrival/departure times
- Terminal and gate information (when available)
- Delay information (if applicable)

## Security Notes

- Keep your `.env` file secure and never commit it
- All API keys should be properly secured
- Phone numbers should include country codes
- CORS is enabled for development purposes

## License

Private - All Rights Reserved

>>>>>>> d52938b50f589c3693f255c92f0825c91dce4cba
>>>>>>>
>>>>>>
>>>>>
>>>>
>>>
>>
