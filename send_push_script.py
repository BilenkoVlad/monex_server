import asyncio
from datetime import datetime

from google.api_core.exceptions import ResourceExhausted, RetryError

from push_notification.send_push import SendPush

try:
    start = datetime.now()
    asyncio.run(SendPush().main())
    finish = datetime.now()
    print(finish - start)
except (ResourceExhausted, RetryError) as re:
    print(f"Quota exceeded for today! Message: {re.message}.")