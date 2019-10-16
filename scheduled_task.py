"""
Runs everyday at 7:00 (UTC time zone)
Firstly, searches in the database for chats where there was a birthday yesterday. In such chats bot sets the chat photo
that was before the bot updated it with the photo of a birthday person. It is done ONLY if users haven't changed it.
Then this chat is deleted from the database.
Secondly, searches for the chats where there is a birthday today. The photo of a birthday person is taken and modified.
Then it is sent to the chat. After that bot sets this photo as the chat photo and sends his congratulation. Finally,
this chat is added to the database
"""
import datetime
import telebot
import os
import constants
import modify_photo
import random
from main import db, cursor, bot, get_username_or_first_name, awake_mysql_db


def create_markup_pin():
    markup_pin = telebot.types.InlineKeyboardMarkup()
    markup_pin.row(telebot.types.InlineKeyboardButton("Pin", callback_data="pin"),
                   telebot.types.InlineKeyboardButton("Dismiss", callback_data="dismiss"))
    return markup_pin


awake_mysql_db()

# Check if there was a birthday yesterday ------------------------------------------------------------------
cursor.execute("SELECT * FROM was_birthday")
was_birthdays = cursor.fetchall()

for past_birthday in was_birthdays:
    chat_id_of_past_birthday, new_photo_of_past_birthday_id, old_photo_of_past_birthday_id = past_birthday
    # If users blocked the bot, it won't be able to find the chat ------------------------------------------
    try:
        chat = bot.get_chat(chat_id_of_past_birthday)
    except telebot.apihelper.ApiException:
        chat = None
    if not chat:
        sql = "DELETE FROM birthdays WHERE Chat_Id = %s"
        val = (chat_id_of_past_birthday,)
        cursor.execute(sql, val)
        db.commit()
        continue
    # Set photo which was before person's birthday as a chat photo again -----------------------------------
    chat_photo_now = chat.photo
    if chat_photo_now:
        chat_photo_now_file_id = chat_photo_now.big_file_id
        if chat_photo_now_file_id == new_photo_of_past_birthday_id:  # User haven't changed it
            if old_photo_of_past_birthday_id == "None":
                try:
                    bot.delete_chat_photo(chat_id_of_past_birthday)
                except telebot.apihelper.ApiException:
                    bot.send_message(chat_id_of_past_birthday, "I can't set a chat photo :( "
                                                               "\nLooks like I don't have the appropriate admin rights")
            else:
                file_to_download = bot.get_file(old_photo_of_past_birthday_id)
                file_of_old_photo = bot.download_file(file_to_download.file_path)
                try:
                    bot.set_chat_photo(chat_id_of_past_birthday, file_of_old_photo)
                except telebot.apihelper.ApiException:
                    bot.send_message(chat_id_of_past_birthday,
                                     "I can't set a chat photo :( "
                                     "\nLooks like I don't have the appropriate admin rights")

    sql = "DELETE FROM was_birthday WHERE Chat_Id = %s AND New_Photo_Id = %s AND Old_photo_Id = %s"
    val = (chat_id_of_past_birthday, new_photo_of_past_birthday_id, old_photo_of_past_birthday_id)
    cursor.execute(sql, val)
    db.commit()

# ----------------------------------------------------------------------------------------------------------
# Check if someone has birthday today ----------------------------------------------------------------------
# Edit to fit MySQl DATE_FORMAT(Birthday, '%m.%d') ---------------------------------------------------------
month_now = str(datetime.date.today().month)
day_now = str(datetime.date.today().day)

if len(month_now) == 1:
    month_now = "0" + month_now

if len(day_now) == 1:
    day_now = "0" + day_now
# -----------------------------------------------------------------------------------------------------------

cursor.execute("SELECT User_Id, Chat_Id FROM birthdays WHERE DATE_FORMAT(Birthday, '%m.%d') = {}"
               .format(month_now + "." + day_now))

birthdays = cursor.fetchall()

for birthday in birthdays:
    script_directory = os.path.dirname(os.path.abspath(__file__))
    user_who_has_birthday_id, chat = birthday
    try:
        bot.send_chat_action(chat, 'typing')
    except telebot.apihelper.ApiException:
        sql = "DELETE FROM birthdays WHERE Chat_Id = %s"
        val = (chat,)
        cursor.execute(sql, val)
        db.commit()
        continue
    # Get user_who_has_birthday profile photo
    user_profile_photos = bot.get_user_profile_photos(user_who_has_birthday_id, limit=1).photos
    if not user_profile_photos:
        bot.send_message(chat, "Looks like somebody doesn't have the profile photo..."
                               "\nHow is it possible not to have the profile photo in twenty first century.."
                               "\nMaybe it's just a new user.. And it's probably hard to choose the nice one..."
                               "\nOh.. "
                               "\nYea, right! I can help to choose!! How about this one?!")
        user_profile_photos = bot.get_user_profile_photos(constants.bot_id, limit=1).photos
    user_photo_file_id = user_profile_photos[0][-1].file_id
    user_photo_file = bot.get_file(user_photo_file_id)
    modify_photo.modify_photo(user_photo_file, constants.modified_image_save_path)
    result_file = os.path.join(script_directory, constants.modified_image_save_path)
    with open(result_file, 'rb') as result_image:
        new_photo = bot.send_photo(chat, result_image)
    new_photo_id = new_photo.photo[-1].file_id
    # Get future previous chat photo
    chat_photos = bot.get_chat(chat).photo
    if not chat_photos:
        previous_chat_photo_id = "None"
    else:
        previous_chat_photo_id = chat_photos.big_file_id
    if previous_chat_photo_id != "None":
        previous_chat_photo_file = bot.get_file(previous_chat_photo_id)
        bot.download_file(previous_chat_photo_file.file_path)
    # Set new photo as chat photo
    new_photo_file = bot.get_file(new_photo_id)
    file = bot.download_file(new_photo_file.file_path)
    try:
        bot.set_chat_photo(chat, file)
    except telebot.apihelper.ApiException:
        bot.send_message(chat, "I can't set a chat photo :( \nLooks like I don't have the appropriate admin rights")
    # Insert data into MySQL table
    new_chat_photo_id = bot.get_chat(chat).photo.big_file_id
    sql = "SELECT * FROM was_birthday WHERE Chat_Id = %s"
    cursor.execute(sql, (chat,))
    already_in_database = cursor.fetchall()
    # If this chat is already present in the database, update new_photo_id
    if already_in_database:
        sql = "UPDATE was_birthday SET New_Photo_Id = %s WHERE Chat_Id = %s"
        val = (new_chat_photo_id, chat)
        cursor.execute(sql, val)
    else:
        sql = "INSERT INTO was_birthday (Chat_Id, New_Photo_Id, Old_Photo_Id) VALUES (%s, %s, %s)"
        val = (chat, new_chat_photo_id, previous_chat_photo_id)
        cursor.execute(sql, val)
    db.commit()
    # Send a message with congratulations
    name = get_username_or_first_name(chat, user_who_has_birthday_id)
    random_message = constants.messages_to_congratulate.get(random.randint(1, len(constants.messages_to_congratulate)))
    bot.send_message(chat, random_message.format(name), reply_markup=create_markup_pin())
    random_sticker = constants.stickers_to_congratulate.get(random.randint(1, len(constants.stickers_to_congratulate)))
    bot.send_sticker(chat, random_sticker)
