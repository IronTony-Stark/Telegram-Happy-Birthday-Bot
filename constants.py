import mysql.connector
import re

bot_token = "<bot_token>"
bot_id = -1


def initialize_mysql():
    return mysql.connector.connect(
        host="<host>",
        user="<user>",
        passwd="<password>",
        database="<database>"
    )


date_of_birth_pattern = re.compile("[0-9][0-9][.-][0-9][0-9][.-][0-9][0-9][0-9][0-9]")
user_id_pattern = re.compile("\d+")

modified_image_save_path = "<modified_image_path>"

months = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
          9: "September", 10: "October", 11: "November", 12: "December"}

stickers_to_congratulate = {1: "CAADAgADYgADVSx4C-wfF-VhdzeCAg", 2: "CAADAgADSgADVSx4C_alFsjOJxXLAg",
                            3: "CAADAgADZAADVSx4C8jFprgXX7rTAg", 4: "CAADAgADPAADVSx4C-XzQNWkpQG2Ag"}

messages_to_congratulate = {1: "Happy birthday, {}! May your Facebook, Instagram and Twitter walls be filled with "
                               "messages from people you never talk to!",
                            2: "Forget about the past, you can’t change it. Forget about the future, you can’t "
                               "predict it. Forget about the present, I didn't get you one. Happy birthday, {}!",
                            3: "On your birthday, I thought of giving you the cutest gift in the world. But then I "
                               "realized that is not possible, because you yourself are the cutest gift in the world. "
                               "Anyway, happy birthday, {}!",
                            4: "Happy birthday, {}! The emergency department is on speed dial just in case you have "
                               "an unexpected asthma attack blowing the candles. Just saying... I mean just kidding",
                            5: "Happy birthday, {}! I made a list about the words of wisdom I wanted to give you "
                               "for your birthday. It’s still blank. Maybe next year",
                            6: "Oh yeah! You’re getting closer to the age when the government sends you money "
                               "every month. Happy Birthday, {}!",
                            7: "Congratulations, {}! You only look one year older than you did on your last birthday.",
                            8: "Brace yourself, {}! An explosion of Facebook, Twitter and Instagram notifications "
                               "is coming. Happy Birthday!",
                            9: '"We got no food! We got no jobs! Our pets heads are falling off!!" '
                               'I hope you are having a better day than Harry & Lloyd. Happy Birthday, {}!',
                            10: "Happy Birthday, {}! May your day be full of happiness, laughter, love, and of "
                                "course the most important thing—wine!!"}
