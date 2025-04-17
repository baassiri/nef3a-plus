import subprocess

# Start the general bot
bot_process = subprocess.Popen(["python3", "nef3a_subscription/bot.py"])

# Start the subscription bot
sub_process = subprocess.Popen(["python3", "nef3a_subscription/bot_subscription.py"])

# Wait for both to finish
bot_process.wait()
sub_process.wait()
