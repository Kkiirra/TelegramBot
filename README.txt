Hello! This bot is designed to be able to find information about hotels
in any city thanks to a request to the Rapidapi website

The project is divided into 3 parts
1 Database queries
2 API requests and write hotels to database
3 main.py file that manages the whole project.

We have 4 commands.
Lowprice
Highprice
Bestdeal
History

Lowprice : For this command, you can display information about the cheapest hotels
Highprice: With this command, you can display information about the most expensive hotels
Bestdeal: With this command, you can display information about hotels according to user-specified parameters
History: With this command, you can display information about user requests

We have log file for understanding errors
database - Sqlite3
File database.py will help you got faster database requests


You must create .env file with
.env KEY=YOUR_BOT_KEY key from Telegram
.env RAPIDAPI_KEY=YOUR_RAPIDAPI_KEY key from rapidapi/hotels
