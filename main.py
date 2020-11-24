"""
Important information
I use pythonanywhere as the server. It offers so called "scheduled tasks". Basically that's the script that is executed
everyday at a specific time. I have a file called scheduled_task.py which is executed everyday at 7:00 (UTC time zone).
However it is also possible to achieve the same result using threading. At the end of this file there is a commented
block of code. It uses threading to do the job. So if you don't have the opportunity to execute the scheduled_task.py
script you can use this code.
"""
import constants
import datetime
import telebot
import flask
from flask import Flask
from flask_sslify import SSLify

# Initialization
app = Flask(__name__)
sslify = SSLify(app)
bot = telebot.TeleBot(constants.bot_token, threaded=False)

db = constants.initialize_mysql()
cursor = db.cursor()


def awake_mysql_db():
    """"
    If there's no connection, creates one, else pings to wake up the connection
    """
    global db
    if db is None:
        db = constants.initialize_mysql()
    else:
        db.ping(True)


# -----------------------------------------
# Bot methods


def get_username_or_first_name(chat_id, user_id):
    """"
    Returns username if exists. Else, returns first_name
    """
    chat_member_who_has_birthday = bot.get_chat_member(chat_id, user_id)
    if chat_member_who_has_birthday.user.username is None:
        name = chat_member_who_has_birthday.user.first_name
    else:
        name = "@" + chat_member_who_has_birthday.user.username
    return name


@app.route('/', methods=['GET', 'HEAD'])
def index():
    return '<h1>Happy Birthday Telegram Bot by Iron Tony</h1>'


@app.route('/', methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


@bot.message_handler(commands=['mybirthday'])
def handle_text(message):
    """
    Insert user id, his birth date and chat id into the database. If such user already exists in the database
    updates his birth date. Private chats not allowed
    """
    chat = bot.get_chat(message.chat.id)

    # Private chats are not allowed
    if chat.type == "private":
        bot.send_message(message.chat.id, "Sorry, I don't work in private chats")
        return

    # Channels are not allowed
    if chat.type == "channel":
        bot.send_message(message.chat.id, "Sorry, I don't work in channels")
        return

    words_in_message = message.text.split()

    if len(words_in_message) != 2:
        bot.reply_to(message, 'Wrong format. '
                              '\nPlease type "/mybirthday dd.mm.yyyy"'
                              '\n dd, mm, yyyy - the day, month and year when you were born')
        return

    birthday_date = words_in_message[1]

    if not constants.date_of_birth_pattern.match(birthday_date):
        bot.reply_to(message, 'Wrong format. '
                              '\nPlease type "/mybirthday dd.mm.yyyy"'
                              '\ndd, mm, yyyy - the day, month and year when you were born')
        return

    # Check user input for the correct values -----------------------------------------------------------
    day = birthday_date[:2]
    month = birthday_date[3:5]
    year = birthday_date[6:]

    if int(day) > 31 or int(day) < 1:
        bot.reply_to(message, "Looks like something is wrong with the day")
        return

    if month in ["04", "06", "09", "11"] and int(day) == 31:
        bot.reply_to(message, "{} has only 30 days :)".format(constants.months.get(int(month))))
        return

    if month == "02" and int(day) > 29:
        bot.reply_to(message, "February has only 28 days :)")
        return

    if int(month) > 12 or int(month) < 1:
        bot.reply_to(message, "Looks like something is wrong with the month")
        return

    if int(year) > 2016 or int(year) < 1900:
        bot.reply_to(message,
                     "Hey, I don't believe you! You can't be born in {}!"
                     "\nIf you are woman or (and) you are "
                     "afraid somebody will find out your age, don't worry, I'll keep it in secret :)"
                     .format(year))
        bot.send_sticker(message.chat.id, "CAADAgADMgADVSx4C49XV6fn89_VAg")
        return 
    # -------------------------------------------------------------------------------------------------

    user_id = message.from_user.id
    # Modifying birthday_date to fit MySQL date format
    birthday_date = birthday_date[6:] + birthday_date[2:6] + birthday_date[:2]

    awake_mysql_db()

    name = get_username_or_first_name(message.chat.id, user_id)

    sql = "SELECT DATE_FORMAT(Birthday, '%Y.%m.%d') FROM birthdays WHERE User_Id = %s AND Chat_Id = %s"
    val = (user_id, message.chat.id)
    cursor.execute(sql, val)
    is_registered_in_chat = cursor.fetchall()

    # Check if the user's birthday is already registered in this chat
    if is_registered_in_chat:
        birthday_date_in_the_database = is_registered_in_chat[0][0]
        if birthday_date_in_the_database == birthday_date:
            answer = "Don't worry, {}! I remember you were born on {} {}" \
                .format(name, birthday_date[8:], constants.months.get(int(birthday_date[5:7])))
        else:
            sql = "UPDATE birthdays SET Birthday = %s WHERE User_Id = %s"
            val = (birthday_date, user_id)
            cursor.execute(sql, val)
            db.commit()
            answer = "Update! \nLooks like {0} went back to past and changed his (her) birth date (somehow)" \
                     "\nSo {0} was born on {1} {2} now! \nI wonder if his (her) age has changed..." \
                .format(name, birthday_date[8:], constants.months.get(int(birthday_date[5:7])))
    else:
        sql = "SELECT DATE_FORMAT(Birthday, '%Y.%m.%d') FROM birthdays WHERE User_Id = %s"
        val = (user_id,)
        cursor.execute(sql, val)
        is_registered_in_the_database = cursor.fetchall()

        # Check if the user's birthday have been registered in the database before
        if is_registered_in_the_database:
            birthday_date_in_the_database = is_registered_in_the_database[0][0]
            if birthday_date_in_the_database == birthday_date:
                answer = "Happy to see you again, {}! How are things going?" \
                    .format(name)
            else:
                answer = "Hey, {}! That's quite suspicious... \nIn another chat you said you were born on {} {} {} " \
                         "\nAnyway, I have updated my database. So now your birthday is {} {} {}.. In every chat :)" \
                    .format(name,
                            birthday_date_in_the_database[8:],
                            constants.months.get(int(birthday_date_in_the_database[5:7])),
                            birthday_date_in_the_database[:4],
                            birthday_date[8:],
                            constants.months.get(int(birthday_date[5:7])),
                            birthday_date[:4])
                sql = "UPDATE birthdays SET Birthday = %s WHERE User_Id = %s"
                val = (birthday_date, user_id)
                cursor.execute(sql, val)
                db.commit()
        else:
            answer = "Hi, {}! \nI'm so glad to meet you! \nI will remember you were born on {} {}" \
                .format(name, birthday_date[8:], constants.months.get(int(birthday_date[5:7])))

        sql = "INSERT INTO birthdays (User_Id, Birthday, Chat_Id) VALUES (%s, %s, %s)"
        val = (user_id, birthday_date, message.chat.id)
        cursor.execute(sql, val)
        db.commit()

    bot.send_message(message.chat.id, answer)
    bot.send_sticker(message.chat.id, "CAADAgADGAEAArnzlwtw2f1OYY8VcwI")


@bot.message_handler(commands=['help'])
def handle_text(message):
    bot.send_message(message.chat.id,
                     "mybirthday - /mybirthday [dd.mm.yyyy] The day, month and year when you were born"
                     "\nnextbirthday - Shows whose birthday is next"
                     "\naboutme - Shows description")


@bot.message_handler(commands=['aboutme'])
def handle_text(message):
    bot.send_sticker(message.chat.id, "CAADAgADZgADVSx4C4I00LsibnWGAg")
    bot.send_message(message.chat.id,
                     "Often forgetting when the birthday of your friend is? This won’t happen again! "
                     "\nI am HappyBirthdayBot and I’ll make sure your friends are happy when their birthdays come! "
                     "\n\nAll you need to do is to add me to your chat group and ask your friends to type the command "
                     "/mybirthday [date of your friend's birthday in format dd.mm.yyyy]. Don’t forget to do the same "
                     "and you are all done! When the day comes I’ll send my congratulation to this chat group. Also, "
                     "I’ll take the birthday person's profile photo, modify it adding some cool things and send "
                     "it too. Finally, I’ll set this new photo as the chat profile photo! Next day I will reset the "
                     "chat profile photo with the one that was before."
                     "\n\nWith me it’s impossible to forget about birthdays of your friends! "
                     "\n\nMy creator (@IronTony_Stark github.com/IronTony-Stark/Telegram-Happy-Birthday-Bot) said that "
                     "he will be very thankful for your feedback, any suggestions are welcomed and bug reports are "
                     "priceless! Well, personally I am not sure about the last, but my creator knows best", True)


@bot.message_handler(commands=['nextbirthday'])
def handle_text(message):
    """
    Searches whose birthday is next in this chat
    """
    if message.chat.id == message.from_user.id:
        bot.send_message(message.chat.id, "Well, it's quite obvious whose birthday is next in private chat :D")
        bot.send_sticker(message.chat.id, "CAADAgADMgADVSx4C49XV6fn89_VAg")
        return

    awake_mysql_db()

    month_now = datetime.date.today().month
    day_now = datetime.date.today().day

    def answer(query_result):
        """"
        Sends message to the chat telling whose birthday is next
        """
        username_or_first_name = get_username_or_first_name(message.chat.id, query_result[0][0])
        bot.reply_to(message, "Get ready, {}! You're next! On {} {} we'll tear you apart... "
                              "With our congratulations! :)"
                     .format(username_or_first_name, query_result[0][1][3:],
                             constants.months.get(int(query_result[0][1][:2]))))
        bot.send_sticker(message.chat.id, "CAADAgADOgADVSx4C7RBZBTJ4211Ag")

    sql_queries = [
        # Later this month
        "SELECT User_Id, DATE_FORMAT(Birthday, '%m.%d') "
        "FROM birthdays WHERE MONTH(Birthday) = %s AND Day(Birthday) > %s AND Chat_Id = %s "
        "ORDER BY Day(Birthday)",
        # After this month
        "SELECT User_Id, DATE_FORMAT(Birthday, '%m.%d') "
        "FROM birthdays WHERE MONTH(Birthday) > %s AND Chat_Id = %s "
        "ORDER BY MONTH(Birthday), Day(Birthday)",
        # Before this month
        "SELECT User_Id, DATE_FORMAT(Birthday, '%m.%d') "
        "FROM birthdays WHERE MONTH(Birthday) < %s AND Chat_Id = %s "
        "ORDER BY MONTH(Birthday), Day(Birthday)",
        # Earlier this month
        "SELECT User_Id, DATE_FORMAT(Birthday, '%m.%d') "
        "FROM birthdays WHERE MONTH(Birthday) = %s AND Day(Birthday) <= %s AND Chat_Id = %s "
        "ORDER BY Day(Birthday)"
    ]

    for i in range(4):
        if i == 0 or i == 3:
            val = (month_now, day_now, message.chat.id)
        else:
            val = (month_now, message.chat.id)

        cursor.execute(sql_queries[i], val)
        result = cursor.fetchall()

        if result:
            answer(result)
            return

    bot.reply_to(message, "Looks like there are no birthdays registered in this chat")
    bot.send_sticker(message.chat.id, "CAADAgADQAADVSx4CwnTmrLuK3GoAg") 


@bot.message_handler(commands=['listbirthdays'])
def handle_text(message):
    """
    Lists all birthdays in this manner:
    ```
    January:
    1 - username_or_first_name[, second_person [...]]

    February:
    1 - username_or_first_name[, second_person [...]]
    ```

    If no birthdays are found, it says "Looks like there are no birthdays registered in this chat" and sends a sticker
    """
    if message.chat.id == message.from_user.id:
        bot.send_message(message.chat.id, "There's only one birthday coming up here... And I bet you can guess whose it is XD")
        return

    awake_mysql_db()

    sql_query = "SELECT User_Id, DATE_FORMAT(Birthday, '%m.%d') FROM birthdays WHERE MONTH(Birthday) > -1 AND Chat_Id = %s ORDER BY MONTH(Birthday), Day(Birthday)"

    list_of_birthdays = ""
    current_month = -1
    current_day = -1
    cursor.execute(sql_query, message.chat.id)
    results = cursor.fetchall()

    for row in results:
        username = row[0]
        month, day = row[1][:2], row[1][3:]
        if month != current_month:
            if current_month != -1:
                list_of_birthdays += "\n\n"
            month = current_month
            list_of_birthdays += constants.months.get(int(month))+":"
            current_day = -1
        
        if current_day == day:
            list_of_birthdays += ", "+username
        else:
            list_of_birthdays += "\n"+str(day)+" - "+username
            current_day = day

    if list_of_birthdays == "":
        bot.reply_to(message, "Looks like there are no birthdays registered in this chat")
        bot.send_sticker(message.chat.id, "CAADAgADQAADVSx4CwnTmrLuK3GoAg")
    else:
        bot.send_message(message.chat.id, list_of_birthdays)


@bot.message_handler(commands=['start'])
def handle_text(message):
    bot.send_sticker(message.chat.id, "CAADAgADZgADVSx4C4I00LsibnWGAg")
    bot.send_message(message.chat.id,
                     "Hi! I'm so happy to meet you!!"
                     "\nNow add me to some chat group and type /mybirthday [your birth date in format dd.mm.yyyy]"
                     "\nType /aboutme if you want to get more info"
                     "\nHope you enjoy! :)")


@bot.callback_query_handler(lambda query: query.data == "pin")
def pin_message(query):
    query_chat_id = query.message.chat.id
    query_chat_admins = bot.get_chat_administrators(query_chat_id)
    query_chat_admins_id = [admin.user.id for admin in query_chat_admins]
    if query.from_user.id in query_chat_admins_id:
        try:
            bot.pin_chat_message(query_chat_id, query.message.message_id)
            bot.edit_message_reply_markup(query_chat_id, query.message.message_id)
            bot.answer_callback_query(query.id)
        except telebot.apihelper.ApiException:
            bot.send_message(query.message.chat.id, "I can't pin a message(( \nThat's a pity! "
                                                    "\nLooks like I don't have the appropriate admin rights")
    else:
        bot.answer_callback_query(query.id, "You don't have permission to pin messages")


@bot.callback_query_handler(lambda query: query.data == "dismiss")
def remove_markup(query):
    bot.edit_message_reply_markup(query.message.chat.id, query.message.message_id)
    bot.answer_callback_query(query.id)


# Threading ----------------------------------------------------------------------
# By the way I haven't checked if it works.. But I suppose it does :)

# import modify_photo
# import random
# import time
# import threading
# import os
#
#
# def count_time_to_sleep(wake_up_hour: "int") -> "int":
#     """
#     Counts how many minutes is needed for thread to sleep, so the wake up time will be :param wake_up_hour
#     """
#     if wake_up_hour < 0 or wake_up_hour > 24:
#         raise ValueError("Invalid wake_up_hour. Value from 0 to 24 is expected")
#     local_time = time.strftime("%H:%M", time.localtime())
#     local_hour, local_min = local_time.split(":")
#     hour_difference = wake_up_hour - int(local_hour)
#     minute_difference = 0 - int(local_min)
#     minutes_to_12 = hour_difference * 60 + minute_difference
#     if minutes_to_12 < 0:
#         minutes_to_12 = 24 * 60 - (-minutes_to_12)
#     return minutes_to_12
#
#
# # # Execute every day at 12:00 (hour difference in count_time_to_sleep function)
# def check_birthday():
#     """"
#     Firstly, searches in the database (was_birthday) for chats where there was a birthday yesterday. In such chats
#     bot sets the chat photo that was before the bot updated it with the photo of a birthday person. It is done
#     ONLY IF users haven't changed it. Then this chat is deleted from the database.
#     Secondly, searches in the database (birthdays) for the chats where there is a birthday today. The photo of a
#     birthday person
#     is taken and modified. Then it is sent to the chat. After that bot sets this photo as the chat photo and sends his
#     congratulation. After that this chat is added to the database
#     Finally, calls count_time_to_sleep function and sleeps
#     """
#     while True:
#         awake_mysql_db()
#
#         # Check if there was a birthday yesterday ------------------------------------------------------------------
#         cursor.execute("SELECT * FROM was_birthday")
#         was_birthdays = cursor.fetchall()
#
#         # Set photo which was before person's birthday as a chat photo again
#         for past_birthday in was_birthdays:
#             chat_id_of_past_birthday, new_photo_of_past_birthday_id, old_photo_of_past_birthday_id = past_birthday
#             if old_photo_of_past_birthday_id == "None":
#                 try:
#                     bot.delete_chat_photo(chat_id_of_past_birthday)
#                 except telebot.apihelper.ApiException:
#                     bot.send_message(chat_id_of_past_birthday, "I can't set a chat photo :( "
#                                                                "\nLooks like I don't have the appropriate admin
#                                                                rights")
#         else:
#             chat_photo_now_file_id = bot.get_chat(chat_id_of_past_birthday).photo.big_file_id
#             if chat_photo_now_file_id == new_photo_of_past_birthday_id:  # User haven't changed it
#                 file_of_old_photo = bot.download_file(bot.get_file(old_photo_of_past_birthday_id).file_path)
#                 try:
#                     bot.set_chat_photo(chat_id_of_past_birthday, file_of_old_photo)
#                 except telebot.apihelper.ApiException:
#                     bot.send_message(chat_id_of_past_birthday,
#                                      "I can't set a chat photo :( "
#                                      "\nLooks like I don't have the appropriate admin rights")
#
#         sql = "DELETE FROM was_birthday WHERE Chat_Id = %s AND New_Photo_Id = %s AND Old_photo_Id = %s"
#         val = (chat_id_of_past_birthday, new_photo_of_past_birthday_id, old_photo_of_past_birthday_id)
#         cursor.execute(sql, val)
#         db.commit()
#
#     # ----------------------------------------------------------------------------------------------------------
#     # Check if someone has birthday today ----------------------------------------------------------------------
#     # Edit to fit MySQl DATE_FORMAT(Birthday, '%m.%d') ---------------------------------------------------------
#     month_now = str(datetime.date.today().month)
#     day_now = str(datetime.date.today().day)
#
#     if len(month_now) == 1:
#         month_now = "0" + month_now
#
#     if len(day_now) == 1:
#         day_now = "0" + day_now
#     # -----------------------------------------------------------------------------------------------------------
#
#     cursor.execute("SELECT User_Id, Chat_Id FROM birthdays WHERE DATE_FORMAT(Birthday, '%m.%d') = {}"
#                    .format(month_now + "." + day_now))
#
#     birthdays = cursor.fetchall()
#
#     for birthday in birthdays:
#         script_directory = os.path.dirname(os.path.abspath(__file__))
#         user_who_has_birthday_id, chat = birthday
#         try:
#             bot.send_chat_action(chat, 'typing')
#         except telebot.apihelper.ApiException:
#             sql = "DELETE FROM birthdays WHERE Chat_Id = %s"
#             val = (chat,)
#             cursor.execute(sql, val)
#             db.commit()
#             continue
#         # Get user_who_has_birthday profile photo
#         user_profile_photos = bot.get_user_profile_photos(user_who_has_birthday_id, limit=1).photos
#         if not user_profile_photos:
#             bot.send_message(chat, "Looks like somebody doesn't have the profile photo. ")
#             user_profile_photos = bot.get_user_profile_photos(constants.bot_id, limit=1).photos
#         user_photo_file_id = user_profile_photos[0][2].file_id
#         user_photo_file = bot.get_file(user_photo_file_id)
#         modify_photo.modify_photo(user_photo_file, constants.modified_image_save_path)
#         result_file = os.path.join(script_directory, constants.modified_image_save_path)
#         with open(result_file, 'rb') as result_image:
#             new_photo = bot.send_photo(chat, result_image)
#         new_photo_id = new_photo.photo[2].file_id
#         # Get future previous chat photo
#         chat_photos = bot.get_chat(chat).photo
#         if not chat_photos:
#             previous_chat_photo_id = "None"
#         else:
#             previous_chat_photo_id = chat_photos.big_file_id
#         # Set new photo as chat photo
#         new_photo_file = bot.get_file(new_photo_id)
#         file = bot.download_file(new_photo_file.file_path)
#         try:
#             bot.set_chat_photo(chat, file)
#         except telebot.apihelper.ApiException:
#             bot.send_message(chat,
#                              "I can't set a chat photo :( \nLooks like I don't have the appropriate admin rights")
#         # Insert data into MySQL table
#         new_chat_photo_id = bot.get_chat(chat).photo.big_file_id
#         sql = "SELECT * FROM was_birthday WHERE Chat_Id = %s"
#         cursor.execute(sql, (chat,))
#         already_in_database = cursor.fetchall()
#         # If this chat is already present in the database, update new_photo_id
#         if already_in_database:
#             sql = "UPDATE was_birthday SET New_Photo_Id = %s WHERE Chat_Id = %s"
#             val = (new_chat_photo_id, chat)
#             cursor.execute(sql, val)
#         else:
#             sql = "INSERT INTO was_birthday (Chat_Id, New_Photo_Id, Old_photo_Id) VALUES (%s, %s, %s)"
#             val = (chat, new_chat_photo_id, previous_chat_photo_id)
#             cursor.execute(sql, val)
#         db.commit()
#         # Send a message with congratulations
#         name = get_username_or_first_name(chat, user_who_has_birthday_id)
#         random_message = constants.messages_to_congratulate.get(
#             random.randint(1, len(constants.messages_to_congratulate)))
#         message_to_pin = bot.send_message(chat, random_message.format(name))
#         random_sticker = constants.stickers_to_congratulate.get(
#             random.randint(1, len(constants.stickers_to_congratulate)))
#         bot.send_sticker(chat, random_sticker)
#         # Pin the message with congratulations
#         try:
#             bot.pin_chat_message(chat, message_to_pin.message_id)
#         except telebot.apihelper.ApiException:
#             bot.send_message(chat, "I can't pin a message(( \nThat's a pity! "
#                                    "\nLooks like I don't have the appropriate admin rights")
#
#         minutes_to_sleep = count_time_to_sleep(12)
#         time.sleep(minutes_to_sleep)
#
#
# check_birthday_thread = threading.Thread(target=check_birthday)
# check_birthday_thread.start()
# --------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run()
