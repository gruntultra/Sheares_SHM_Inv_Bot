import schedule
import time
import dbworker

def job():
    dbworker.get_expiry_loans()

# schedule.every().day.at("00:00").do(job)

# while True:
#     schedule.run_pending()
job()