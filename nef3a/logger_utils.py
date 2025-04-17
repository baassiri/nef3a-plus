import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=3)
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def log_user_info(update: Update, action: str, context) -> None:
    logger = setup_logger('user_activity', 'user_activity.log')
    user = update.message.from_user
    logger.info(f"User {user.username} - ID: {user.id} performed action: {action}")
    
if __name__ == "__main__":
    app_logger = setup_logger('app_logger', 'app.log')
    app_logger.info('Logger setup complete.')

    dummy_update = Update(update_id=1, message=None)
    dummy_context = None
    log_user_info(dummy_update, "started bot", dummy_context)
