import asyncio
from datetime import datetime

from push_notification.update_currency import UpdateCurrency

start = datetime.now()
asyncio.run(UpdateCurrency().main())
finish = datetime.now()
print(finish - start)
