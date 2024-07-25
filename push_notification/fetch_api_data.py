import asyncio
from datetime import datetime

from push_notification.send_push import SendPush

start = datetime.now()
asyncio.run(SendPush().main())
finish = datetime.now()
print(finish - start)